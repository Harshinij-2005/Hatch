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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_resources(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)

    member = filters.get("member")

    if not member:
        return []

    membership_plan = frappe.db.get_value(
        "Member",
        member,
        "membership_plan"
    )

    if not membership_plan:
        return []

    allowed_resources = frappe.get_all(
        "Membership Plan Resource Type",
        filters={"parent": membership_plan},
        pluck="resource_type"
    )

    if not allowed_resources:
        return []

    resources = frappe.get_all(
        "Resource",
        filters={
            "name": ["in", allowed_resources]
        },
        fields=["name", "resource_type"],
        limit_start=start,
        limit_page_length=page_len
    )
    return [(r.name, r.resource_type) for r in resources]

@frappe.whitelist()
def get_live_availability(
    resource,
    booking_date,
    start_time,
    end_time,
    booking=None
):
    capacity = frappe.db.get_value(
        "Resource",
        resource,
        "capacity"
    ) or 0

    filters = {
        "resource": resource,
        "booking_date": booking_date,
        "docstatus": ["!=", 2],
        "status": ["in", ["Pending", "Confirmed"]]
    }

    if booking:
        filters["name"] = ["!=", booking]

    bookings = frappe.get_all(
        "Booking",
        filters=filters,
        fields=["start_time", "end_time"]
    )

    overlapping = 0

    for existing in bookings:
        if (
            existing.start_time < end_time
            and existing.end_time > start_time
        ):
            overlapping += 1

    free = max(capacity - overlapping, 0)

    return {
        "available": free > 0,
        "free": free,
        "total": capacity,
        "message": f"{free} of {capacity} seats free in this slot"
    }
@frappe.whitelist()
def check_in(booking):
    doc = frappe.get_doc("Booking", booking)

    if doc.status != "Confirmed":
        frappe.throw("Only confirmed bookings can be checked in.")

    if doc.docstatus != 1:
        frappe.throw("Booking must be submitted.")

    if str(doc.booking_date) != frappe.utils.today():
        frappe.throw("Check In is available only on the booking date.")

    doc.status = "Checked In"
    doc.save()

    return True

@frappe.whitelist()
def cancel_booking(booking, cancellation_reason):
    doc = frappe.get_doc("Booking", booking)

    if not cancellation_reason:
        frappe.throw("Cancellation Reason is required.")

    if doc.docstatus != 1:
        frappe.throw("Only submitted bookings can be cancelled.")

    doc.status = "Cancelled"
    doc.add_comment(
        "Comment",
        f"Cancellation Reason: {cancellation_reason}"
    )
    doc.save(ignore_permissions=True)

    return True


@frappe.whitelist()
def reassign_booking(booking, new_member):
    doc = frappe.get_doc("Booking", booking)

    if not new_member:
        frappe.throw("New Member is required.")

    if doc.docstatus != 1:
        frappe.throw("Only submitted bookings can be reassigned.")

    if not frappe.db.exists("Member", new_member):
        frappe.throw("Member does not exist.")

    doc.member = new_member
    doc.save(ignore_permissions=True)
    frappe.db.set_value(
        "Booking",
        booking,
        "member",
        new_member
    )

    return True
