 
  # Copyright (c) 2023, Quantbit Technologies Pvt ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form

def getVal(val):
        return val if val is not None else 0

class OutsourcingJobWork(Document):
	
	def get_available_quantity(self,item_code, warehouse):
		result = frappe.get_value("Bin",{"item_code": item_code,"warehouse": warehouse}, "actual_qty")
		return result if result else 0
	
	@frappe.whitelist()
	def set_available_qty(self ,table_name ,item_code , warehouse ,field_name):
		for tn in self.get(table_name):
			setattr(tn, field_name, self.get_available_quantity(tn.get(item_code), tn.get(warehouse)))


	@frappe.whitelist()
	def set_rate_from_order(self):
		item_code = self.finished_item_code or self.loan_material_item_code
		if self.select_link and item_code:
			parent = self.linking_option
			table= 'Blanket Order Item' if parent == 'Blanket Order' else 'Purchase Order Item'
			self.rate_from_order = frappe.get_value(table, {"parent":self.select_link ,'item_code': item_code}, 'rate')

	@frappe.whitelist()
	def set_filters_for_items(self):
		parent = self.linking_option
		table= 'Blanket Order Item' if parent == 'Blanket Order' else 'Purchase Order Item'
		moc = frappe.get_all(table, filters = {"parent":self.select_link }, fields =['item_code'])
		final_listed =[]
		for d in moc:
			final_listed.append(d.item_code)
		return final_listed
		

	def on_refresh_stockqty_update(self ,table , item ,warehouse ,available):
		table_data = self.get(str(table))
		item_field = str(item)
		warehouse_field =str(warehouse)
		available_field = str(available)
		for d in table_data:
			if d.get(item_field) and d.get(warehouse_field):
				d[available_field] = self.get_available_quantity(d.get(item_field), d.get(warehouse_field))
				# frappe.msgprint(str(r))


	def before_save(self):
		self.validate_ojwd()
		self.finish_total_quentity_calculate()
		self.validate_rejected_items_reasons()
		self.getting_weight()
		# self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
		# self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
	@frappe.whitelist()
	def getting_weight(self):
		# frappe.msgprint("hiii")
		if (self.finished_item_code or self.loan_material_item_code):
			item_code = self.finished_item_code or self.loan_material_item_code
			weight_per_unit = self.item_weight_per_unit(item_code)
			self.weight_per_unit = weight_per_unit
			if self.production_quantity:
				self.total_finished_weight =  weight_per_unit * self.production_quantity
   

	def before_submit(self):
		if self.in_or_out == "OUT":
			self.stock_transfer_stock_entry()
			self.production_done_quantity = 0
			self.process_status = "In Process"	

		elif self.in_or_out == "IN":
			self.manifacturing_stock_entry()
			self.stock_transfer_stock_entry_rejections()
			
   			#Below program for as it is entry
			self.stock_transfer_for_as_it_is()
		

		self.update_finished_item()
			

	def before_cancel(self):
		self.cancel_update_finished_item()

	@frappe.whitelist()
	def in_outsouring_data(self):
		# frappe.msgprint("Hi.......!")s
		for d in self.get("outsourcing_job_work"):
			OW = frappe.get_all('Outsourcing Job Work',
				  								filters = {'name':d.outsourcing_job_work},
												fields = ['loan_material_item_code','loan_material_item_name','finished_item_code','finished_item_name','production_quantity','production_done_quantity','target_warehouse','weight_per_unit','total_finished_weight','rate_from_order'])
			
			for j in OW:
				quantity = j.production_quantity - j.production_done_quantity
				item_code = j.finished_item_code  if self.entry_type == 'Outsourcing Job Work' else j.loan_material_item_code
				item_name = j.finished_item_name if self.entry_type == 'Outsourcing Job Work' else j.loan_material_item_name
				self.append("finished_item_outsource_job_work_details",{
							'item_code': item_code,
							'item_name': item_name,
							'source_warehouse': j.target_warehouse ,
							'target_warehouse': self.target_warehouse,
							'actual_required_quantity': quantity,
							'quantity': quantity,
							'available_quantity' :self.get_available_quantity(item_code ,j.target_warehouse ),
							'weight_per_unit':j.weight_per_unit,
							'total_finished_weight': j.weight_per_unit * quantity,
							'reference_id': d.outsourcing_job_work,
							'is_finished_item': True,
							'cr_casting_rejection':0,
							'mr_machine_rejection':0,
							'rw_rework':0,
							'as_it_is':0,
							'rate_from_order': j.rate_from_order
						},),

		self.if_in_fill_ojwd()

	@frappe.whitelist()
	def if_in_fill_ojwd(self):
		if self.in_or_out == "IN":
			outsource_job_work_details = self.get("outsource_job_work_details")
			outsource_job_work_details.clear()
			f_i_ojwd = self.get("finished_item_outsource_job_work_details")
			for f in f_i_ojwd:
				if f.quantity:
					if f.quantity > f.actual_required_quantity:
						frappe.throw('You Can Not Select Quantity Greater Than Actual Required Quantity')
					if 	self.entry_type == 'Outsourcing Job Work':
						doc = frappe.get_all("Outsourcing BOM Details",
									filters = {'parent':f.item_code},
									fields = ['item_code','item_name','required_quantity','weight_per_unit'])
					
						for d in doc:
							quantity =d.required_quantity * f.quantity
							warehouse=self.source_warehouse if self.source_warehouse else f.source_warehouse,
							rate=self.get_item_rate(d.item_code,warehouse)
							tax_template=self.get_tax_temp_for_items(d.item_code)
							self.append("outsource_job_work_details",{
										'item_code': d.item_code ,
										'item_name': d.item_name,
										'source_warehouse': self.source_warehouse if self.source_warehouse else f.source_warehouse,
										'target_warehouse': self.target_warehouse ,
										'quantity': quantity,
										'actual_required_quantity':quantity,
										'weight_per_unit': d.weight_per_unit ,
										'total_required_weight': d.weight_per_unit * quantity,
										'reference_id': f.reference_id,
										'rate':rate,
										'tax_template':tax_template,
										'total_amount':round(rate*quantity,2) if rate and quantity else 0
									},),

					else:
						# doc = [{
						# 	'item_code':f.item_code,
						# 	'item_name':frappe.get_value("Item",f.item_code,"item_name"),
						# 	'required_quantity':1,
						# 	'weight_per_unit': self.item_weight_per_unit(self.loan_material_item_code),}]
						
						doc = frappe.get_all('Outsource Job Work Details',filters = {'Parent': f.reference_id} ,fields =['item_code','item_name'])
			
						for d in doc:
							weight = self.item_weight_per_unit(d.item_code)
							quantity = f.quantity
							warehouse=self.source_warehouse if self.source_warehouse else f.source_warehouse,
							rate=self.get_item_rate(d.item_code,warehouse)
							tax_template=self.get_tax_temp_for_items(d.item_code)
							self.append("outsource_job_work_details",{
										'item_code': d.item_code,
										'item_name': d.item_name,
										'source_warehouse': self.source_warehouse if self.source_warehouse else f.source_warehouse,
										'target_warehouse': self.target_warehouse ,
										'quantity': quantity,
										'actual_required_quantity':quantity,
										'weight_per_unit': weight ,
										'total_required_weight': weight * quantity,
										'reference_id': f.reference_id,
										'rate':rate,
										'tax_template':tax_template,
										'total_amount':round(rate*quantity,2) if rate and quantity else 0
									},),
					



					self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
					self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
					self.get("taxes_and_charges").clear()
					self.get_in_out_tax_template()
					self.get_tax_amount()
			self.finish_total_quentity_calculate()
					

	@frappe.whitelist()
	def update_finished_item(self):
		f_i_ojwd = self.get("finished_item_outsource_job_work_details")
		for g in f_i_ojwd:
			production_done_quantity = frappe.get_value("Outsourcing Job Work", g.reference_id ,"production_done_quantity")
			production_quantity = frappe.get_value("Outsourcing Job Work", g.reference_id ,"production_quantity")
			updated_value = production_done_quantity + g.total_quantity

			frappe.set_value("Outsourcing Job Work",g.reference_id,"production_done_quantity",updated_value)

			if updated_value == production_quantity:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'Done')
			elif updated_value== 0:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'In Process')
			else:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'Partially Done')

	@frappe.whitelist()
	def cancel_update_finished_item(self):
		f_i_ojwd = self.get("finished_item_outsource_job_work_details")
		for g in f_i_ojwd:
			production_done_quantity = frappe.get_value("Outsourcing Job Work", g.reference_id ,"production_done_quantity")
			production_quantity = frappe.get_value("Outsourcing Job Work", g.reference_id ,"production_quantity")
			updated_value = float(production_done_quantity) - float(g.total_quantity)

			frappe.set_value("Outsourcing Job Work",g.reference_id,"production_done_quantity",updated_value)

			if updated_value == production_quantity:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'Done')
			elif updated_value == 0:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'In Process')
			else:
				frappe.set_value("Outsourcing Job Work",g.reference_id,"process_status",'Partially Done')
		


	@frappe.whitelist()
	def set_source_warehouse(self):
		for i in self.get("outsource_job_work_details"):
			if self.source_warehouse:
				i.source_warehouse = self.source_warehouse
				rate=self.get_item_rate(i.item_code, self.source_warehouse)
				i.rate=rate if rate else 0
				i.total_amount=round(rate*i.quantity,2) if rate and i.quantity else 0
				if i.item_code:
					i.available_quantity =self.get_available_quantity(i.item_code,i.source_warehouse)

		self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
		self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
		self.get("taxes_and_charges").clear()
		self.get_in_out_tax_template()
		self.get_tax_amount()
		for j in self.get("finished_item_outsource_job_work_details"):
			if self.source_warehouse:
				j.source_warehouse = self.source_warehouse

			if j.item_code:
					j.available_quantity =self.get_available_quantity(j.item_code,j.source_warehouse)


	@frappe.whitelist()
	def set_target_warehouse(self):
		for i in self.get("outsource_job_work_details"):
			if self.target_warehouse:
				i.target_warehouse = self.target_warehouse

		for j in self.get("finished_item_outsource_job_work_details"):
			if self.target_warehouse:
				j.target_warehouse = self.target_warehouse

	
	@frappe.whitelist()
	def set_warehouse_after_item(self):
		for i in self.get("outsource_job_work_details"):
			if not i.source_warehouse:
				i.source_warehouse = self.source_warehouse
				i.rate=self.get_item_rate(i.item_code, self.source_warehouse)
				i.total_amount=round(i.rate*i.quantity,2) if i.rate and i.quantity else 0

			if not i.target_warehouse:
				i.target_warehouse = self.target_warehouse
		self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
		self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
		self.get("taxes_and_charges").clear()
		self.get_in_out_tax_template()
		self.get_tax_amount()


	@frappe.whitelist()
	def validate_is_finish(self):
		for l in self.get("outsourcing_job_work"):
			doc = self.get('outsource_job_work_details' , filters={'is_finished_item':True ,})
			if len(doc) == 0:
				frappe.throw('There must be atleast 1 Finished Good in this Stock Entry')  
			elif len(doc) != 1:
				frappe.throw('Multiple items cannot be marked as finished item')



	@frappe.whitelist()
	def calculating_total(self,child_table ,total_field):
		casting_details = self.get(child_table)
		total_pouring_weight = 0
		for i in casting_details:
			field_data = getVal(i.get(total_field))
			total_pouring_weight = total_pouring_weight + field_data
		return total_pouring_weight
			


	@frappe.whitelist()
	def set_data_in_ojwd (self):
		if (self.finished_item_code or self.loan_material_item_code) and self.production_quantity:
			if 	self.entry_type == 'Outsourcing Job Work':
				doc = frappe.get_all("Outsourcing BOM Details",
										filters = {'parent':self.finished_item_code},
										fields = ['item_code','item_name','required_quantity','weight_per_unit',])
				
				for d in doc:
					quantity = d.required_quantity * self.production_quantity
					rate=self.get_item_rate(d.item_code, self.source_warehouse)
					tax_template=self.get_tax_temp_for_items(d.item_code)
					self.append("outsource_job_work_details",{
								'item_code': d.item_code ,
								'item_name': d.item_name,
								'available_quantity': self.get_available_quantity(d.item_code, self.source_warehouse),
								'source_warehouse': self.source_warehouse ,
								'target_warehouse': self.target_warehouse,
								'weight_per_unit':d.weight_per_unit,
								'total_required_weight': d.weight_per_unit * quantity,
								'quantity': quantity,
								'actual_required_quantity':quantity,
								'rate':rate,
								'tax_template':tax_template,
								'total_amount':round(rate*quantity,2) if rate and quantity else 0
							},),



			elif self.entry_type == 'Outsourcing Job Work W/O BOM':
				item_code = frappe.get_value('Item', self.loan_material_item_code , 'raw_material')
				if not item_code:
					frappe.throw(f"Please Set Raw Item In Item Master For Item {self.loan_material_item_code}")
				doc = [{
					'item_code':item_code,
					'item_name':frappe.get_value('Item', item_code , 'item_name'),
					'required_quantity':1,
					'weight_per_unit': self.item_weight_per_unit(item_code),}]
				
			
				for d in doc:
					quantity = d.get('required_quantity') * self.production_quantity
					rate=self.get_item_rate(d.get('item_code'), self.source_warehouse)
					tax_template=self.get_tax_temp_for_items(d.get('item_code'))
					self.append("outsource_job_work_details",{
								'item_code': d.get('item_code') ,
								'item_name': d.get('item_name'),
								'available_quantity': self.get_available_quantity(d.get('item_code'), self.source_warehouse),
								'source_warehouse': self.source_warehouse ,
								'target_warehouse': self.target_warehouse,
								'weight_per_unit':d.get('weight_per_unit'),
								'total_required_weight': d.get('weight_per_unit') * quantity,
								'quantity': quantity,
								'actual_required_quantity':quantity,
								'rate':rate,
								'tax_template':tax_template,
								'total_amount':round(rate*quantity,2) if rate and quantity else 0
							},),
			
			else :
				doc = [{
					'item_code':self.loan_material_item_code,
					'item_name':self.loan_material_item_name,
					'required_quantity':1,
					'weight_per_unit': self.item_weight_per_unit(self.loan_material_item_code),}]
				
			
				for d in doc:
					quantity = d.get('required_quantity') * self.production_quantity
					rate=self.get_item_rate(d.get('item_code'), self.source_warehouse)
					tax_template=self.get_tax_temp_for_items(d.get('item_code'))
					self.append("outsource_job_work_details",{
								'item_code': d.get('item_code') ,
								'item_name': d.get('item_name'),
								'available_quantity': self.get_available_quantity(d.get('item_code'), self.source_warehouse),
								'source_warehouse': self.source_warehouse ,
								'target_warehouse': self.target_warehouse,
								'weight_per_unit':d.get('weight_per_unit'),
								'total_required_weight': d.get('weight_per_unit') * quantity,
								'quantity': quantity,
								'actual_required_quantity':quantity,
								'rate':rate,
								'tax_template':tax_template,
								'total_amount':round(rate*quantity,2) if rate and quantity else 0
							},),
			
			self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
			self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
			self.get("taxes_and_charges").clear()
			self.get_in_out_tax_template()
			self.get_tax_amount()
	
	@frappe.whitelist()
	def validate_ojwd(self):
		if self.in_or_out == 'OUT' and self.entry_type == 'Outsourcing Job Work':
			poc = (self.get('outsource_job_work_details'))

			moc = frappe.get_all("Outsourcing BOM Details",
										filters = {'parent':self.finished_item_code},
										fields = ['item_code','item_name','required_quantity',])
			if len(moc) != len(poc) :
				frappe.throw("You can not add or remove rows in table 'Outsource Job Work Details'")

			for p in poc:
				count = 0
				for m in moc:
					if p.item_code == m.item_code:
						count = count + 1

				if count == 0:
					frappe.throw(f"Item Code is not matches with Item code from 'Outsourcing BOM'")

			poc_target_warehouse = set(p.target_warehouse for p in poc)
			if len(poc_target_warehouse) != 1:
				frappe.throw('The "Target Warehose" should be same for all item')
			else:
				self.target_warehouse = list(poc_target_warehouse)[0] 

		elif self.in_or_out == 'IN':
			for m in self.get("outsourcing_job_work"):
				for n in self.get("finished_item_outsource_job_work_details" , filters= {"reference_id" : m.outsourcing_job_work}):
					if not n.quantity:
						continue
					shit = self.get("outsource_job_work_details" , filters= {"reference_id" : m.outsourcing_job_work})
					poc_source_warehouse = set(b.target_warehouse for b in shit)
					if len(poc_source_warehouse) != 1:
						frappe.throw('The "Source Warehose" should be same for all item')



	@frappe.whitelist()
	def finish_total_quentity_calculate(self):
		for j in self.get("finished_item_outsource_job_work_details"):
			j.total_quantity = getVal(j.quantity) + getVal(j.cr_casting_rejection) + getVal(j.mr_machine_rejection) + getVal(j.rw_rework) + getVal(j.as_it_is)
			j.total_finished_weight = getVal(j.weight_per_unit) * getVal(j.quantity)
	
			if j.total_quantity > j.actual_required_quantity:
				frappe.throw(f'Total Quantity For Item {j.item_code}-{j.item_name} is Should Not Be Greater Than Actual Required Quantity ')


	@frappe.whitelist()
	def set_dat_in_rejected_items_reasons(self):
		for n in self.get("finished_item_outsource_job_work_details"):
			if 	self.entry_type == 'Outsourcing Job Work':
				doc = frappe.get_all("Outsourcing BOM Details",
										filters = {'parent':n.item_code},
										fields = ['item_code','item_name','required_quantity','weight_per_unit',])
				

			elif self.entry_type == 'Outsourcing Job Work W/O BOM':
				item_code = frappe.get_value('Item', n.item_code , 'raw_material')
				if not item_code:
					frappe.throw(f"Please Set Raw Item In Item Master For Item {n.item_code}")
				doc = [{
					'item_code':item_code,
					'item_name':frappe.get_value('Item', item_code , 'item_name'),
					'required_quantity':1,
					'weight_per_unit': self.item_weight_per_unit(item_code),}]
				
			
			else :
				doc = [{
					'item_code':n.item_code,
					'item_name':frappe.get_value("Item",n.item_code,'item_name'),
					'required_quantity':1,
					'weight_per_unit': self.item_weight_per_unit(n.item_code),}]

		
			for x in doc:
				per_unit_finish =  x.get('required_quantity')
				if n.cr_casting_rejection:
					cr_qty = n.cr_casting_rejection * per_unit_finish
					self.append("rejected_items_reasons",{
								'item_code':  x.get('item_code'),
								'item_name':x.get('item_name'),
								'reference_id': n.get('reference_id'),
								'rejection_type': "CR (Casting Rejection)",
								'quantity': cr_qty,
								'weight_per_unit': n.weight_per_unit,
								'total_rejected_weight': n.weight_per_unit * cr_qty,
								'target_warehouse':'',
							},),
				if n.mr_machine_rejection:
					mr_qty = n.mr_machine_rejection * per_unit_finish
					self.append("rejected_items_reasons",{
								'item_code':  x.get('item_code'),
								'item_name':x.get('item_name'),
								'reference_id': n.get('reference_id'),
								'rejection_type': "MR (Machine Rejection)",
								'quantity': mr_qty,
								'weight_per_unit': n.weight_per_unit,
								'total_rejected_weight': n.weight_per_unit * mr_qty,
								'target_warehouse':'',
							},),
				if n.rw_rework:
					rw_qty = n.rw_rework * per_unit_finish
					self.append("rejected_items_reasons",{
								'item_code': x.get('item_code'),
								'item_name':x.get('item_name'),
								'reference_id': n.get('reference_id'),
								'rejection_type': "RW (Rework)",
								'quantity': rw_qty,
								'weight_per_unit': n.weight_per_unit,
								'total_rejected_weight': n.weight_per_unit * rw_qty,
								'target_warehouse':'',
							},),
		# for p in self.get("finished_item_outsource_job_work_details"):
		# 	for x in self.get("outsource_job_work_details" , filters = {'reference_id' : p.reference_id }):
		# 		per_unit_finish = (x.quantity / p.quantity )
		# 		if p.cr_casting_rejection:
		# 			cr_qty = p.cr_casting_rejection * per_unit_finish
		# 			self.append("rejected_items_reasons",{
		# 						'item_code': x.item_code,
		# 						'item_name': x.item_name,
		# 						'reference_id': x.reference_id,
		# 						'rejection_type': "CR (Casting Rejection)",
		# 						'quantity': cr_qty,
		# 						'weight_per_unit': p.weight_per_unit,
		# 						'total_rejected_weight': p.weight_per_unit * cr_qty,
		# 						'target_warehouse':'',
		# 					},),
		# 		if p.mr_machine_rejection:
		# 			mr_qty = p.mr_machine_rejection * per_unit_finish
		# 			self.append("rejected_items_reasons",{
		# 						'item_code': x.item_code,
		# 						'item_name': x.item_name,
		# 						'reference_id': x.reference_id,
		# 						'rejection_type': "MR (Machine Rejection)",
		# 						'quantity': mr_qty,
		# 						'weight_per_unit': p.weight_per_unit,
		# 						'total_rejected_weight': p.weight_per_unit * mr_qty,
		# 						'target_warehouse':'',
		# 					},),
		# 		if p.rw_rework:
		# 			rw_qty = p.rw_rework * per_unit_finish
		# 			self.append("rejected_items_reasons",{
		# 						'item_code': x.item_code,
		# 						'item_name': x.item_name,
		# 						'reference_id': x.reference_id,
		# 						'rejection_type': "RW (Rework)",
		# 						'quantity': rw_qty,
		# 						'weight_per_unit': p.weight_per_unit,
		# 						'total_rejected_weight': p.weight_per_unit * rw_qty,
		# 						'target_warehouse':'',
		# 					},),


	@frappe.whitelist()
	def validate_rejected_items_reasons(self):
		for m in self.get("finished_item_outsource_job_work_details"):
			total_cr , total_mr , total_rw = 0 ,0 ,0 
			for x in self.get("outsource_job_work_details" , filters = {'reference_id' : m.reference_id }):
				per_unit_finish = (x.quantity / m.quantity )
				cr_qty = m.cr_casting_rejection * per_unit_finish
				mr_qty = m.mr_machine_rejection * per_unit_finish
				rw_qty = m.rw_rework * per_unit_finish

				if m.cr_casting_rejection:
					for p in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'CR (Casting Rejection)',} ):
						total_cr = total_cr + p.quantity
					if total_cr != cr_qty:
						frappe.throw('Invalid Rejection')

				if m.mr_machine_rejection:
					for q in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'MR (Machine Rejection)',} ):
						total_mr = total_mr + q.quantity
					if total_mr != mr_qty:
						frappe.throw('Invalid Rejection')

				if m.rw_rework:
					for r in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'RW (Rework)',} ):
						total_rw = total_rw + r.quantity
					if total_rw != rw_qty:
						frappe.throw('Invalid Rejection')

	@frappe.whitelist()
	def item_weight_per_unit(self , item_code ):
		item_uom = frappe.get_value("Item",item_code,"stock_uom")
		if item_uom == 'Kg':
			item_weight = frappe.get_value("Item",item_code,"weight")
		else:
			production_uom_definition = frappe.get_all("Production UOM Definition",
																				filters = {"parent":item_code,"uom": 'Kg'},
																				fields = ["value_per_unit"])
			if production_uom_definition:
				for k in production_uom_definition:
					item_weight= k.value_per_unit
			else:
				item_weight = 0
		if item_weight:
			return  item_weight
		else:
			return 0



	@frappe.whitelist()
	def stock_transfer_stock_entry(self):
		if self.in_or_out == "OUT":
			count = 0
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Transfer"
			se.company = self.company
			se.posting_date = self.posting_date
			for d in self.get('outsource_job_work_details' ,filters= {"is_supply_by_supplier" : False }):
				count = count + 1
				se.append(
							"items",
							{
								"item_code": d.item_code,
								"qty": d.quantity,
								"s_warehouse": d.source_warehouse,
								"t_warehouse": d.target_warehouse,
							},)

						
			se.custom_outsourcing_job_work = self.name	
			if count !=0:
				se.insert()
				se.save()
				se.submit()	

	@frappe.whitelist()
	def manifacturing_stock_entry(self):
		if self.in_or_out == 'IN':
			# if self.entry_type == 'Outsourcing Job Work':
				for cd in self.get("outsourcing_job_work"):      
					se = frappe.new_doc("Stock Entry")
					se.stock_entry_type = "Manufacture"
					se.company = self.company
					se.posting_date = self.posting_date
					
					all_core = self.get("finished_item_outsource_job_work_details" ,  filters={"reference_id": cd.outsourcing_job_work ,'quantity':['!=', 0]})
					for core in all_core:
						if core.is_finished_item:
							se.append(
								"items",
								{
									"item_code": core.item_code,
									"qty": core.quantity,
									"t_warehouse": core.target_warehouse,
									"is_finished_item": True
								},)
							if core.rate_from_order:
								qty =0
								qty = core.quantity + core.cr_casting_rejection
								if core.update_mr_qty_value:
									qty = qty + core.mr_machine_rejection
								se.append(
									"additional_costs",
									{
										"expense_account":'Expenses Included in Valuation - PEPL',
										"description": 'Reference from Orders',
										"amount": qty * core.rate_from_order ,

									},)
					details = self.get("outsource_job_work_details" ,  filters={"reference_id": cd.outsourcing_job_work ,})
					for shena in details:
						se.append(
								"items",
								{
									"item_code": shena.item_code,
									"qty":  shena.quantity,
									"s_warehouse": shena.source_warehouse,
								},)
						

					se.custom_outsourcing_job_work = self.name	
					if all_core:
						se.insert()
						se.save()
						se.submit()
			# else:
			# 	count = 0
			# 	se = frappe.new_doc("Stock Entry")
			# 	se.stock_entry_type = "Material Transfer"
			# 	se.company = self.company
			# 	se.posting_date = self.posting_date
			# 	for d in self.get('outsource_job_work_details' ,filters= {"is_supply_by_supplier" : False }):
			# 		count = count + 1
			# 		se.append(
			# 					"items",
			# 					{
			# 						"item_code": d.item_code,
			# 						"qty": d.quantity,
			# 						"s_warehouse": d.source_warehouse,
			# 						"t_warehouse": d.target_warehouse,
			# 					},)

							
			# 	se.custom_outsourcing_job_work = self.name	
			# 	if count !=0:
			# 		se.insert()
			# 		se.save()
			# 		se.submit()	





	@frappe.whitelist()
	def stock_transfer_stock_entry_rejections(self):
		if self.in_or_out == "IN":
			count = 0
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Transfer"
			se.company = self.company
			se.posting_date = self.posting_date
			for d in self.get('finished_item_outsource_job_work_details'):
				if d.cr_casting_rejection or d.mr_machine_rejection or d.rw_rework:
					for k in self.get('rejected_items_reasons' ,filters= {"reference_id" : d.reference_id }):
						count = count + 1
						se.append(
										"items",
										{
											"item_code": k.item_code,
											"qty": k.quantity,
											"s_warehouse": d.source_warehouse,
											"t_warehouse": k.target_warehouse,
										},)

						
			se.custom_outsourcing_job_work = self.name	
			if count !=0:
				se.insert()
				se.save()
				se.submit()



	
#*********************************************************************************** Program written for outsource_as_it_is_item Table ***************************
	#To create stock transfer entry
	def stock_transfer_for_as_it_is(self):
		if self.in_or_out == "IN":
			count = 0
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Transfer"
			se.company = self.company
			se.posting_date = self.posting_date
			for d in self.get('outsource_as_it_is_item'):
				count = count + 1
				se.append(
							"items",
							{
								"item_code": d.item_code,
								"qty": d.quantity,
								"s_warehouse": d.source_warehouse,
								"t_warehouse": d.target_warehouse,
							},)		
			se.custom_outsourcing_job_work = self.name	
			if count !=0:
				se.insert()
				se.save()
				se.submit()	
    
    
	#To set Targer warehouse for as it is 
	@frappe.whitelist()
	def set_target_warehouse_for_as_it_is(self):
		for i in self.get("outsource_as_it_is_item"):
			if self.target_warehouse_for_as_it_is_item:
				i.target_warehouse = self.target_warehouse_for_as_it_is_item


    #To append data into outsource_as_it_is_item table
	@frappe.whitelist()
	def get_as_it_is_item(self):
		# frappe.throw("hi......")
		outsource_as_it_is_item = self.get("outsource_as_it_is_item")
		outsource_as_it_is_item.clear()
		if self.in_or_out == "IN":
			f_i_ojwd = self.get("finished_item_outsource_job_work_details")
			for f in f_i_ojwd:
				if f.as_it_is:
					if f.as_it_is > f.actual_required_quantity:
						frappe.throw('You Can Not Select Quantity Greater Than Actual Required Quantity')
					if self.entry_type == 'Outsourcing Job Work':
						doc = frappe.get_all("Outsourcing BOM Details",
										filters = {'parent':f.item_code},
										fields = ['item_code','item_name','required_quantity','weight_per_unit'])
						for d in doc:
							quantity =d.required_quantity * f.as_it_is
							self.append("outsource_as_it_is_item",{
										'item_code': d.item_code ,
										'item_name': d.item_name,
										'source_warehouse': self.source_warehouse if self.source_warehouse else f.source_warehouse,
										'target_warehouse': self.target_warehouse ,
										'quantity': quantity,
										'actual_required_quantity':quantity,
										'weight_per_unit': d.weight_per_unit ,
										'total_required_weight': d.weight_per_unit * quantity,
										'reference_id': f.reference_id
									},),
					else :
						doc = frappe.get_all('Outsource Job Work Details',filters = {'Parent': f.reference_id} ,fields =['item_code','item_name'])
			
						for d in doc:
							quantity =f.as_it_is
							weight = self.item_weight_per_unit(d.item_code ) 
							self.append("outsource_as_it_is_item",{
										'item_code': d.item_code ,
										'item_name': d.item_name,
										'source_warehouse': self.source_warehouse if self.source_warehouse else f.source_warehouse,
										'target_warehouse': self.target_warehouse ,
										'quantity': quantity,
										'actual_required_quantity':quantity,
										'weight_per_unit': weight,
										'total_required_weight': weight * quantity,
										'reference_id': f.reference_id
									},),
		self.finish_total_quentity_calculate()
	
 
	#Program for get rate in Outsource Job Work Details child table 
	@frappe.whitelist()
	def get_item_rate(self,item_code=None,warehouse=None,item_index=None):
		if(self.in_or_out=="OUT"):
			count=0
			item=""
			source_warehouse=""
			if(item_index or item_index==0):
				count+=1
			if(count):
				item=str(self.get("outsource_job_work_details")[item_index].item_code)
				source_warehouse=str(self.get("outsource_job_work_details")[item_index].source_warehouse)
			else:
				item=item_code
				source_warehouse=warehouse
			item_rate=frappe.get_value("Bin",{"item_code":item,"warehouse":source_warehouse},'valuation_rate')
			if(item_rate):
				item_rate=round(item_rate,2)
				if(count==0):
					return item_rate
				else:
					self.get("outsource_job_work_details")[item_index].rate=round(item_rate,2)
					quantity=self.get("outsource_job_work_details")[item_index].quantity
					if(self.get("outsource_job_work_details")[item_index].rate):
						self.get("outsource_job_work_details")[item_index].total_amount=round(item_rate*quantity ,2)
					else:
						self.get("outsource_job_work_details")[item_index].total_amount=0
					self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
					self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
					self.get("taxes_and_charges").clear()
					self.get_in_out_tax_template()
					self.get_tax_amount()
   
	#To get Company Address and supplier address
	@frappe.whitelist()
 
	def get_company_address(self):
		company_name=frappe.get_value("Dynamic Link",{"link_doctype":"Company","link_name":self.company},"parent")
		self.company_address_name=company_name
		doc=frappe.get_doc("Address",company_name)
		self.company_gstin=doc.gstin
		self.place_of_supply_for_company=f"{doc.gst_state_number}-{doc.state}"
		temp_str = f"{doc.address_line1}\n" if doc.address_line1 else ""
		temp_str += f"{doc.address_line2}\n" if doc.address_line2 else ""
		temp_str += f"{doc.city}\n" if doc.city else ""
		temp_str += f"{doc.state} " if doc.state else ""
		temp_str += f"State Code:{doc.gst_state_number}\n" if doc.gst_state_number else ""
		temp_str += f"Pin Code:{doc.pincode}\n" if doc.pincode else ""
		temp_str += f"{doc.country}\n" if doc.country else ""
		temp_str += f"Phone:{doc.phone}\n" if doc.phone else ""
		temp_str += f"Email:{doc.email_id}\n" if doc.email_id else ""
		temp_str += f"GSTIN:{doc.gstin}\n" if doc.gstin else ""
		self.company_address=temp_str
  
  
	@frappe.whitelist()
	def get_supplier_address(self):
		supplier_name=frappe.get_value("Dynamic Link",{"link_doctype":"Supplier","link_name":self.supplier_id},"parent")
		if(supplier_name):
			self.supplier_address=supplier_name
			doc=frappe.get_doc("Address",supplier_name)
			self.billing_address_gstin=doc.gstin
			self.gst_category=doc.gst_category
			self.territory=doc.country
			self.place_of_supply=f"{doc.gst_state_number}-{doc.state}"
			temp_str = f"{doc.address_line1}\n" if doc.address_line1 else ""
			temp_str += f"{doc.address_line2}\n" if doc.address_line2 else ""
			temp_str += f"{doc.city}\n" if doc.city else ""
			temp_str += f"{doc.state} " if doc.state else ""
			temp_str += f"State Code:{doc.gst_state_number}\n" if doc.gst_state_number else ""
			temp_str += f"Pin Code:{doc.pincode}\n" if doc.pincode else ""
			temp_str += f"{doc.country}\n" if doc.country else ""
			temp_str += f"Phone:{doc.phone}\n" if doc.phone else ""
			temp_str += f"Email:{doc.email_id}\n" if doc.email_id else ""
			temp_str += f"GSTIN:{doc.gstin}\n" if doc.gstin else ""
			self.address=temp_str
   
   #To get tax Template to respective item in Outsource Job Work Details child table 
	@frappe.whitelist()
	def get_tax_temp_for_items(self,item_code):
		query = """SELECT item_tax_template FROM `tabItem Tax` WHERE parent=%s"""
		doc = frappe.db.sql(query, (item_code,), as_dict=True)
		if(doc):
			for d in doc:
				tepmlate_doc=frappe.get_value("Item Tax Template",{"name":d.item_tax_template,"company":self.company},"name")
				if(tepmlate_doc):
					return tepmlate_doc
	
 
	#To get in and out tax template for all items on parent doctype and append data to taxes_and_charges child table
	@frappe.whitelist()
	def get_in_out_tax_template(self):
		if(self.in_or_out=="OUT"):
			if(self.billing_address_gstin):
				if(self.place_of_supply and self.place_of_supply_for_company):
					count=0
					if(self.place_of_supply==self.place_of_supply_for_company):
						count+=1
					template_name=frappe.get_value("Sales Taxes and Charges Template",{"tax_category":"In-State" if(count) else "Out-State","company":self.company},"name")
					self.sales_taxes_and_charges_template=template_name
					template_child_table=frappe.get_all("Sales Taxes and Charges",{"parent":self.sales_taxes_and_charges_template},["charge_type","account_head","rate","tax_amount","total","description","cost_center"])
					for i in template_child_table:
						self.append("taxes_and_charges",{
							"charge_type":i.charge_type,
							"account_head":i.account_head,
							"rate":i.rate,
							"tax_amount":i.tax_amount,
							"total":i.total,
							"description":i.description,
							"cost_center":i.cost_center
						})
				else:
					if(self.place_of_supply):
						frappe.throw(f"Please add the address for Company {self.company}")
					else:
						frappe.throw(f"Please add the address for Supplier {self.supplier_id}")

	#To Calculate Total Tax Amount 
	@frappe.whitelist()
	def get_tax_amount(self):
		if(self.in_or_out=="OUT"):
			if(self.billing_address_gstin):
				for k in self.get("taxes_and_charges"):
					total_taxable_amt=0
					for i in self.get("outsource_job_work_details"):
						if(i.tax_template):
							tax_rate=frappe.get_value("Item Tax Template Detail",{"parent":i.tax_template,"tax_type":k.account_head},"tax_rate")
							if(tax_rate):
								tax_amt=tax_rate*i.total_amount/100
								total_taxable_amt=total_taxable_amt+tax_amt
					k.tax_amount=round(total_taxable_amt,2)
					check=0
					if(len(self.get("taxes_and_charges"))==2):
						check=1
						if(self.get("taxes_and_charges")[0].total==0 or self.get("taxes_and_charges")[0].total==None):
							k.total=round(total_taxable_amt,2)+self.total_amount
						else:
							k.total=round(total_taxable_amt,2)+self.get("taxes_and_charges")[0].total
					if(check==0):
						k.total=round(total_taxable_amt,2)+self.total_amount
				if(len(self.get("taxes_and_charges"))==2):
					self.total_taxes_and_charges=self.get("taxes_and_charges")[0].tax_amount+self.get("taxes_and_charges")[1].tax_amount
				else:	
					self.total_taxes_and_charges=self.get("taxes_and_charges")[0].tax_amount
				self.grand_total=self.total_taxes_and_charges+self.total_amount


	#To update amount when we chnage rate in child table as well parent table
	@frappe.whitelist()
	def update_item_amount(self,index=None):
		if(self.in_or_out=="OUT"):
			if(self.billing_address_gstin):
				if(index or index==0):
					self.get("outsource_job_work_details")[index].total_amount=self.get("outsource_job_work_details")[index].rate*self.get("outsource_job_work_details")[index].quantity
				self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
				self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
				self.get("taxes_and_charges").clear()
				self.get_in_out_tax_template()
				self.get_tax_amount()


#*********************************************************************************** Program end***************************************************
# ============================================================================================================================================================
