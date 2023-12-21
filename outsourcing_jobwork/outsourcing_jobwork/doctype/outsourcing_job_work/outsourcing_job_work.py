# Copyright (c) 2023, Quantbit Technologies Pvt ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form

class OutsourcingJobWork(Document):
	def before_save(self):
		self.validate_ojwd()
		self.finish_total_quentity_calculate()
		self.validate_rejected_items_reasons()
		self.total_quantity = self.calculating_total('outsource_job_work_details','quantity')
		self.total_amount = self.calculating_total('outsource_job_work_details','total_amount')
		if self.finished_item_code and self.production_quantity:
			weight_per_unit = self.item_weight_per_unit(self.finished_item_code)
			self.weight_per_unit = weight_per_unit
			self.total_finished_weight =  weight_per_unit * self.production_quantity
   

	def before_submit(self):
		if self.in_or_out == "OUT":
			self.stock_transfer_stock_entry()
			
			if not self.process_status:
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
												fields = ['finished_item_code','finished_item_name','production_quantity','production_done_quantity','target_warehouse','weight_per_unit','total_finished_weight'])
			
			for j in OW:
				quantity = j.production_quantity - j.production_done_quantity
				self.append("finished_item_outsource_job_work_details",{
							'item_code': j.finished_item_code ,
							'item_name': j.finished_item_name,
							'source_warehouse': j.target_warehouse ,
							'target_warehouse': self.target_warehouse,
							'actual_required_quantity': quantity,
							'quantity': quantity,
							'weight_per_unit':j.weight_per_unit,
							'total_finished_weight': j.weight_per_unit * quantity,
							'reference_id': d.outsourcing_job_work,
							'is_finished_item': True,
							'cr_casting_rejection':0,
							'mr_machine_rejection':0,
							'rw_rework':0,
							'as_it_is':0
						},),

		self.if_in_fill_ojwd()

	@frappe.whitelist()
	def if_in_fill_ojwd(self):
		outsource_job_work_details = self.get("outsource_job_work_details")
		outsource_job_work_details.clear()
		if self.in_or_out == "IN":
			f_i_ojwd = self.get("finished_item_outsource_job_work_details")
			for f in f_i_ojwd:
				if f.quantity:
					if f.quantity > f.actual_required_quantity:
						frappe.throw('You Can Not Select Quantity Greater Than Actual Required Quantity')

					doc = frappe.get_all("Outsourcing BOM Details",
									filters = {'parent':f.item_code},
									fields = ['item_code','item_name','required_quantity','weight_per_unit'])
					for d in doc:
						quantity =d.required_quantity * f.quantity
						self.append("outsource_job_work_details",{
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

		for j in self.get("finished_item_outsource_job_work_details"):
			if self.source_warehouse:
				j.source_warehouse = self.source_warehouse


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

			if not i.target_warehouse:
				i.target_warehouse = self.target_warehouse



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
			field_data = i.get(total_field)
			total_pouring_weight = total_pouring_weight + field_data
		return total_pouring_weight
			


	@frappe.whitelist()
	def set_data_in_ojwd (self):
		if self.finished_item_code and self.production_quantity:
			doc = frappe.get_all("Outsourcing BOM Details",
									filters = {'parent':self.finished_item_code},
									fields = ['item_code','item_name','required_quantity','weight_per_unit',])
			for d in doc:
				quantity = d.required_quantity * self.production_quantity
				self.append("outsource_job_work_details",{
							'item_code': d.item_code ,
							'item_name': d.item_name,
							'source_warehouse': self.source_warehouse ,
							'target_warehouse': self.target_warehouse,
							'weight_per_unit':d.weight_per_unit,
							'total_required_weight': d.weight_per_unit * quantity,
							'quantity': quantity,
							'actual_required_quantity':quantity,
						},),
	
	@frappe.whitelist()
	def validate_ojwd(self):
		if self.in_or_out == 'OUT':
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
			j.total_quantity = j.quantity + j.cr_casting_rejection + j.mr_machine_rejection + j.rw_rework+j.as_it_is
			j.total_finished_weight = j.weight_per_unit * j.quantity
	
			if j.total_quantity > j.actual_required_quantity:
				frappe.throw(f'Total Quantity For Item {j.item_code}-{j.item_name} is Should Not Be Greater Than Actual Required Quantity ')


	@frappe.whitelist()
	def set_dat_in_rejected_items_reasons(self):
		for x in self.get("finished_item_outsource_job_work_details"):
			if x.cr_casting_rejection:
				self.append("rejected_items_reasons",{
							'item_code': x.item_code,
							'item_name': x.item_name,
							'reference_id': x.reference_id,
							'rejection_type': "CR (Casting Rejection)",
							'quantity': x.cr_casting_rejection,
							'weight_per_unit': x.weight_per_unit,
							'total_rejected_weight': x.weight_per_unit * x.cr_casting_rejection,
							'target_warehouse':'',
						},),
			if x.mr_machine_rejection:
				self.append("rejected_items_reasons",{
							'item_code': x.item_code,
							'item_name': x.item_name,
							'reference_id': x.reference_id,
							'rejection_type': "MR (Machine Rejection)",
							'quantity': x.mr_machine_rejection,
							'weight_per_unit': x.weight_per_unit,
							'total_rejected_weight': x.weight_per_unit * x.mr_machine_rejection,
							'target_warehouse':'',
						},),
			if x.rw_rework:
				self.append("rejected_items_reasons",{
							'item_code': x.item_code,
							'item_name': x.item_name,
							'reference_id': x.reference_id,
							'rejection_type': "RW (Rework)",
							'quantity': x.rw_rework,
							'weight_per_unit': x.weight_per_unit,
							'total_rejected_weight': x.weight_per_unit * x.rw_rework,
							'target_warehouse':'',
						},),


	@frappe.whitelist()
	def validate_rejected_items_reasons(self):
		for x in self.get("finished_item_outsource_job_work_details"):
			total_cr , total_mr , total_rw = 0 ,0 ,0 
			if x.cr_casting_rejection:
				for p in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'CR (Casting Rejection)',} ):
					total_cr = total_cr + p.quantity
				if total_cr != x.cr_casting_rejection:
					frappe.throw('Invalid Rejection')

			if x.mr_machine_rejection:
				for q in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'MR (Machine Rejection)',} ):
					total_mr = total_mr + q.quantity
				if total_mr != x.mr_machine_rejection:
					frappe.throw('Invalid Rejection')

			if x.rw_rework:
				for r in self.get("rejected_items_reasons" , filters= {"reference_id" : x.reference_id ,"item_code" : x.item_code , "rejection_type": 'RW (Rework)',} ):
					total_rw = total_rw + r.quantity
				if total_rw != x.rw_rework:
					frappe.throw('Invalid Rejection')

	@frappe.whitelist()
	def item_weight_per_unit(self , item_code ):
		item_uom = frappe.get_value("Item",item_code,"stock_uom")
		if item_uom == 'Kg':
			item_weight = frappe.get_all("Item",item_code,"weight")
		else:
			production_uom_definition = frappe.get_all("Production UOM Definition",
																				filters = {"parent":item_code,"uom": 'Kg'},
																				fields = ["value_per_unit"])
			if production_uom_definition:
				for k in production_uom_definition:
					item_weight= k.value_per_unit
			else:
				frappe.throw(f'Please Set "Production UOM Definition" For Item {get_link_to_form("Item",item_code)} of UOM "Kg" ')
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
					for k in self.get('rejected_items_reasons' ,filters= {"item_code" : d.item_code }):
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
		outsource_as_it_is_item = self.get("outsource_as_it_is_item")
		outsource_as_it_is_item.clear()
		if self.in_or_out == "IN":
			f_i_ojwd = self.get("finished_item_outsource_job_work_details")
			for f in f_i_ojwd:
				if f.as_it_is:
					if f.as_it_is > f.actual_required_quantity:
						frappe.throw('You Can Not Select Quantity Greater Than Actual Required Quantity')

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
		self.finish_total_quentity_calculate()
	


#*********************************************************************************** Program end***************************************************
# ============================================================================================================================================================
