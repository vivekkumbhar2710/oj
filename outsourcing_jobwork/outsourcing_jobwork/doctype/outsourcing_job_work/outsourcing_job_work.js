// Copyright (c) 2023, Quantbit Technologies Pvt ltd and contributors
// For license information, please see license.txt


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
        frm.fields_dict['linking_option'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['select_link'].$input.css('background-color', '#D2E9FB');

        frm.fields_dict['loan_material_item_code'].$input.css('background-color', '#D2E9FB');
        frm.fields_dict['loan_material_item_name'].$input.css('background-color', '#D2E9FB');

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
		});
        frm.call({
            method:'getting_weight',
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
            },);
           
	}
    frm.call({
        method:'getting_weight',
        doc:frm.doc,
    })

    }
});

frappe.ui.form.on('Outsourcing Job Work', {
    outsourcing_job_work: function(frm) {

	

            frm.clear_table("outsource_job_work_details");
            frm.refresh_field('outsource_job_work_details');

            frm.clear_table("finished_item_outsource_job_work_details");
            frm.refresh_field('finished_item_outsource_job_work_details');

            frm.clear_table("outsource_as_it_is_item");
            frm.refresh_field('outsource_as_it_is_item');

            frm.call({
                method:'in_outsouring_data',
                doc:frm.doc,
            })
            
            frm.call({
                method:'get_as_it_is_item',
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
            frm.clear_table("taxes_and_charges");
            frm.refresh_field('taxes_and_charges');
            frm.doc.total_taxes_and_charges=""
            frm.doc.grand_total=""
            frm.doc.sales_taxes_and_charges_template=""
            if(frm.doc.in_or_out=="IN")
            {
                frm.fields_dict['taxes_and_charges'].toggle(false);
                frm.fields_dict['total_taxes_and_charges'].toggle(false);
                frm.fields_dict['grand_total'].toggle(false);
                frm.fields_dict['sales_taxes_and_charges_template'].toggle(false);
            } 
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
                    ['Outsourcing Job Work', 'entry_type', '=', frm.doc.entry_type],
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

frappe.ui.form.on("Outsourcing Job Work", {
    setup: function(frm) {
            frm.set_query("linking_option", function() { // Replace with the name of the link field
                return {
                    filters: [
                        ["DocType", "name", 'in', ["Blanket Order","Purchase Order"]] // Replace with your actual filter criteria
                    ]
                };
            });
        }
    });

    
    frappe.ui.form.on("Outsourcing Job Work", {
        setup: function (frm) {
            frm.set_query("select_link", function () { // Replace with the name of the link field
                if (frm.doc.linking_option == "Blanket Order") {
                    return {
    
                        filters: [
                            ["Blanket Order", "blanket_order_type", '=', 'Purchasing'],
                            ["Blanket Order", "supplier", '=', frm.doc.supplier_id] // Replace with your actual filter criteria
                        ]
                    };
                }
                if (frm.doc.linking_option == "Purchase Order") {
                    return {
    
                        filters: [
                            ["Purchase Order", "supplier", '=', frm.doc.supplier_id] // Replace with your actual filter criteria
                        ]
                    };
                } 
            });
        }
    });

    frappe.ui.form.on("Outsourcing Job Work", {
        setup: function(frm) {
                frm.set_query("loan_material_item_code", function() { // Replace with the name of the link field
                    return {
                        filters: [
                            ["Item", "custom_company", '=', frm.doc.company] // Replace with your actual filter criteria
                        ]
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


// ============================================================= Program for Outsource As It Is Item Table =================================================  

frappe.ui.form.on('Outsourcing Job Work', {
	refresh: function(frm) {
        frm.fields_dict['outsource_as_it_is_item'].toggle(false);
        frm.refresh_fields();
        
        frm.fields_dict['target_warehouse_for_as_it_is_item'].toggle(false);
        frm.refresh_fields();
    },
    target_warehouse_for_as_it_is_item: function(frm) {
        frm.call({
			method:'set_target_warehouse_for_as_it_is',
			doc:frm.doc,
		})
    },
    setup: function(frm) {
        frm.call({
			method:'get_company_address',
			doc:frm.doc,
		})
    },
    supplier_id: function(frm) {
        frm.doc.supplier_address=""
        frm.doc.address=""
        frm.doc.billing_address_gstin=""
        frm.doc.gst_category=""
        frm.doc.place_of_supply=""
        frm.doc.territory=""
        frm.doc.contact_person=""
        frm.doc.total_quantity=""
        frm.doc.total_amount=""
        frm.doc.sales_taxes_and_charges_template=""
        frm.doc.finished_item_code=""
        frm.doc.finished_item_name=""
        frm.doc.production_quantity=""
        frm.doc.total_taxes_and_charges=""
        frm.doc.grand_total=""
        frm.clear_table("taxes_and_charges")
        frm.clear_table("outsource_job_work_details")
        frm.call({
			method:'get_supplier_address',
			doc:frm.doc,
		})
    },
    total_amount: function(frm) {
        frm.clear_table("taxes_and_charges")
        frm.call({
			method:'get_in_out_tax_template',
			doc:frm.doc,
		})
    },
  
});
frappe.ui.form.on('Outsource Job Work Details', {
    // as_it_is:function(frm){
    //     frm.call({
    //         method:"get_as_it_is_item",
    //         doc:frm.doc
    //     });
    // },
    source_warehouse: function(frm,cdt,cdn) {
        let d = locals[cdt][cdn];
        let table = frm.fields_dict['outsource_job_work_details'].grid;
        let table_index = table.grid_rows.findIndex(row => row.doc === d);
        frm.call({
			method:'get_item_rate',
			args: {
                item_index: table_index
            },
            doc:frm.doc,
		})
        frm.doc.total_amount=frm.doc.rate*frm.doc.quantity
    },
    tax_template: function(frm) {
        frm.call({
			method:'update_item_amount',
			args: {
                index: null
            },
            doc: frm.doc,
		})
    },
    rate:function(frm,cdt,cdn) {
        let d = locals[cdt][cdn];
        let table = frm.fields_dict['outsource_job_work_details'].grid;
        let table_index = table.grid_rows.findIndex(row => row.doc === d);
        frm.call({
			method:'update_item_amount',
			args: {
                index: table_index
            },
            doc: frm.doc,
		})
    }
});

frappe.ui.form.on('Finished Item Outsource Job Work Details', {
	as_it_is: function(frm) {
        frm.fields_dict['outsource_as_it_is_item'].toggle(true);
        frm.refresh_fields();
        frm.fields_dict['target_warehouse_for_as_it_is_item'].toggle(true);
        frm.refresh_fields();
        var qty_sum=0
        var flag=true
        frm.doc.finished_item_outsource_job_work_details.forEach(function(row) {
            qty_sum=row.quantity+row.cr_casting_rejection+row.mr_machine_rejection+row.rw_rework+row.as_it_is
            if(qty_sum>parseFloat(row.actual_required_quantity))
            {
                
                frappe.throw(`Total Quantity For Item ${row.item_code}-${row.item_name} is Should Not Be Greater Than Actual Required Quantity `)
            }
            else
            {
                if(parseFloat(row.as_it_is)!=parseFloat(row.actual_required_quantity))
                {
                    flag=false
                }
                row.total_quantity=qty_sum
                row.total_finished_weight=row.weight_per_unit * row.quantity
            }
        });
        if(flag)
        {
            frm.fields_dict['rejected_items_reasons'].toggle(false);
            frm.refresh_fields();
            frm.fields_dict['outsource_job_work_details'].toggle(false);
            frm.refresh_fields();
            frm.fields_dict['get_rejections'].toggle(false);
            frm.refresh_fields();
            frm.doc.total_quantity=null
            frm.refresh_fields();
            frm.doc.total_amount=null
            frm.refresh_fields();
        }
    }
});
frappe.ui.form.on('Finished Item Outsource Job Work Details', {
    as_it_is:function(frm){
        frm.call({
            method:"get_as_it_is_item",
            doc:frm.doc
        });
    }
})
// frappe.ui.form.on('Outsourcing Job Work', {
//     target_warehouse_for_as_it_is_item: function(frm) {
//         frm.call({
// 			method:'set_target_warehouse_for_as_it_is',
// 			doc:frm.doc,
// 		})
//     }
// });

//Below code for to get item rate

//Below code for to get compnay address
// frappe.ui.form.on('Outsourcing Job Work', {
//     setup: function(frm) {
//         frm.call({
// 			method:'get_company_address',
// 			doc:frm.doc,
// 		})
//     }
// });

// frappe.ui.form.on('Outsourcing Job Work', {
//     supplier_id: function(frm) {
//         frm.call({
// 			method:'get_supplier_address',
// 			doc:frm.doc,
// 		})
//     }
// });

// frappe.ui.form.on('Outsource Job Work Details', {
//     tax_template: function(frm) {
//         frm.call({
// 			method:'get_tax_temp',
// 			doc:frm.doc,
// 		})
//     }
// });

// frappe.ui.form.on('Outsourcing Job Work', {
//     total_amount: function(frm) {
//         frm.call({
// 			method:'get_in_out_tax_template',
// 			doc:frm.doc,
// 		})
//     }
// });