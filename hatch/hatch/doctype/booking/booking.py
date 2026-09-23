import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class Booking(Document):

    def validate(self):
        if self.end_time <= self.start_time:
            frappe.throw("End time must be greater than start time")

        resource = frappe.get_doc("Resource", self.resource)

        duration = time_diff_in_hours(
            self.end_time,
            self.start_time
        )

        self.base_amount = resource.hourly_rate * duration

        addons_total = 0

        for row in self.addons:
            row.amount = row.rate * row.quantity
            addons_total += row.amount

        self.addons_total = addons_total
        self.total_amount = self.base_amount + self.addons_total

        existing = frappe.db.sql(
            """
            SELECT COALESCE(SUM(headcount), 0) AS booked_headcount
            FROM `tabBooking`
            WHERE resource = %s
              AND booking_date = %s
              AND name != %s
              AND start_time < %s
              AND end_time > %s
              AND status IN (
                  'Pending Confirmation',
                  'Confirmed',
                  'Checked-In'
              )
            """,
            (
                self.resource,
                self.booking_date,
                self.name,
                self.end_time,
                self.start_time
            ),
            as_dict=True
        )

        booked_headcount = existing[0].booked_headcount or 0
        total_headcount = booked_headcount + self.headcount
        free_seats = resource.capacity - booked_headcount

        if total_headcount > resource.capacity:
            frappe.throw(
                f"Booking exceeds resource capacity. "
                f"Only {free_seats} seats are actually free."
            )

    def before_submit(self):
        if self.status != "Pending Confirmation":
            frappe.throw(
                "Only bookings with status 'Pending Confirmation' "
                "can be submitted."
            )

    def on_submit(self):
        self.status = "Confirmed"

        frappe.enqueue(
            "hatch.hatch.doctype.booking.booking.send_confirmation_email",
            booking_name=self.name
        )

    def on_cancel(self):
        self.status = "Cancelled"

    def on_trash(self):
        if self.status not in ("Cancelled", "Draft"):
            frappe.throw(
                "Only Cancelled or Draft bookings can be deleted."
            )  

def send_confirmation_email(booking_name):
    booking = frappe.get_doc("Booking", booking_name)

    frappe.sendmail(
        recipients=[booking.member],
        subject=f"Booking {booking.name} Confirmed",
        message=f"Your booking {booking.name} has been confirmed."
    )
