import frappe
from frappe.utils import get_datetime


def execute(filters=None):
    filters = filters or {}

    columns = [
        {
            "label": "Resource",
            "fieldname": "resource",
            "fieldtype": "Link",
            "options": "Resource",
            "width": 150
        },
        {
            "label": "Total Bookings",
            "fieldname": "total_bookings",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Total Hours Booked",
            "fieldname": "total_hours",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": "Utilization %",
            "fieldname": "utilization",
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "label": "Revenue",
            "fieldname": "revenue",
            "fieldtype": "Currency",
            "width": 120
        }
    ]

    conditions = {
        "booking_date": [
            "between",
            [filters.get("from_date"), filters.get("to_date")]
        ]
    }

    if filters.get("resource"):
        conditions["resource"] = filters["resource"]

    bookings = frappe.get_list(
        "Booking",
        filters=conditions,
        fields=[
            "resource",
            "booking_date",
            "start_time",
            "end_time",
            "total_amount"
        ]
    )

    data = {}

    for booking in bookings:
        resource = booking.resource

        if resource not in data:
            data[resource] = {
                "total_bookings": 0,
                "total_hours": 0,
                "revenue": 0
            }

        data[resource]["total_bookings"] += 1

        start = get_datetime(booking.start_time)
        end = get_datetime(booking.end_time)

        hours = (end - start).total_seconds() / 3600

        data[resource]["total_hours"] += hours
        data[resource]["revenue"] += booking.total_amount or 0

    rows = []

    period_hours = (
        get_datetime(filters["to_date"])
        - get_datetime(filters["from_date"])
    ).days + 1

    period_hours *= 24

    for resource, values in data.items():

        utilization = (
            values["total_hours"] / period_hours
            if period_hours
            else 0
        )

        rows.append({
            "resource": resource,
            "total_bookings": values["total_bookings"],
            "total_hours": values["total_hours"],
            "utilization": utilization,
            "revenue": values["revenue"]
        })

    total_bookings = sum(
        row["total_bookings"] for row in rows
    )

    total_revenue = sum(
        row["revenue"] for row in rows
    )

    busiest_resource = (
        max(
            rows,
            key=lambda row: row["total_bookings"]
        )["resource"]
        if rows
        else "-"
    )

    report_summary = [
        {
            "label": "Total Bookings",
            "value": total_bookings,
            "datatype": "Int"
        },
        {
            "label": "Total Revenue",
            "value": total_revenue,
            "datatype": "Currency"
        },
        {
            "label": "Busiest Resource",
            "value": busiest_resource,
            "datatype": "Data"
        }
    ]

    return columns, rows, None, report_summary