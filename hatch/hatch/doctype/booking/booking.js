frappe.ui.form.on("Booking", {

    validate: function(frm) {

        // 1. Check time
        if (frm.doc.end_time <= frm.doc.start_time) {
            frappe.throw("End Time must be greater than Start Time");
        }

        // 2. Calculate duration
        let start = moment(frm.doc.start_time, "HH:mm:ss");
        let end = moment(frm.doc.end_time, "HH:mm:ss");

        let duration_in_hours = moment
            .duration(end.diff(start))
            .asHours();

        // 3. Get hourly rate from Resource
        frappe.db.get_value(
            "Resource",
            frm.doc.resource,
            "hourly_rate"
        ).then(r => {

            let hourly_rate = r.message.hourly_rate || 0;

            // 4. Calculate base amount
            let base_amount = hourly_rate * duration_in_hours;

            frm.set_value("base_amount", base_amount);

            // 5. Calculate add-on amounts
            let addons_total = 0;

            for (let row of frm.doc.addons || []) {

                row.amount = (row.rate || 0) * (row.quantity || 0);

                addons_total = addons_total + row.amount;
            }

            // 6. Set add-ons total
            frm.set_value("addons_total", addons_total);

            // 7. Calculate total amount
            let total_amount = base_amount + addons_total;

            frm.set_value("total_amount", total_amount);
        });
    }
});