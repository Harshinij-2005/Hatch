import frappe


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if "Hatch Member" in frappe.get_roles(user):
        return """`tabBooking`.`member` IN (
            SELECT `name`
            FROM `tabMember`
            WHERE `user` = {user}
        )""".format(user=frappe.db.escape(user))

    return ""
