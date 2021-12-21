# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2021-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import ValidationError

class JobCostSheet(models.Model):
    _name = 'job.cost.sheet'
    _description = "Job Cost Sheet"

    name = fields.Char("Sheet Number")
    cost_sheet_name = fields.Char(string = 'Name',required = False)
    project_id = fields.Many2one('project.project', string = 'Project')
    supplier_id = fields.Many2one('res.partner', string = 'Customer', required = True)
    close_date = fields.Datetime(string = 'Close Date', readonly = True)
    user_id = fields.Many2one('res.users', string = 'Created By',default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', oldname='currency', string="Currency")
    purchase_exempt = fields.Boolean(string = 'Purchase Exempt', copy=False)
    description = fields.Text(string = 'Extra Information')

    material_ids = fields.One2many('material.material','job_sheet_id', string = 'Materials')
    material_labour_ids = fields.One2many('material.labour','job_sheet_id', string = 'Labour')
    material_overhead_ids = fields.One2many('material.overhead','job_sheet_id', string = 'Service')
    material_vehicle_ids = fields.One2many('material.vehicle', 'job_sheet_id', string='Vehicle')
    material_equipment_ids = fields.One2many('material.equipment', 'job_sheet_id', string='Equipment')
    material_subcontract_ids = fields.One2many('material.subcontract', 'job_sheet_id', string='Subcontract')

    amount_material = fields.Monetary(string='Material Cost', readonly=True, compute = '_amount_material')
    amount_labour = fields.Monetary(string='Labour Cost', readonly=True, compute = '_amount_labour')
    amount_overhead = fields.Monetary(string='Service Cost', readonly=True, compute = '_amount_overhead')
    amount_vehicle = fields.Monetary(string='Vehicle Cost', readonly=True, compute = '_amount_vehicle')
    amount_equipment = fields.Monetary(string='Equipment Cost', readonly=True, compute = '_amount_equipment')
    amount_subcontract = fields.Monetary(string='SubContract Cost', readonly=True, compute = '_amount_subcontract')

    amount_total = fields.Monetary(string='Total Estimation Cost', readonly=True, compute = '_amount_total', store = True)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('purchase','Purchase Order'),('done','Done')],string = "State", readonly=True, default='draft')

    purchase_order_ids = fields.One2many('purchase.order','job_cost_sheet_id', string = 'Purchase Orders')
    purchase_order_count = fields.Integer(string = 'Purchases', compute = '_purchase_order_count')

    bulk_cost = fields.Float("Bulk Cost")

    @api.onchange('project_id')
    def onchange_project_id(self):
        for record in self:
            if record.project_id and record.project_id.partner_id:
                record.update({'supplier_id': record.project_id.partner_id.id})

    def action_view_purchase_order(self):
        return {
                'name': _('Purchase order'),
                'domain': [('id','in',[x.id for x in self.purchase_order_ids])],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'view_id': False,
                'views': [(self.env.ref('purchase.purchase_order_tree').id, 'tree'), (self.env.ref('purchase.purchase_order_form').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def _purchase_order_count(self):
        total = 0
        for order in self.purchase_order_ids:
            if order:
                total += 1
        self.purchase_order_count = total

    def create_purchase_order(self):
        if self.supplier_id:
            purchase_order_obj = self.env['purchase.order']
            purchase_order_line_obj = self.env['purchase.order.line']
            cost_sheet_dict = { 'partner_id' :  self.supplier_id.id, 'job_cost_sheet_id' : self.id }
            if cost_sheet_dict:
                new_purchase_order_id = purchase_order_obj.create(cost_sheet_dict)
            if self.material_ids:
                for material in self.material_ids:
                    if material.product_id:
                        material_material_dict = { 'order_id' : new_purchase_order_id.id,
                                                   'product_id' : material.product_id.id,
                                                   'price_unit' : material.price_unit,
                                                   'name' : material.product_id.description,
                                                   'date_planned' : datetime.today(),
                                                   'name' : material.product_id.name,
                                                   'product_qty' : material.product_qty,
                                                   'product_uom': material.product_id.uom_id.id }
                        purchase_order_line_obj.create(material_material_dict)
            if self.material_labour_ids:
                for labour in self.material_labour_ids:
                    if labour.product_id:
                        material_labour_dict = { 'order_id' : new_purchase_order_id.id,
                                                 'product_id' : labour.product_id.id,
                                                 'price_unit' : labour.price_unit,
                                                 'name' : labour.product_id.description,
                                                 'date_planned' : datetime.today(),
                                                 'name' : labour.product_id.name,
                                                 'product_qty' : labour.product_qty,
                                                 'product_uom': labour.product_id.uom_id.id }
                        purchase_order_line_obj.create(material_labour_dict)
            if self.material_overhead_ids:
                for overhead in self.material_overhead_ids:
                    if overhead.product_id:
                        material_overhead_dict = { 'order_id' : new_purchase_order_id.id,
                                                   'product_id' : overhead.product_id.id,
                                                   'price_unit' : overhead.price_unit,
                                                   'name' : overhead.product_id.description,
                                                   'date_planned' : datetime.today(),
                                                   'name' : overhead.product_id.name,
                                                   'product_qty' : overhead.product_qty,
                                                   'product_uom': overhead.product_id.uom_id.id }
                        purchase_order_line_obj.create(material_overhead_dict)
            self.update({ 'purchase_exempt' : True, 'state' : 'purchase' })

    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id

    def action_approved(self):
        if not self.material_ids and not self.material_labour_ids and not self.material_overhead_ids:
            raise ValidationError(_( "Add at least one material for estimation."))
        return self.write({'state': 'approved'})

    def action_done(self):
        return self.write({'state': 'done', 'close_date' : datetime.now()})

    @api.model
    def create(self,vals):
        sequence = self.env['ir.sequence'].sudo().get('job.cost.sheet') or ' '
        vals['name'] = sequence
        if vals.get('project_id'):
            project_rec = self.search([('project_id', '=', vals.get('project_id'))])
            if project_rec:
                raise ValidationError(_("Already created estimation cost for this project."))
        result = super(JobCostSheet, self).create(vals)

        return result

    @api.depends('material_ids.material_amount_total')
    def _amount_material(self):
        for sheet in self:
            amount_material = 0.0
            for line in sheet.material_ids:
                amount_material += line.material_amount_total
            sheet.update({'amount_material': round(amount_material)})

    @api.depends('material_labour_ids.labour_amount_total')
    def _amount_labour(self):
        for sheet in self:
            amount_labour = 0.0
            for line in sheet.material_labour_ids:
                amount_labour += line.labour_amount_total
            sheet.update({'amount_labour': round(amount_labour)})

    @api.depends('material_overhead_ids.overhead_amount_total')
    def _amount_overhead(self):
        for sheet in self:
            amount_overhead = 0.0
            for line in sheet.material_overhead_ids:
                amount_overhead += line.overhead_amount_total
            sheet.update({'amount_overhead': round(amount_overhead)})

    @api.depends('material_vehicle_ids.vehicle_amount_total')
    def _amount_vehicle(self):
        for sheet in self:
            amount_vehicle = 0.0
            for line in sheet.material_vehicle_ids:
                amount_vehicle += line.vehicle_amount_total
            sheet.update({'amount_vehicle': round(amount_vehicle)})

    @api.depends('material_equipment_ids.equipment_amount_total')
    def _amount_equipment(self):
        for sheet in self:
            amount_equipment = 0.0
            for line in sheet.material_equipment_ids:
                amount_equipment += line.equipment_amount_total
            sheet.update({'amount_equipment': round(amount_equipment)})

    @api.depends('material_subcontract_ids.subcontract_amount_total')
    def _amount_subcontract(self):
        for sheet in self:
            amount_subcontract = 0.0
            for line in sheet.material_subcontract_ids:
                amount_subcontract += line.subcontract_amount_total
            sheet.update({'amount_subcontract': round(amount_subcontract)})

    @api.depends('material_ids.material_amount_total','material_labour_ids.labour_amount_total','material_overhead_ids.overhead_amount_total','material_vehicle_ids.vehicle_amount_total','material_equipment_ids.equipment_amount_total', 'material_subcontract_ids.subcontract_amount_total', 'bulk_cost')
    def _amount_total(self):
        for cost_sheet in self:
            amount_material = 0.0
            amount_labour = 0.0
            amount_overhead = 0.0
            amount_overhead = 0.0
            amount_vehicle = 0.0
            amount_equipment = 0.0
            amount_subcontract = 0.0
            for line in cost_sheet.material_ids:
                amount_material += line.material_amount_total
            for line in cost_sheet.material_labour_ids:
                amount_labour += line.labour_amount_total
            for line in cost_sheet.material_overhead_ids:
                amount_overhead += line.overhead_amount_total
            for line in cost_sheet.material_vehicle_ids:
                amount_vehicle += line.vehicle_amount_total
            for line in cost_sheet.material_equipment_ids:
                amount_equipment += line.equipment_amount_total
            for line in cost_sheet.material_subcontract_ids:
                amount_subcontract += line.subcontract_amount_total
            cost_sheet.amount_total = (amount_material + amount_labour + amount_overhead + amount_equipment + amount_vehicle + amount_subcontract + cost_sheet.bulk_cost)

class MaterialMaterial(models.Model):
    _name = 'material.material'
    _description = "Material"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_qty = fields.Float(string='Quantity', default='1.00')
    price_unit = fields.Float(string='Unit Price', default='0.00')
    tax_id = fields.Many2one('account.tax', string="Taxes")
    material_amount_total = fields.Float(string = 'Subtotal', compute = 'compute_material_amount_total')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.update({'description': record.product_id.name, 'price_unit' : record.product_id.list_price})

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def compute_material_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.product_qty * line.price_unit) * line.tax_id.amount * 0.01
            line.update({'material_amount_total': (line.product_qty * line.price_unit) + tax})

class MaterialLabour(models.Model):
    _name = 'material.labour'
    _description = "Labour"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_qty = fields.Float(string='Quantity', default='1.00')
    price_unit = fields.Float(string='Unit Price', default='0.00')
    tax_id = fields.Many2one('account.tax', string="Taxes")
    labour_amount_total = fields.Float(string = 'Subtotal', compute = 'compute_labour_amount_total')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.update({'description': record.product_id.name, 'price_unit' : record.product_id.list_price})

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def compute_labour_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.product_qty * line.price_unit) * line.tax_id.amount * 0.01
            line.update({'labour_amount_total': (line.product_qty * line.price_unit) + tax})

class MaterialOverhead(models.Model):
    _name = 'material.overhead'
    _description = "Overhead"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_qty = fields.Float(string='Quantity', default='1.00')
    price_unit = fields.Float(string='Unit Price', default='0.00')
    tax_id = fields.Many2one('account.tax', string="Taxes")
    overhead_amount_total = fields.Float(string = 'Subtotal', compute = 'compute_overhead_amount_total')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.update({'description': record.product_id.name, 'price_unit' : record.product_id.list_price})

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def compute_overhead_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.product_qty * line.price_unit) * line.tax_id.amount * 0.01
            line.update({'overhead_amount_total': (line.product_qty * line.price_unit) + tax})

class MaterialVehicle(models.Model):
    _name = 'material.vehicle'
    _description = "Vehicle"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    product_id = fields.Many2one('product.product', string = 'Product')
    description = fields.Char(string = 'Description')
    product_qty = fields.Float(string = 'Quantity', default = '1.00')
    price_unit = fields.Float(string = 'Unit Price', default = '0.00')
    tax_id = fields.Many2one('account.tax', string="Taxes")
    vehicle_amount_total = fields.Float(string = 'Subtotal', compute = 'compute_vehicle_amount_total')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.update({'description': record.product_id.name, 'price_unit' : record.product_id.list_price})

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def compute_vehicle_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.product_qty * line.price_unit) * line.tax_id.amount * 0.01
            line.update({'vehicle_amount_total': (line.product_qty * line.price_unit) + tax})

class MaterialEquipment(models.Model):
    _name = 'material.equipment'
    _description = "Equipment"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    product_id = fields.Many2one('product.product', string = 'Product')
    description = fields.Char(string = 'Description')
    product_qty = fields.Float(string = 'Quantity', default = '1.00')
    price_unit = fields.Float(string = 'Unit Price', default = '0.00')
    tax_id = fields.Many2one('account.tax', string="Taxes")
    equipment_amount_total = fields.Float(string = 'Subtotal', compute = 'compute_equipment_amount_total')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.update({'description': record.product_id.name, 'price_unit' : record.product_id.list_price})

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def compute_equipment_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.product_qty * line.price_unit) * line.tax_id.amount * 0.01
            line.update({'equipment_amount_total': (line.product_qty * line.price_unit) + tax})


class SubContractEquipment(models.Model):
    _name = 'material.subcontract'
    _description = "SubContract"

    job_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Sheet')
    phase = fields.Char(string='Phase')
    task = fields.Char(string='Task')
    description = fields.Char(string = 'Description')
    subcontract_amount_total = fields.Float(string = 'Cost')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    job_cost_sheet_id = fields.Many2one('job.cost.sheet', string = 'Job Cost Sheet')
    work_order_id = fields.Many2one('project.task', string = 'Work order')
    project_id = fields.Many2one('project.project', string = 'Project')
    is_project = fields.Boolean(string = 'Is Project')
    product_type_id = fields.Selection([('material','Material'),('labour','Labour'),('service','Service'),('equipment','Equipment'),('vehicle','Vehicle')],string = "Request Type")

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.project_id:
            res['project_id'] = self.project_id.id
        if self.work_order_id:
            res['work_order_id'] = self.work_order_id.id
        if self.product_type_id:
            res['product_type_id'] = self.product_type_id
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_type_id = fields.Selection([('material','Material'),('labour','Labour'),('service','Service'),('equipment','Equipment'),('vehicle','Vehicle')],string = "Request Type",related='order_id.product_type_id')
    is_project = fields.Boolean(string='Is Project',related='order_id.is_project')

class contractContract(models.Model):
    _inherit = 'contract.contract'

    is_sub_contract = fields.Boolean(string='Is Sub Contract')
    is_customer_contract = fields.Boolean(string='Is Customer Contract')
    work_order_id = fields.Many2one('project.task', string='Work order')
    project_id = fields.Many2one('project.project', string='Project')

class CustomerPayment(models.Model):
    _inherit = 'account.payment'

    is_customer_payment = fields.Boolean(string='Is Customer Payment')
    project_id = fields.Many2one('project.project', string='Project')
