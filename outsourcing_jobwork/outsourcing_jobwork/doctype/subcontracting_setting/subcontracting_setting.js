// Copyright (c) 2024, Quantbit Technologies Pvt ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Setting', {
	// refresh: function(frm) {

	// }
});


function set_field_filter(frm) {
	const field_filter = [
		{ field: "cr_warehouse", filter: [["Warehouse", "company", '=', frm.doc.company],["Warehouse", "is_group", '=', 0]] },
		{ field: "mr_warehouse", filter: [["Warehouse", "company", '=', frm.doc.company],["Warehouse", "is_group", '=', 0]] },
		{ field: "rw_warehouse", filter: [["Warehouse", "company", '=', frm.doc.company],["Warehouse", "is_group", '=', 0]] },
		{ field: "as_it_is_warehouse", filter: [["Warehouse", "company", '=', frm.doc.company],["Warehouse", "is_group", '=', 0]]},
		{ field: "default_expense_account", filter: [["Account", "Account_type", '=', 'Expenses Included In Valuation'],["Account", "company", '=', frm.doc.company]] },
	];

	for (const i of field_filter) {
		frm.set_query(i.field, function () {
			return {
				filters: i.filter
			};
		});
	}
}


frappe.ui.form.on("Subcontracting Setting", {
	setup: function (frm) {
		set_field_filter(frm);
	}
});
