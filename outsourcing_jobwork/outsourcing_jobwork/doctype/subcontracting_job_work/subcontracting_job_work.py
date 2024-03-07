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

class SubcontractingJobWork(Document):
	@frappe.whitelist()
	def before_save(self):
		if self.in_or_out == 'OUT':
			pass
		else:
			self.finish_total_quantity_calculate()

	@frappe.whitelist()
	def before_submit(self):
		if self.in_or_out == 'OUT':
			if self.entry_type != 'Material Loan Given':
				self.stock_transfer_stock_entry('raw_outsourcing_job_work' , 'raw_item_code' , 'quantity' , 'source_warehouse' , self.target_warehouse )
			else:
				self.stock_transfer_stock_entry('loan_items_outsourcing_job_work' , 'finished_item_code' , 'production_quantity' , 'source_warehouse' , 'target_warehouse' ,1)

		else:
			if self.entry_type != 'Material Loan Given':
				self.stock_transfer_stock_entry('rejected_items_reasons' , 'raw_item_code' , 'quantity' , 'source_warehouse' , 'target_warehouse',1)
				self.manifacturing_stock_entry()
			else:
				self.stock_transfer_stock_entry('in_loan_items_outsourcing_job_work' , 'finished_item_code' , 'production_quantity' , 'source_warehouse' , 'target_warehouse',1)



# =================================================================================================== OUT ===================================================================================================

	@frappe.whitelist()
	def set_order_data(self):
		if self.entry_type == 'Outsourcing Job Work With Order' and self.linking_option and (self.blanket_order or self.purchase_order) :
			if self.linking_option == 'Blanket Order':
				b_o_l = []
				for i in self.blanket_order:
					b_o_l.append(str(i.blanket_order))

				doctype = 'Blanket Order Item'
				filters = {'parent':['in',b_o_l]}
				fields = ['item_code' , 'parent']

			else:
				p_o_l = []
				for j in self.purchase_order:
					p_o_l.append(str(j.purchase_order))

				doctype = 'Purchase Order Item'
				filters = {'parent':['in',p_o_l]}
				fields = ['item_code' , 'parent']

			doc = frappe.get_all(doctype , filters = filters , fields = fields)
			for d in doc:
				self.append("items_outsourcing_job_work",{
											'finished_item_code': d.item_code,
											'finished_item_name': ItemName(d.item_code),
											'reference_id': d.parent,},),

		self.set_raw_order_data('items_outsourcing_job_work')

	@frappe.whitelist()
	def set_raw_order_data(self , table ):
			items = self.get(table)
			for j in items:
				if j.finished_item_code:
					bom_exist = frappe.get_value("Outsourcing BOM",j.finished_item_code,'name')
					
					if bom_exist :
						bom = frappe.get_doc("Outsourcing BOM",j.finished_item_code)
						child_bom = bom.get("outsourcing_bom_details")

						for k in child_bom:
							self.append("raw_outsourcing_job_work",
										{	'finished_item_code': j.finished_item_code ,
											'raw_item_code'	: k.item_code,
											'raw_item_name':ItemName(k.item_code),
											'quantity_per_finished_item': k.required_quantity,
											'reference_id': j.reference_id,
											'source_warehouse': self.source_warehouse,},),
					else:
						raw_item_code = frappe.get_value("Item",j.finished_item_code,'raw_material')
						if raw_item_code:
							self.append("raw_outsourcing_job_work",
											{	'finished_item_code': j.finished_item_code ,
												'raw_item_code'	: raw_item_code ,
												'raw_item_name':ItemName(raw_item_code),
												'quantity_per_finished_item':1,
												'reference_id': j.reference_id,
												'source_warehouse': self.source_warehouse,},),
						else:
							frappe.msgprint(f"There is no 'Raw Material'defined at Item master of Item {j.finished_item_code}")



	@frappe.whitelist()
	def set_quantity_raw_order_data(self , table):
		finished_items = self.get(table)
		
		for f in finished_items:
			raw_items = self.get("raw_outsourcing_job_work" , filters = {'finished_item_code':f.finished_item_code , 'reference_id' : str(f.reference_id)})
			for r in raw_items:
				actual_required_quantity = getVal(f.production_quantity) * getVal(r.quantity_per_finished_item)
				r.actual_required_quantity = actual_required_quantity
				r.quantity = actual_required_quantity


	@frappe.whitelist()
	def set_warehouses_in_loan_table(self):
		self.set_table_data('loan_items_outsourcing_job_work' , 'source_warehouse', self.source_warehouse ,'finished_item_code','available_quantity' )
		self.set_table_data('loan_items_outsourcing_job_work' , 'target_warehouse', self.target_warehouse )

	

# =================================================================================================== Both ===================================================================================================
	@frappe.whitelist()
	def set_table_data(self , table , table_field , field_data ,item_field = None,available=None):
		items_table = self.get(table)
		for i in items_table:
			setattr(i, table_field, field_data)
			if item_field and available:
				setattr(i, available, get_available_quantity(item_field , field_data))

	@frappe.whitelist()
	def stock_transfer_stock_entry(self , table , item_code , quantity , source_warehouse , target_warehouse , T=None):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.company = self.company
		se.posting_date = self.posting_date
		for d in self.get(table ,filters= {"is_supply_by_supplier" : False}):
			se.append("items",
						{
							"item_code": d.get(item_code),
							"qty": d.get(quantity),
							"s_warehouse": d.get(source_warehouse),
							"t_warehouse": d.get(target_warehouse) if T else  target_warehouse ,
						},)
		se.custom_subcontracting_job_work = self.name	
		if se.items:
			se.insert()
			se.save()
			se.submit()	


# =================================================================================================== IN ===================================================================================================


	@frappe.whitelist()
	def set_in_finished_item_outsource_job_work(self):
		subcontracting_job_work = self.get("subcontracting_job_work")
		if subcontracting_job_work :
			sub_job_list = []
			for d in subcontracting_job_work :
				sub_job_list.append(d.subcontracting_job_work)

			if self.entry_type == 'Outsourcing Job Work With Order':
				doctype , filters, fields= 'Items Outsourcing Job Work' , {'parent':['in',sub_job_list]} , ['finished_item_code' , 'parent' ,'production_quantity','production_done_quantity','reference_id']
	
			elif self.entry_type == 'Outsourcing Job Work With BOM':
				doctype , filters, fields= 'Items Bom Outsourcing Job Work' , {'parent':['in',sub_job_list]} , ['finished_item_code' , 'parent' ,'production_quantity','production_done_quantity','reference_id']

			else:
				doctype , filters, fields= 'Loan Items Outsourcing Job Work' , {'parent':['in',sub_job_list]} , ['finished_item_code' , 'parent', 'production_quantity','production_done_quantity','target_warehouse']

			CHILD_SJW = frappe.get_all(doctype,filters = filters,fields = fields)
			
			for j in CHILD_SJW:
				in_able_quantity = j.production_quantity - j.production_done_quantity
				
				if doctype == 'Loan Items Outsourcing Job Work':
					self.append("in_loan_items_outsourcing_job_work",{
								'finished_item_code': j.finished_item_code,
								'finished_item_name': ItemName(j.finished_item_code),
								'source_warehouse': j.target_warehouse,
								'in_able_quantity': in_able_quantity,
								'target_warehouse': None,
								'reference_id': j.parent,
								'scj_parent':j.parent,
							},),
				else:
					self.append("in_finished_item_outsource_job_work",{
								'item_code': j.finished_item_code,
								'item_name': ItemName(j.finished_item_code),
								'source_warehouse': None,
								'in_able_quantity': in_able_quantity,
								'target_warehouse': None,
								'reference_id': j.reference_id,
								'scj_parent':j.parent,
							},),

			self.set_in_raw_item_outsourcing_job_work()

	@frappe.whitelist()
	def set_in_raw_item_outsourcing_job_work(self):
		in_finished =  self.get('in_finished_item_outsource_job_work')
		for i in in_finished :
			doctype , filters, fields= 'Raw Outsourcing Job Work' , {'parent':['in',i.scj_parent] ,'finished_item_code':i.item_code , 'reference_id': i.reference_id} , ['finished_item_code' ,'raw_item_code', 'parent','reference_id' ,'quantity_per_finished_item']
			CHILD_ROJW = frappe.get_all(doctype,filters = filters,fields = fields)
			for j in CHILD_ROJW :
				source_warehouse = frappe.get_value("Subcontracting Job Work", j.parent ,'target_warehouse')
				self.append("in_raw_item_outsourcing_job_work",{
							'finished_item_code': j.finished_item_code,
							'raw_item_code': j.raw_item_code,
							'raw_item_name': ItemName(j.raw_item_code),
							'source_warehouse': source_warehouse,
							'in_able_quantity': 0,
							'target_warehouse': None,
							'reference_id': j.reference_id,
							'scj_parent':j.parent ,
							'quantity_per_finished_item': j.quantity_per_finished_item ,
						},),
	

	@frappe.whitelist()
	def raw_material_qty(self):
		in_finished =  self.get('in_finished_item_outsource_job_work' , filters = {'quantity': ['!=',None]})
		for i in in_finished :
			in_raw = self.get('in_raw_item_outsourcing_job_work' , filters = {'reference_id': i.reference_id , 'scj_parent' : i.scj_parent})
			for j in in_raw :
				j.quantity =  getVal(j.quantity_per_finished_item) * getVal(i.quantity)

		self.finish_total_quantity_calculate()

	@frappe.whitelist()
	def rejected_item(self):
		in_finished =  self.get('in_finished_item_outsource_job_work' , filters = {'quantity': ['!=',None]})
		for i in in_finished :
			in_raw = self.get('in_raw_item_outsourcing_job_work' , filters = {'reference_id': i.reference_id , 'scj_parent' : i.scj_parent})
			for j in in_raw :
				as_it_is = getVal(j.quantity_per_finished_item) * getVal(i.as_it_is)
				cr_casting_rejection = getVal(j.quantity_per_finished_item) * getVal(i.cr_casting_rejection)
				mr_machine_rejection = getVal(j.quantity_per_finished_item) * getVal(i.mr_machine_rejection)
				rw_rework = getVal(j.quantity_per_finished_item) * getVal(i.rw_rework)
				if as_it_is:
					self.append("rejected_items_reasons",{
								'finished_item_code': i.item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': as_it_is,
								'rejection_type' :'AS IT IS (AS IT AS)' ,
								'source_warehouse': j.source_warehouse,
							},),
				if cr_casting_rejection:
					self.append("rejected_items_reasons",{
								'finished_item_code': i.item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': cr_casting_rejection,
								'rejection_type' :'CR (Casting Rejection)' ,
								'source_warehouse': j.source_warehouse,
							},),
				if mr_machine_rejection:
					self.append("rejected_items_reasons",{
								'finished_item_code': i.item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': mr_machine_rejection,
								'rejection_type' :'MR (Machine Rejection)' ,
								'source_warehouse': j.source_warehouse,
							},),
				if rw_rework:
					self.append("rejected_items_reasons",{
								'finished_item_code': i.item_code,
								'raw_item_code': j.raw_item_code,
								'raw_item_name': ItemName(j.raw_item_code),
								'quantity': rw_rework,
								'rejection_type' :'RW (Rework)' ,
								'source_warehouse': j.source_warehouse,
							},),
		
		if self.rejection_target_warehouse:
			self.set_table_data('rejected_items_reasons' , 'target_warehouse' , self.rejection_target_warehouse  )

	@frappe.whitelist()
	def finish_total_quantity_calculate(self):
		for j in self.get("in_finished_item_outsource_job_work"):
			j.total_quantity = getVal(j.quantity) + getVal(j.cr_casting_rejection) + getVal(j.mr_machine_rejection) + getVal(j.rw_rework) + getVal(j.as_it_is)
			if j.total_quantity > j.in_able_quantity:
				frappe.throw(f'Total Quantity For Item {j.item_code}-{j.item_name} is Should Not Be Greater Than "IN able Quantity"')


	@frappe.whitelist()
	def manifacturing_stock_entry(self):
		if self.in_or_out == 'IN':
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Manufacture"
			se.company = self.company
			se.posting_date = self.posting_date
			in_finished =  self.get('in_finished_item_outsource_job_work' , filters = {'quantity': ['not in',(None,0)]})
			for i in in_finished :
				in_raw = None
				in_raw = self.get('in_raw_item_outsourcing_job_work' , filters = {'reference_id': i.reference_id , 'scj_parent' : i.scj_parent})
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
							"item_code": i.item_code,
							"qty": i.quantity,
							"t_warehouse": i.target_warehouse,
							"is_finished_item": True
						},)
			se.custom_subcontracting_job_work = self.name
			if se.items:		
				se.insert()
				se.save()
				se.submit()

