# Copyright (c) 2023, Quantbit Technologies Pvt ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OutsourcingBOM(Document):
	def before_save(self):
		outsourcing_bom_details = self.get("outsourcing_bom_details")
		for d in outsourcing_bom_details:
			item_uom = frappe.get_value("Item",d.item_code,"stock_uom")
			if item_uom == 'Kg':
				item_weight = frappe.get_value("Item",d.item_code,"weight")
			else:
				production_uom_definition = frappe.get_all("Production UOM Definition",
											   										filters = {"parent":d.item_code,"uom": 'Kg'},
																					fields = ["value_per_unit"])
				if production_uom_definition:
					for k in production_uom_definition:
						item_weight= k.value_per_unit
				else:
					frappe.throw(f'Please Set "Production UOM Definition" For Item {d.item_code}-{d.item_name} of UOM "Kg" ')

			d.weight_per_unit = item_weight
			d.total_required_weight = item_weight * d.required_quantity


