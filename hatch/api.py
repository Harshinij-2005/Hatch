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


@frappe.whitelist()
def get_upcoming_bookings(resource=None):
    query = """
        SELECT
            name,
            member,
            resource,
            booking_date,
            start_time,
            end_time,
            headcount,
            status
        FROM `tabBooking`
        WHERE booking_date >= %(today)s
    """

    params = {
        "today": frappe.utils.today(),
        "resource": resource,
    }

    if resource:
        query += " AND resource = %(resource)s"

    query += " ORDER BY booking_date"

    return frappe.db.sql(
        query,
        params,
        as_dict=True
    )


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


