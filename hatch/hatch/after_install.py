import frappe


def after_install():
    create_default_resources()
    create_default_hatch_settings()
    frappe.msgprint("Hatch installed successfully with default data.")


def create_default_resources():
    resources = [
        "Meeting Room",
        "Projector",
        "Laptop",
    ]

    for resource in resources:
        if not frappe.db.exists("Resource", {"resource_name": resource}):
            doc = frappe.get_doc({
                "doctype": "Resource",
                "resource_name": resource
            })
            doc.insert(ignore_permissions=True)


def create_default_hatch_settings():
    if not frappe.db.exists("Hatch Settings"):
        doc = frappe.get_doc({
            "doctype": "Hatch Settings"
        })
        doc.insert(ignore_permissions=True)
