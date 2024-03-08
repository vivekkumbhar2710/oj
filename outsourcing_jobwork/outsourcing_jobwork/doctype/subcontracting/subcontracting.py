# Copyright (c) 2024, Quantbit Technologies Pvt ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def getVal(val):
	return val if val is not None else 0

def ItemName(item_code):
	return frappe.get_value('Item', item_code , 'item_name')

def get_available_quantity(item_code, warehouse):
		result = frappe.get_value("Bin",{"item_code": item_code,"warehouse": warehouse}, "actual_qty")
		return result if result else 0
def ItemWeight(item_code):
	item_uom = frappe.get_value("Item",item_code,"stock_uom")
	if item_uom == 'Kg':
		item_weight = frappe.get_value("Item",item_code,"weight")
	else:
		item_weight = frappe.get_value('Production UOM Definition',{'parent': item_code ,'uom':'Kg'}, "value_per_unit")
	return item_weight if item_weight else 0


class Subcontracting(Document):
	@frappe.whitelist()
	def before_save(self):
		if self.in_or_out == 'OUT':
			pass
		else:
			self.validate_entry()

	@frappe.whitelist()
	def before_submit(self):
		if self.in_or_out == 'OUT':
			if self.out_entry_type == 'Material Loan Given':
				self.stock_transfer_stock_entry('loan_items_subcontracting' , 'finished_item_code' , 'production_quantity' , 'source_warehouse' , 'target_warehouse' )
			else:
				self.stock_transfer_stock_entry('items_subcontracting' , 'raw_item_code' , 'production_quantity' , 'source_warehouse' , 'target_warehouse')
		else:
			if self.out_entry_type == 'Material Loan Given':
				pass
			else:
				self.manifacturing_stock_entry()
				self.stock_transfer_stock_entry('in_rejected_items_reasons_subcontracting' , 'raw_item_code' , 'quantity' , 'source_warehouse' , 'target_warehouse')
				self.update_out_entry()

	def before_cancel(self):
		self.cancel_update_out_entry()


# =================================================================================================== BOTH ===================================================================================================

	@frappe.whitelist()
	def set_table_data(self , table , table_field , field_data , qty_field = None, item_code = None , warehouse_field = None):
		items_table = self.get(table)
		for i in items_table:
			setattr(i, table_field, field_data)
			if qty_field and i.get(item_code) and i.get(warehouse_field) :
				setattr(i, qty_field, get_available_quantity(i.get(item_code), i.get(warehouse_field)))


	@frappe.whitelist()
	def set_available_qty(self , table , qty_field, item_code , warehouse_field):
		items_table = self.get(table)
		for i in items_table:
			if i.get(item_code) and i.get(warehouse_field) :
				setattr(i, qty_field, get_available_quantity(i.get(item_code), i.get(warehouse_field)))



	@frappe.whitelist()
	def stock_transfer_stock_entry(self , table , item_code , quantity , source_warehouse , target_warehouse):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.company = self.company
		se.posting_date = self.posting_date
		for d in self.get(table):
			se.append("items",
						{
							"item_code": d.get(item_code),
							"qty": d.get(quantity),
							"s_warehouse": d.get(source_warehouse),
							"t_warehouse": d.get(target_warehouse),
						},)
		se.custom_subcontracting = self.name	
		if se.items:
			se.insert()
			se.save()
			se.submit()

# =================================================================================================== IN ===================================================================================================
	@frappe.whitelist()
	def set_in_finished_item(self):
		if self.in_entry_type == 'Subcontracting' and self.linking_option and (self.blanket_order or self.purchase_order) :
			if self.linking_option == 'Blanket Order':
				b_o_l = []
				for i in self.blanket_order:
					b_o_l.append(str(i.blanket_order))

				doctype = 'Blanket Order Item'
				filters = {'parent':['in',b_o_l]}
				fields = ['item_code' , 'parent','custom_subcontracting_operations','rate']

			else:
				p_o_l = []
				for j in self.purchase_order:
					p_o_l.append(str(j.purchase_order))

				doctype = 'Purchase Order Item'
				filters = {'parent':['in',p_o_l]}
				fields = ['item_code' , 'parent','custom_subcontracting_operations','rate']

			doc = frappe.get_all(doctype , filters = filters , fields = fields)
			# frappe.throw(str(doc))
			for d in doc:
				self.append("in_finished_item_subcontracting",{
											'in_item_code': d.item_code,
											'in_item_name': ItemName(d.item_code),
											'order_type': self.linking_option,
											'select_order': d.parent,
											'operation': d.custom_subcontracting_operations,
											'target_warehouse' : self.target_warehouse,
											'unvaried': frappe.get_value('Subcontracting Operations',d.custom_subcontracting_operations , 'unvaried') if d.custom_subcontracting_operations else False ,
											'weight_per_unit':ItemWeight(d.item_code),
											'rate_from_order': d.rate,
											},),

	@frappe.whitelist()
	def set_raw_order_data(self , table):
		self.finish_total_quantity_calculate()
		items = self.get(table)
		for j in items:
			if j.in_item_code and j.total_quantity:
				if j.unvaried :
					self.append("in_raw_item_subcontracting",
										{	'in_item_code': j.in_item_code ,
											'raw_item_code'	: j.in_item_code ,
											'raw_item_name':ItemName(j.in_item_code),
											'quantity_per_finished_item':1,
											'actual_required_quantity': getVal(j.quantity),
											'quantity': getVal(j.quantity),
											'reference_id': j.name,
											'source_warehouse':self.source_warehouse,
											'weight_per_unit':ItemWeight(j.in_item_code),
											'total_required_weight': ItemWeight(j.in_item_code) * getVal(j.quantity),
										},),
				else:
					bom_exist = frappe.get_value("Outsourcing BOM",j.in_item_code,'name')
					if bom_exist :
						bom = frappe.get_doc("Outsourcing BOM",j.in_item_code)
						child_bom = bom.get("outsourcing_bom_details")
						for k in child_bom:
							self.append("in_raw_item_subcontracting",
										{	'in_item_code': j.in_item_code ,
											'raw_item_code'	: k.item_code,
											'raw_item_name':ItemName(k.item_code),
											'quantity_per_finished_item': k.required_quantity,
											'actual_required_quantity': getVal(j.quantity) * getVal(k.required_quantity),
											'quantity': getVal(j.quantity) * getVal(k.required_quantity),
											'reference_id': j.name,
											'source_warehouse':self.source_warehouse,
											'weight_per_unit':ItemWeight(k.item_code),
											'total_required_weight': ItemWeight(k.item_code) * (getVal(j.quantity) * getVal(k.required_quantity)),
										},),
					else:
						raw_item_code = frappe.get_value("Item",j.in_item_code,'raw_material')
						if raw_item_code:
							self.append("in_raw_item_subcontracting",
										{	'in_item_code': j.in_item_code ,
											'raw_item_code'	: raw_item_code ,
											'raw_item_name':ItemName(raw_item_code),
											'quantity_per_finished_item':1,
											'actual_required_quantity': getVal(j.quantity),
											'quantity': getVal(j.quantity),
											'reference_id': j.name,
											'source_warehouse':self.source_warehouse,
											'weight_per_unit':ItemWeight(raw_item_code),
											'total_required_weight': ItemWeight(raw_item_code) * getVal(j.quantity),
										},),
						else:
							frappe.msgprint(f"There is no 'Raw Material'defined at Item master of Item {j.in_item_code}")
		self.set_table_data('in_finished_item_subcontracting' , 'target_warehouse' , self.target_warehouse ,)
		self.set_out_subcontracting()

	@frappe.whitelist()
	def set_out_subcontracting(self):
		in_raw_item_subcontracting = self.get("in_raw_item_subcontracting")
		raw_item_code_list = []
		supplier_id = self.supplier_id
		company = self.company
		if not supplier_id and company:
			frappe.throw('Please select supplier_id and company')
		for d in in_raw_item_subcontracting:
			raw_item_code_list.append(str(d.raw_item_code))
		data = frappe.db.sql("""
							SELECT a.name name, b.raw_item_code ,b.production_quantity ,b.production_done_quantity , b.name reference_id
							FROM `tabSubcontracting` a
							LEFT JOIN `tabItems Subcontracting` b ON a.name = b.parent
							WHERE b.raw_item_code IN %s AND a.supplier_id = %s AND a.company = %s AND b.docstatus = 1 AND b.out_done = 0
					   		ORDER BY b.raw_item_code
						""",(tuple(raw_item_code_list+['xxxxxx']) ,supplier_id ,company),as_dict="True")
		for i in data:
			self.append("bifurcation_out_subcontracting",
										{	'subcontracting': i.name ,
											'raw_item_code'	: i.raw_item_code ,
											'raw_item_name':ItemName(i.raw_item_code),
											'production_out_quantity': getVal(i.production_quantity) ,
											'production_done_quantity':getVal(i.production_done_quantity) ,
											'production_remaining_quantity': getVal(i.production_quantity) - getVal(i.production_done_quantity),
											'reference_id': i.reference_id,
											'weight_per_unit':ItemWeight(i.raw_item_code),
										},),

	@frappe.whitelist()
	def set_quantity(self):
		in_finished_item_subcontracting = self.get('in_finished_item_subcontracting')
		for i in in_finished_item_subcontracting:
			if not i.reference_id:
				i.reference_id = i.name
			for j in self.get("in_raw_item_subcontracting" , filters = {'reference_id':i.reference_id}):
				actual_required_quantity = getVal(j.quantity_per_finished_item) * getVal(i.quantity)
				j.actual_required_quantity = actual_required_quantity
				j.quantity = actual_required_quantity

		self.finish_total_quantity_calculate()


	@frappe.whitelist()
	def rejected_item(self):
		self.set_quantity()
		in_finished =  self.get('in_finished_item_subcontracting')
		for i in in_finished :
			in_raw = self.get('in_raw_item_subcontracting' , filters = {'reference_id': i.reference_id,})
			for j in in_raw :
				as_it_is = getVal(j.quantity_per_finished_item) * getVal(i.as_it_is)
				cr_casting_rejection = getVal(j.quantity_per_finished_item) * getVal(i.cr_casting_rejection)
				mr_machine_rejection = getVal(j.quantity_per_finished_item) * getVal(i.mr_machine_rejection)
				rw_rework = getVal(j.quantity_per_finished_item) * getVal(i.rw_rework)
				if as_it_is:
					self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': i.in_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': as_it_is,
								'rejection_type' :'AS IT IS (AS IT AS)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':i.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
								'total_rejected_weight': ItemWeight(j.raw_item_code) * as_it_is,
							},),
				if cr_casting_rejection:
					self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': i.in_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': cr_casting_rejection,
								'rejection_type' :'CR (Casting Rejection)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':i.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
								'total_rejected_weight': ItemWeight(j.raw_item_code) * cr_casting_rejection,
							},),
				if mr_machine_rejection:
					self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': i.in_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': mr_machine_rejection,
								'rejection_type' :'MR (Machine Rejection)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':i.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
								'total_rejected_weight': ItemWeight(j.raw_item_code) * mr_machine_rejection,
							},),
				if rw_rework:
					self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': i.in_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': rw_rework,
								'rejection_type' :'RW (Rework)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':i.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
								'total_rejected_weight': ItemWeight(j.raw_item_code) * rw_rework,
							},),

	@frappe.whitelist()
	def finish_total_quantity_calculate(self):
		for j in self.get("in_finished_item_subcontracting"):
			j.total_quantity = getVal(j.quantity) + getVal(j.cr_casting_rejection) + getVal(j.mr_machine_rejection) + getVal(j.rw_rework) + getVal(j.as_it_is)
			j.total_finished_weight =  j.total_quantity * getVal(j.weight_per_unit)
			j.total_amount = j.total_quantity * getVal(j.rate_from_order)

	@frappe.whitelist()
	def bifurgation_quantity_calculate(self):
		for j in self.get("bifurcation_out_subcontracting"):
			j.production_quantity = getVal(j.ok_quantity) + getVal(j.cr_quantity) + getVal(j.mr_quantity) + getVal(j.rw_quantity) + getVal(j.as_it_is_quantity)
			j.total_finished_weight =  j.production_quantity * getVal(j.weight_per_unit)
			# j.total_amount = j.total_quantity * getVal(j.rate_from_order)


	@frappe.whitelist()
	def validate_entry(self):
		result_dict = {}
		out_raw_dict = {}

		for j in self.get("in_raw_item_subcontracting"):
			raw_item_code, quantity = j.raw_item_code, j.quantity

			if raw_item_code not in result_dict:
				result_dict[raw_item_code] = [0, 0]

			result_dict[raw_item_code][0] += quantity
			result_dict[raw_item_code][1] = max(quantity, result_dict[raw_item_code][1])

		for k in self.get("in_rejected_items_reasons_subcontracting"):
			raw_item_code, quantity = k.raw_item_code, k.quantity

			if raw_item_code not in result_dict:
				result_dict[raw_item_code] = [0, 0]

			result_dict[raw_item_code][0] += quantity
			result_dict[raw_item_code][1] = max(quantity, result_dict[raw_item_code][1])

		for l in self.get("bifurcation_out_subcontracting"):
			raw_item_code , quantity = l.raw_item_code , l.production_quantity
			out_raw_dict[raw_item_code] = out_raw_dict.get(raw_item_code, 0) + quantity



		for item, qty_range in result_dict.items():
			max_qty ,min_qty = qty_range
			b_qty = out_raw_dict.get(item, None)

			if b_qty is not None and not (min_qty <= b_qty <= max_qty):
				frappe.throw(f"The Quantity for Raw Item '{item}' is should not be more than {max_qty} and should not be less than {min_qty}")
			if b_qty is None:
				frappe.throw(f"You Can Not Inword {item} As It Have Not Any Out Entry")


	@frappe.whitelist()
	def set_source_warehouse(self):
		self.set_table_data('in_raw_item_subcontracting','source_warehouse',self.source_warehouse,'available_quantity','raw_item_code','source_warehouse')
		self.set_table_data('in_rejected_items_reasons_subcontracting','source_warehouse', self.source_warehouse,'available_quantity','raw_item_code','source_warehouse')




	@frappe.whitelist()
	def validate_bifurcation_out_subcontracting(self):
		for i in self.get('bifurcation_out_subcontracting'):
			if i.production_remaining_quantity < i.production_quantity:
				frappe.msgprint("You Can Not Set 'Production Quantity' More Than 'Production Remaining Quantity'")
				i.production_quantity = 0

	@frappe.whitelist()
	def update_get_rejections(self):
		in_finished =  self.get('in_finished_item_subcontracting')
		for i in in_finished :
			as_it_is = 0
			for j in self.get('in_rejected_items_reasons_subcontracting', filters = {'reference_id': i.reference_id , 'rejection_type': 'AS IT IS (AS IT AS)'}):
				as_it_is = as_it_is + j.quantity
			
			if i.as_it_is > as_it_is:
				self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': j.finished_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': i.as_it_is - as_it_is ,
								'rejection_type' : 'AS IT IS (AS IT AS)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':j.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
							},),


			cr_casting_rejection = 0
			for j in self.get('in_rejected_items_reasons_subcontracting', filters = {'reference_id': i.reference_id , 'rejection_type': 'CR (Casting Rejection)'}):
				cr_casting_rejection = cr_casting_rejection + j.quantity
			
			if i.cr_casting_rejection > cr_casting_rejection:
				self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': j.finished_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': i.cr_casting_rejection - cr_casting_rejection ,
								'rejection_type' : 'CR (Casting Rejection)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':j.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
							},),

			mr_machine_rejection = 0
			for j in self.get('in_rejected_items_reasons_subcontracting', filters = {'reference_id': i.reference_id , 'rejection_type': 'MR (Machine Rejection)'}):
				mr_machine_rejection = mr_machine_rejection + j.quantity
			
			if i.mr_machine_rejection > mr_machine_rejection:
				self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': j.finished_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': i.mr_machine_rejection - mr_machine_rejection ,
								'rejection_type' : 'MR (Machine Rejection)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':j.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
							},),

			rw_rework = 0
			for j in self.get('in_rejected_items_reasons_subcontracting', filters = {'reference_id': i.reference_id , 'rejection_type': 'RW (Rework)'}):
				rw_rework = rw_rework + j.quantity
			
			if i.rw_rework > rw_rework:
				self.append("in_rejected_items_reasons_subcontracting",{
								'finished_item_code': j.finished_item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': i.rw_rework - rw_rework ,
								'rejection_type' : 'RW (Rework)' ,
								'source_warehouse': j.source_warehouse,
								'reference_id':j.reference_id,
								'weight_per_unit':ItemWeight(j.raw_item_code),
							},),




	@frappe.whitelist()
	def manifacturing_stock_entry(self):
		if self.in_or_out == 'IN':
			in_finished =  self.get('in_finished_item_subcontracting' , filters = {'quantity': ['not in',(None,0)]})
			for i in in_finished :
				se = frappe.new_doc("Stock Entry")
				se.stock_entry_type = "Manufacture"
				se.company = self.company
				se.posting_date = self.posting_date
				in_raw = None
				in_raw = self.get('in_raw_item_subcontracting' , filters = {'reference_id': i.reference_id })
				for j in in_raw :
					se.append(
						"items",
						{
							"item_code": j.raw_item_code,
							"qty":  j.quantity,
							"s_warehouse": j.source_warehouse,
						},)
					
				if in_raw :
					se.append(
						"items",
						{
							"item_code": i.in_item_code,
							"qty": i.quantity,
							"t_warehouse": i.target_warehouse,
							"is_finished_item": True
						},)
				se.custom_subcontracting = self.name
				if se.items:		
					se.insert()
					se.save()
					se.submit()

	@frappe.whitelist()
	def update_out_entry(self):
		for i in self.get('bifurcation_out_subcontracting'):
			doc = frappe.get_doc('Items Subcontracting',i.reference_id)
			production_done_quantity = doc.production_done_quantity
			updated_value = getVal(production_done_quantity) + getVal(i.production_quantity)
			doc.production_done_quantity = updated_value
			if doc.production_done_quantity == doc.production_quantity:
				doc.out_done = True
			doc.save()
	
	@frappe.whitelist()
	def cancel_update_out_entry(self):
		for i in self.get('bifurcation_out_subcontracting'):
			doc = frappe.get_doc('Items Subcontracting',i.reference_id)
			production_done_quantity = doc.production_done_quantity
			updated_value = getVal(production_done_quantity) - getVal(i.production_quantity)
			doc.production_done_quantity = updated_value
			if doc.production_done_quantity == doc.production_quantity:
				doc.out_done = True
			else:
				doc.out_done = False
			doc.save()

	