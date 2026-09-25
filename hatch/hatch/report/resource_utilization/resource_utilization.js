frappe.query_reports["Resource Utilization"] = {

    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "resource",
            label: "Resource",
            fieldtype: "Link",
            options: "Resource"
        }
    ],

    formatter: function(value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (column.fieldname === "utilization") {

            let percentage = parseFloat(data.utilization) * 100;

            if (percentage > 95) {
                return `<span style="color:red;font-weight:bold">
                    ${percentage.toFixed(2)}%
                </span>`;
            }

            if (percentage >= 40 && percentage <= 85) {
                return `<span style="color:green;font-weight:bold">
                    ${percentage.toFixed(2)}%
                </span>`;
            }

            return `${percentage.toFixed(2)}%`;
        }

        return value;
    }
};