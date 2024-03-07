// Copyright (c) 2024, Quantbit Technologies Pvt ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Job Work', {
	// refresh: function(frm) {

	// }
});

function outclearAndRefreshTables(frm) {
    frm.clear_table("items_outsourcing_job_work");
    frm.refresh_field('items_outsourcing_job_work');

    frm.clear_table("raw_outsourcing_job_work");
    frm.refresh_field('raw_outsourcing_job_work');
}

function inclearAndRefreshTables(frm) {
    frm.clear_table("in_finished_item_outsource_job_work");
    frm.refresh_field('in_finished_item_outsource_job_work');

    frm.clear_table("in_raw_item_outsourcing_job_work");
    frm.refresh_field('in_raw_item_outsourcing_job_work');

	frm.clear_table("in_loan_items_outsourcing_job_work");
    frm.refresh_field('in_loan_items_outsourcing_job_work');
}

function append_rejected_items_reasons(frm) {
    frm.clear_table("rejected_items_reasons");
    frm.refresh_field('rejected_items_reasons');

	frm.call({
		method: 'rejected_item',
		doc: frm.doc,
	})

}

// ================================================================================== Subcontracting Job Work ================================================================================== 

var company_field = 'custom_company'

frappe.ui.form.on("Subcontracting Job Work", {
    setup: function (frm) {

		frm.fields_dict.subcontracting_job_work.get_query = function (doc, cdt, cdn) {
            return {
                filters: [
                    ['Subcontracting Job Work', 'docstatus', '=', 1],
                    ['Subcontracting Job Work', 'supplier_id', '=', frm.doc.supplier_id],
                    ['Subcontracting Job Work', 'in_or_out', '=', 'OUT'],
                    ['Subcontracting Job Work', 'entry_type', '=', frm.doc.entry_type],
                ]
            };
        };

		frm.set_query("source_warehouse", function () { // Replace with the name of the link field
			return {
				filters: [
					["Warehouse", "company", '=', frm.doc.company] // Replace with your actual filter criteria
				]
			};
		});

		frm.set_query("target_warehouse", function () { // Replace with the name of the link field
			return {
				filters: [
					["Warehouse", "company", '=', frm.doc.company] // Replace with your actual filter criteria
				]
			};
		});

		frm.set_query("rejection_target_warehouse", function () { // Replace with the name of the link field
			return {
				filters: [
					["Warehouse", "company", '=', frm.doc.company] // Replace with your actual filter criteria
				]
			};
		});

		frm.set_query("linking_option", function () { // Replace with the name of the link field
			return {
				filters: [
					["DocType", "name", 'in', ["Blanket Order", "Purchase Order"]] // Replace with your actual filter criteria
				]
			};
		});

		frm.set_query("blanket_order", function () { // Replace with the name of the link field
			return {
				filters: [
					["Blanket Order", "blanket_order_type", '=', 'Purchasing'],
					["Blanket Order", "supplier", '=', frm.doc.supplier_id] ,
					["Blanket Order", "company", '=', frm.doc.company]
				]
			};
		});

		frm.set_query("purchase_order", function () { // Replace with the name of the link field
			return {
				filters: [
					["Purchase Order", "supplier", '=', frm.doc.supplier_id], 
                    ["Purchase Order", "company", '=', frm.doc.company]
				]
			};
		});

		frm.set_query("finished_item_code", "items_outsourcing_job_work", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: [
					["Item", company_field, '=', frm.doc.company],
				]
            };
        });


		frm.set_query("finished_item_code", "items_bom_outsourcing_job_work", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: [
					["Outsourcing BOM", 'company', '=', frm.doc.company],
				]
            };
        });

		frm.set_query("finished_item_code", "loan_items_outsourcing_job_work", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: [
					["Item", company_field, '=', frm.doc.company],
				]
            };
        });

		frm.set_query("source_warehouse", "loan_items_outsourcing_job_work", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: [
					["Warehouse", "company", '=', frm.doc.company],
				]
            };
        });
		frm.set_query("target_warehouse", "loan_items_outsourcing_job_work", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: [
					["Warehouse", "company", '=', frm.doc.company],
				]
            };
        });


    }
});


frappe.ui.form.on('Subcontracting Job Work', {
    blanket_order: function (frm) {
		outclearAndRefreshTables(frm);

        frm.call({
            method: 'set_order_data',
            doc: frm.doc,
        })

    }
});

frappe.ui.form.on('Subcontracting Job Work', {
    purchase_order: function (frm) {
		outclearAndRefreshTables(frm);

        frm.call({
            method: 'set_order_data',
            doc: frm.doc,
        })

    }
});


frappe.ui.form.on('Subcontracting Job Work', {
	source_warehouse: function (frm) {
		if (frm.doc.in_or_out == 'OUT') {
			if (frm.doc.entry_type == 'Material Loan Given') {
				var args = {
					table: 'loan_items_outsourcing_job_work',
					table_field: 'source_warehouse',
					field_data: frm.doc.source_warehouse,
				};
			}
			else {
				var args = {
					table: 'raw_outsourcing_job_work',
					table_field: 'source_warehouse',
					field_data: frm.doc.source_warehouse,
				};
			}
		}
		else {
			if (frm.doc.entry_type == 'Material Loan Given') {
				var args = {
					table: 'in_loan_items_outsourcing_job_work',
					table_field: 'source_warehouse',
					field_data: frm.doc.source_warehouse,
				};
			}
			else {
				var args = {
					table: 'in_raw_item_outsourcing_job_work',
					table_field: 'source_warehouse',
					field_data: frm.doc.source_warehouse,
				};
			}
		}

		frm.call({
			method: 'set_table_data',
			args: args,
			doc: frm.doc,
		})
	}
});

frappe.ui.form.on('Subcontracting Job Work', {
	target_warehouse: function (frm) {
		if (frm.doc.in_or_out == 'OUT') {
			if (frm.doc.entry_type == 'Material Loan Given') {
				var args = {
					table: 'loan_items_outsourcing_job_work',
					table_field: 'target_warehouse',
					field_data: frm.doc.target_warehouse,
				};

				frm.call({
					method: 'set_table_data',
					args: args,
					doc: frm.doc,
				})
			}
		}
		else {
			if (frm.doc.entry_type == 'Material Loan Given') {

				var args = {
					table: 'in_loan_items_outsourcing_job_work',
					table_field: 'target_warehouse',
					field_data: frm.doc.target_warehouse,
				}
			}
			else {
				var args = {
					table: 'in_finished_item_outsource_job_work',
					table_field: 'target_warehouse',
					field_data: frm.doc.target_warehouse,
				}
			}

			frm.call({
				method: 'set_table_data',
				args: args,
				doc: frm.doc,
			})
		}

	}
});

frappe.ui.form.on('Subcontracting Job Work', {
	rejection_target_warehouse: function (frm) {
		if (frm.doc.in_or_out == 'IN') {
				var args = {
					table: 'rejected_items_reasons',
					table_field: 'target_warehouse',
					field_data: frm.doc.rejection_target_warehouse,
				};

				frm.call({
					method: 'set_table_data',
					args: args,
					doc: frm.doc,
				})
		}
	}
});


frappe.ui.form.on('Subcontracting Job Work', {
    subcontracting_job_work: function (frm) {
		inclearAndRefreshTables(frm);

        frm.call({
            method: 'set_in_finished_item_outsource_job_work',
            doc: frm.doc,
        })

    }
});
// ================================================================================== Items Outsourcing Job Work ================================================================================== 

frappe.ui.form.on('Items Outsourcing Job Work', {
    production_quantity : function (frm) {
		var args = {
			table: 'items_outsourcing_job_work',
		};
        frm.call({
            method: 'set_quantity_raw_order_data',
			args: args,
            doc: frm.doc,
        })

    }
});

// ================================================================================== Items Bom Outsourcing Job Work ================================================================================== 

frappe.ui.form.on('Items Bom Outsourcing Job Work', {
    finished_item_code: function (frm) {

	frm.clear_table("raw_outsourcing_job_work");
    frm.refresh_field('raw_outsourcing_job_work');
	var args = {
		table: 'items_bom_outsourcing_job_work',
	};

	frm.call({
		method:'set_raw_order_data',
		args: args,
		doc:frm.doc,
	})
    }
});

frappe.ui.form.on('Items Bom Outsourcing Job Work', {
    production_quantity : function (frm) {

        var args = {
			table: 'items_bom_outsourcing_job_work',
		};
        frm.call({
            method: 'set_quantity_raw_order_data',
			args: args,
            doc: frm.doc,
        })
    }
});

// ================================================================================== Loan Items Outsourcing Job Work ================================================================================== 
frappe.ui.form.on('Loan Items Outsourcing Job Work', {
    finished_item_code: function(frm) {

        frm.call({
			method:'set_warehouses_in_loan_table',
			doc:frm.doc,
		})
	
    }
});


// ================================================================================== IN Finished Item Outsource Job Work ================================================================================== 


frappe.ui.form.on('IN Finished Item Outsource Job Work', {
    quantity: function (frm) {
        frm.call({
            method: 'raw_material_qty',
            doc: frm.doc,
        })


    }
});

frappe.ui.form.on('IN Finished Item Outsource Job Work', {cr_casting_rejection: function (frm) {append_rejected_items_reasons(frm);}});
frappe.ui.form.on('IN Finished Item Outsource Job Work', {mr_machine_rejection: function (frm) {append_rejected_items_reasons(frm); }});
frappe.ui.form.on('IN Finished Item Outsource Job Work', {rw_rework: function (frm) {append_rejected_items_reasons(frm);}});
frappe.ui.form.on('IN Finished Item Outsource Job Work', {as_it_is: function (frm) {append_rejected_items_reasons(frm);}});