frappe.ui.form.on("Booking", {

    validate: function(frm) {

        if (frm.doc.end_time <= frm.doc.start_time) {
            frappe.throw("End Time must be greater than Start Time");
        }

        let start = moment(frm.doc.start_time, "HH:mm:ss");
        let end = moment(frm.doc.end_time, "HH:mm:ss");

        let duration_in_hours = moment
            .duration(end.diff(start))
            .asHours();

        frappe.db.get_value(
            "Resource",
            frm.doc.resource,
            "hourly_rate"
        ).then(r => {

            let hourly_rate = r.message.hourly_rate || 0;
            let base_amount = hourly_rate * duration_in_hours;

            frm.set_value("base_amount", base_amount);

            let addons_total = 0;

            for (let row of frm.doc.addons || []) {
                row.amount = (row.rate || 0) * (row.quantity || 0);
                addons_total = addons_total + row.amount;
            }

            frm.set_value("addons_total", addons_total);

            let total_amount = base_amount + addons_total;

            frm.set_value("total_amount", total_amount);
        });
    },

    setup(frm) {
        frm.set_query("resource", () => {
            if (!frm.doc.member) {
                return {};
            }

            return {
                query: "hatch.hatch.doctype.booking.booking.get_allowed_resources",
                filters: {
                    member: frm.doc.member
                }
            };
        });
    },

    refresh(frm) {


        if (frm.doc.status === "Confirmed") {
            frm.dashboard.add_indicator(__("Confirmed"), "green");
        } else if (frm.doc.status === "Pending") {
            frm.dashboard.add_indicator(__("Pending"), "orange");
        } else if (frm.doc.status === "Cancelled") {
            frm.dashboard.add_indicator(__("Cancelled"), "red");
        } else if (frm.doc.status) {
            frm.dashboard.add_indicator(
                __(frm.doc.status),
                "blue"
            );
        }

        if (
            frm.doc.status === "Confirmed" &&
            frm.doc.docstatus === 1 &&
            frm.doc.booking_date === frappe.datetime.get_today()
        ) {
            frm.add_custom_button(__("Check In"), () => {
                frappe.call({
                    method: "hatch.hatch.doctype.booking.booking.check_in",
                    args: {
                        booking: frm.doc.name
                    },
                    callback(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            });
        }

        if (frm.doc.docstatus === 1) {

            frm.add_custom_button(__("Cancel Booking"), () => {

                let dialog = new frappe.ui.Dialog({
                    title: __("Cancel Booking"),
                    fields: [
                        {
                            label: __("Cancellation Reason"),
                            fieldname: "cancellation_reason",
                            fieldtype: "Small Text",
                            reqd: 1
                        }
                    ],
                    primary_action_label: __("Cancel Booking"),

                    primary_action(values) {

                        frappe.call({
                            method: "hatch.hatch.doctype.booking.booking.cancel_booking",
                            args: {
                                booking: frm.doc.name,
                                cancellation_reason: values.cancellation_reason
                            },
                            callback(r) {
                                if (!r.exc) {
                                    dialog.hide();
                                    frm.reload_doc();
                                    frm.trigger("resource");
                                }
                            }
                        });
                    }
                });

                dialog.show();
            });

            frm.add_custom_button(__("Reassign to Another Member"), () => {

                frappe.prompt(
                    [
                        {
                            label: __("New Member"),
                            fieldname: "new_member",
                            fieldtype: "Link",
                            options: "Member",
                            reqd: 1
                        }
                    ],

                    values => {

                        frappe.confirm(
                            __("Reassign this booking to {0}?", [
                                values.new_member
                            ]),

                            () => {

                                frappe.call({
                                    method: "hatch.hatch.doctype.booking.booking.reassign_booking",
                                    args: {
                                        booking: frm.doc.name,
                                        new_member: values.new_member
                                    },
                                    callback(r) {
                                        if (!r.exc) {
                                            frm.reload_doc();
                                            frm.trigger("resource");
                                        }
                                    }
                                });

                            }
                        );

                    },

                    __("Reassign Booking"),
                    __("Continue")
                );

            });

        }
    },

    resource(frm) {
        check_live_availability(frm);
    },

    booking_date(frm) {
        check_live_availability(frm);
    },

    start_time(frm) {
        check_live_availability(frm);
    },

    end_time(frm) {
        check_live_availability(frm);
    }
});


function check_live_availability(frm) {

    if (
        !frm.doc.resource ||
        !frm.doc.booking_date ||
        !frm.doc.start_time ||
        !frm.doc.end_time
    ) {
        return;
    }

    frappe.call({
        method: "hatch.hatch.doctype.booking.booking.get_live_availability",

        args: {
            resource: frm.doc.resource,
            booking_date: frm.doc.booking_date,
            start_time: frm.doc.start_time,
            end_time: frm.doc.end_time,
            booking: frm.doc.name
        },

        callback(r) {
            if (r.message) {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: r.message.available ? "green" : "red"
                });
            }
        }
    });
}