// Copyright (c) 2023, Quantbit Technologies Pvt ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Outsourcing Job Work', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Outsourcing Job Work', {
    refresh: function(frm) {
        frm.fields_dict['supplier_id'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['supplier_name'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['in_or_out'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['outsourcing_job_work'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['naming_series'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['company'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['posting_date'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['posting_time'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['source_warehouse'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['target_warehouse'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['finished_item_code'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['finished_item_name'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['production_quantity'].$input.css('background-color', '#D2E9FB');
    }
});


// ============================================================= Outsourcing Job Work ================================================= 

frappe.ui.form.on('Outsourcing Job Work', {
    source_warehouse: function(frm) {
        frm.call({
			method:'set_source_warehouse',
			doc:frm.doc,
		})
    }
});

frappe.ui.form.on('Outsourcing Job Work', {
    target_warehouse: function(frm) {
        frm.call({
			method:'set_target_warehouse',
			doc:frm.doc,
		})
    }
});

frappe.ui.form.on('Outsourcing Job Work', {
    production_quantity: function(frm) {

        frm.clear_table("outsource_job_work_details");
		frm.refresh_field('outsource_job_work_details');

        frm.call({
			method:'set_data_in_ojwd',
			doc:frm.doc,
		})
    }
});


frappe.ui.form.on('Outsourcing Job Work', {
    finished_item_code: function(frm) {

		if (frm.doc.production_quantity) {

            frm.clear_table("outsource_job_work_details");
            frm.refresh_field('outsource_job_work_details');
    
            frm.call({
                method:'set_data_in_ojwd',
                doc:frm.doc,
            })
	}

    }
});

frappe.ui.form.on('Outsourcing Job Work', {
    outsourcing_job_work: function(frm) {

	

            frm.clear_table("outsource_job_work_details");
            frm.refresh_field('outsource_job_work_details');

            frm.clear_table("finished_item_outsource_job_work_details");
            frm.refresh_field('finished_item_outsource_job_work_details');
    
            frm.call({
                method:'in_outsouring_data',
                doc:frm.doc,
            })
	
    }
});

frappe.ui.form.on('Outsourcing Job Work', {
    in_or_out: function(frm) {

            frm.clear_table("outsource_job_work_details");
            frm.refresh_field('outsource_job_work_details');
            frm.clear_table("outsourcing_job_work");
            frm.refresh_field('outsourcing_job_work');
    }
});


frappe.ui.form.on('Outsourcing Job Work', {
    setup: function(frm) {
        frm.fields_dict.outsourcing_job_work.get_query = function(doc, cdt, cdn) {
            return {
                filters: [
                    ['Outsourcing Job Work', 'docstatus', '=', 1],
                    ['Outsourcing Job Work', 'supplier_id', '=', frm.doc.supplier_id],
                    ['Outsourcing Job Work', 'in_or_out', '=', 'OUT'],
                    ['Outsourcing Job Work', 'process_status', '!=', 'Done'],
                ]
            };
        };
    }
});


frappe.ui.form.on('Outsourcing Job Work', {
    get_rejections: function(frm) {



            frm.clear_table("rejected_items_reasons");
            frm.refresh_field('rejected_items_reasons');
    
            frm.call({
                method:'set_dat_in_rejected_items_reasons',
                doc:frm.doc,
            })
	

    }
});


frappe.ui.form.on('Outsourcing Job Work', {
    setup: function(frm) {
        frm.set_query("rejection_reason", "rejected_items_reasons", function(doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    'rejection_type': d.rejection_type
                }
            };
        });
    }
});


// ============================================================= Outsource Job Work Details =================================================  

frappe.ui.form.on('Outsource Job Work Details', {
    item_code: function(frm) {
        frm.call({
			method:'set_warehouse_after_item',
			doc:frm.doc,
		})
    }
});

frappe.ui.form.on('Outsource Job Work Details', {
    is_finished_item: function(frm) {
        frm.call({
			method:'set_finished_item',
			doc:frm.doc,
		})
        

    }
});

// ============================================================= Finished Item Outsource Job Work Details =================================================  

frappe.ui.form.on('Finished Item Outsource Job Work Details', {
    quantity: function(frm) {
        frm.call({
			method:'if_in_fill_ojwd',
			doc:frm.doc,
		})
        

    }
});

frappe.ui.form.on('Finished Item Outsource Job Work Details', {
    cr_casting_rejection: function(frm) {
        frm.call({
			method:'finish_total_quentity_calculate',
			doc:frm.doc,
		})
        

    }
});
frappe.ui.form.on('Finished Item Outsource Job Work Details', {
    mr_machine_rejection: function(frm) {
        frm.call({
			method:'finish_total_quentity_calculate',
			doc:frm.doc,
		})
        

    }
});
frappe.ui.form.on('Finished Item Outsource Job Work Details', {
    rw_rework: function(frm) {
        frm.call({
			method:'finish_total_quentity_calculate',
			doc:frm.doc,
		})
        

    }
});