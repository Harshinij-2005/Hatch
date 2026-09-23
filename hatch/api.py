import frappe


@frappe.whitelist()
def share_booking(booking_name, user_email):
    frappe.share.add(
        "Booking",
        booking_name,
        user_email,
        read=1
    )

    return {
        "success": True,
        "message": f"Booking {booking_name} shared with {user_email}"
    }

import frappe
from frappe.query_builder import DocType


@frappe.whitelist()
def get_upcoming_bookings():
    BK = DocType("Booking")

    result = (
        frappe.qb.from_(BK)
        .select(
            BK.name,
            BK.member,
            BK.resource,
            BK.booking_date,
            BK.start_time
        )
        .where(
            (BK.booking_date >= frappe.utils.today())
            & (BK.status.isin(["Pending Confirmation", "Confirmed"]))
        )
        .orderby(BK.booking_date)
        .run(as_dict=True)
    )

    return result

@frappe.whitelist()
def reassign_bookings(from_member, to_member):
    try:
        frappe.db.sql(
            """
            UPDATE `tabBooking`
            SET member = %s
            WHERE member = %s
            AND booking_date >= %s
            AND status != %s
            """,
            (to_member, from_member, frappe.utils.today(), "Cancelled")
        )

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Booking Reassignment Failed"
        )
        raise

@frappe.whitelist()
def rename_member(old_name, new_name):
    frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )

    return {
        "success": True,
        "old_name": old_name,
        "new_name": new_name
    }