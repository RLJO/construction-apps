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
from odoo.exceptions import ValidationError

class StoreTransfer(models.Model):
    _name = 'store.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name="product.product", string="Product",tracking=True)
    project_id = fields.Many2one(comodel_name="project.project", string="Project", tracking=True)
    project_stock_id = fields.Many2one(comodel_name="project.stock", string="Project Stock", tracking=True)
    transfer_qty = fields.Float(string='Transfer Qauntity',tracking=True)
    unit_price = fields.Float(string='Unit Price',tracking=True)
    tax_id = fields.Many2one('account.tax', string="Taxes",tracking=True)
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('transfer', 'Transfered'), ], default='draft' )

    def transfer_stock(self):
        print("Hellooooooooooooooooooooooooo==================",self.project_stock_id.remain_qty)
        if self.transfer_qty > self.project_stock_id.remain_qty:
            raise ValidationError(_("Transfer Qauntity Never More Than Available Qauntity!"))
        else:
            self.product_id.product_stock_ids = [(0, 0, {
                'project_id': self.project_id.id,
                'qauntity': self.transfer_qty,
                'unit_price': self.unit_price,
                'tax_id': self.tax_id.id if self.tax_id else False,
            })]
            self.project_stock_id.write({
                'qauntity': self.project_stock_id.qauntity - self.transfer_qty,
            })
            self.write({
                'state':'transfer'
            })

class ProductStock(models.Model):
    _name = 'product.stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'

    product_id = fields.Many2one(comodel_name="product.product", string="Product",tracking=True)
    project_id = fields.Many2one(comodel_name="project.project", string="Project",tracking=True)
    qauntity = fields.Float(string='Qauntity',tracking=True)
    unit_price = fields.Float(string='Unit Price',tracking=True)
    state = fields.Selection(string="Type", selection=[('incoming', 'In Coming'), ('outgoing', 'Out Going')],tracking=True)
    title = fields.Char(string='Title', compute='compute_title', store=True, tracking=True)
    tax_id = fields.Many2one('account.tax', string="Taxes")
    amount_total = fields.Float(string='Amount', compute='compute_amount_total', store=True, tracking=True)

    @api.depends('qauntity', 'unit_price', 'tax_id')
    def compute_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.qauntity * line.unit_price) * line.tax_id.amount * 0.01
            line.update({'amount_total': (line.qauntity * line.unit_price) + tax})

    @api.depends('project_id', 'product_id', 'qauntity')
    def compute_title(self):
        for stock in self:
            title = ''
            if stock.project_id:
                title = title + stock.project_id.name
            if stock.product_id:
                title = title + ' - ' +stock.product_id.name
            if stock.qauntity:
                title = title + ' - ' + str(stock.qauntity)
            stock.title = title


class ProjectStock(models.Model):
    _name = 'project.stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'

    project_id = fields.Many2one(comodel_name="project.project", string="Project",tracking=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product",tracking=True)
    qauntity = fields.Float(string='Qauntity',tracking=True)
    used_qauntity = fields.Float(string='Used Qauntity',default=0,tracking=True)
    remain_qty = fields.Float(string='Available Qauntity',compute = 'compute_remain_qty', store = True,tracking=True)
    unit_price = fields.Float(string='Unit Price',tracking=True)
    state = fields.Selection(string="Type", selection=[('incoming', 'In Coming'), ('outgoing', 'Out Going')],tracking=True)
    tax_id = fields.Many2one('account.tax', string="Taxes")
    amount_total = fields.Float(string='Amount', compute='compute_amount_total',store = True,tracking=True)
    project_stock_count = fields.Integer(string='Transfer', compute='_comute_project_stock_count')

    def action_view_stock_transfer(self):
        return {
                'name': _('Transfer'),
                'domain': [('project_stock_id','=',self.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'store.transfer',
                'view_id': False,
                'type': 'ir.actions.act_window'
               }

    def _comute_project_stock_count(self):
        for stock in self:
            store_transfer_obj = self.env['store.transfer'].search([('project_stock_id','=',stock.id)])
            stock.project_stock_count = len(store_transfer_obj)

    @api.depends('qauntity', 'unit_price', 'tax_id')
    def compute_amount_total(self):
        for line in self:
            tax = 0
            if line.tax_id:
                tax = (line.qauntity * line.unit_price) * line.tax_id.amount * 0.01
            line.update({'amount_total': (line.qauntity * line.unit_price) + tax})

    @api.depends('qauntity', 'used_qauntity')
    def compute_remain_qty(self):
        for stock in self:
            if stock.used_qauntity > stock.qauntity:
                raise ValidationError(_("Used Qauntity Never More Than Available Qauntity!"))
            stock.remain_qty = stock.qauntity - stock.used_qauntity

class Productproduct(models.Model):
    _inherit = 'product.product'

    product_stock_ids = fields.One2many('product.stock', 'product_id', string='Stock History',tracking=True)
    total_stock_qty = fields.Float(string='Total Stock Qauntity', compute='compute_total_stock_qty', store=True,tracking=True)
    stock_history_qty = fields.Float(string='Total Stock Qauntity', compute='compute_stock_history_qty', store=True,tracking=True)

    @api.depends('product_stock_ids','product_stock_ids.qauntity')
    def compute_total_stock_qty(self):
        for product in self:
            if product.product_stock_ids:
                product.total_stock_qty = sum(product.product_stock_ids.mapped('qauntity'))
            else:
                product.total_stock_qty = 0

    @api.depends('product_stock_ids')
    def compute_stock_history_qty(self):
        for product in self:
            product.stock_history_qty = len(product.product_stock_ids)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    cost_sheet_count = fields.Integer(string = 'Cost Sheet', compute = '_comute_cost_sheet')
    notes_count = fields.Integer(string = 'Notes', compute = '_comute_notes_count')
    estimation_sheet_cost = fields.Monetary(string = 'Estimation Cost', currency_field='currency_id', compute = 'compute_estimation_sheet_cost', store = True)

    labour_cost = fields.Float(string = 'labour Cost', compute = 'compute_labour_cost', currency_field='currency_id', store = True)
    service_cost = fields.Float(string = 'Service Cost', compute = 'compute_service_cost', currency_field='currency_id', store = True)
    material_cost = fields.Float(string = 'Material Cost', compute = 'compute_material_cost', currency_field='currency_id', store = True)
    equipment_cost = fields.Float(string = 'Equipment Cost', compute = 'compute_equipment_cost', currency_field='currency_id', store = True)
    vehicle_cost = fields.Float(string = 'Vehicle Cost', compute = 'compute_vehicle_cost', currency_field='currency_id', store = True)
    sub_contract_cost = fields.Float(string = 'Sub Contract Cost', compute = 'compute_sub_contract_cost', currency_field='currency_id', store = True)
    contract_amount = fields.Float(string = 'Contract Amount', compute = 'compute_contract_amount_cost', currency_field='currency_id', store = True)
    customer_payment = fields.Float(string = 'Customer Payment', compute = 'compute_customer_payment_cost', currency_field='currency_id', store = True)
    project_issue_cost = fields.Float(string = 'Project Issue Cost', compute = 'compute_project_issue_cost', currency_field='currency_id', store = True)
    extra_material_cost = fields.Float(string="Material Cost", compute="compute_extra_material_cost", currency_field='currency_id')
    invoice_ids = fields.One2many('account.move','project_id', string = 'Project Invoices')
    contract_ids = fields.One2many('contract.contract','project_id', string = 'Contracts')
    payment_ids = fields.One2many('account.payment','project_id', string = 'Payments')
    project_stock_ids = fields.One2many('project.stock','project_id', string = 'Project Stock')
    invoice_count = fields.Integer(string = 'Bills', compute = 'compute_invoices')
    sub_contract_count = fields.Integer(string = 'Sub Contract', compute = 'compute_sub_contract')
    customer_contract_count = fields.Integer(string = 'Customer Contract', compute = 'compute_customer_contract')
    customer_payment_count = fields.Integer(string = 'Customer Payment', compute = 'compute_customer_payment')

    cost_sheet_ids = fields.One2many('job.cost.sheet','project_id', string = 'Cost Sheets')
    total_amount = fields.Monetary(string = 'Total Costing', currency_field='currency_id', compute = 'compute_total_amount', store = True)
    diff_total_amount = fields.Monetary(string = 'Differance', currency_field='currency_id', compute = 'compute_total_amount', store = True)
    diff_customer_amount = fields.Monetary(string = 'Remaining Amount', currency_field='currency_id', compute = 'compute_diff_customer_amount', store = True)

    stock = fields.Char(string="Stock",default='Stock')

    @api.depends('invoice_ids.amount_total','cost_sheet_ids.amount_total','task_ids.extra_material_amount','material_cost','invoice_count','equipment_cost','labour_cost','service_cost','vehicle_cost','estimation_sheet_cost','contract_ids.contract_line_fixed_ids','sub_contract_count')
    def compute_total_amount(self):
        for project in self:
            total = 0
            if project.material_cost:
                total += project.material_cost
            if project.equipment_cost:
                total += project.equipment_cost
            if project.service_cost:
                total += project.service_cost
            if project.labour_cost:
                total += project.labour_cost
            if project.vehicle_cost:
                total += project.vehicle_cost
            if project.sub_contract_cost:
                total += project.sub_contract_cost
            print("==============total================",total)
            print("==============project.material_cost================",project.material_cost)
            print("==============project.equipment_cost================",project.equipment_cost)
            project.total_amount = total
            project.diff_total_amount = project.estimation_sheet_cost - total
            # if project.cost_sheet_ids:
            #     for cost_sheet in project.cost_sheet_ids:
            #         estimation_cost += cost_sheet.amount_total
            # if project.invoice_ids:
            #     for invoice in project.invoice_ids:
            #         total += invoice.amount_total
            # if project.task_ids:
            #     for extra_cost in project.task_ids:
            #         total_cost += extra_cost.extra_material_amount
            # project.total_amount = total + estimation_cost + total_cost

    @api.depends('contract_amount', 'customer_payment', 'customer_payment_count',
                 'customer_contract_count')
    def compute_diff_customer_amount(self):
        for project in self:
            project.diff_customer_amount = project.contract_amount - project.customer_payment


    def compute_invoices(self):
        account_invoice_obj = self.env['account.move']
        for project in self:
            if project:
                project.invoice_count = account_invoice_obj.search_count([('project_id', '=', project.id)])

    @api.depends('cost_sheet_ids.amount_total')
    def compute_estimation_sheet_cost(self):
        for project in self:
            job_cost_sheet_obj = self.env['job.cost.sheet'].search([('project_id','=',project.id)])
            if job_cost_sheet_obj:
                total = 0
                for cost_sheet in job_cost_sheet_obj:
                    if cost_sheet:
                        total += cost_sheet.amount_total
                project.estimation_sheet_cost = total

    def compute_sub_contract(self):
        sub_contract_obj = self.env['contract.contract']
        for contract in self:
            if contract:
                contract.sub_contract_count = sub_contract_obj.search_count([('project_id', '=', contract.id), ('is_sub_contract','=',True)])

    def compute_customer_contract(self):
        customer_contract_obj = self.env['contract.contract']
        for contract in self:
            if contract:
                contract.customer_contract_count = customer_contract_obj.search_count([('project_id', '=', contract.id), ('is_customer_contract','=',True)])

    def compute_customer_payment(self):
        customer_payment_obj = self.env['account.payment']
        for payment in self:
            if payment:
                payment.customer_payment_count = customer_payment_obj.search_count([('project_id', '=', payment.id), ('is_customer_payment','=',True)])


    @api.depends('project_stock_ids','project_stock_ids.amount_total')
    def compute_material_cost(self):
        for project in self:
            total = 0
            project_stock_objs = self.env['project.stock'].search([('project_id', '=', project.id)])
            print("=====project_stock_objs=========compute_material_cost=================", project_stock_objs)
            if project_stock_objs:
                for project_stock in project_stock_objs:
                    if project_stock.product_id.product_type_id == 'material':
                        total += project_stock.amount_total
            project.material_cost = total
            # account_invoice_obj = self.env['account.move'].search([('product_type_id', '=', 'material'),('project_id', '=', project.id),('payment_state', '=', 'paid')])
            # print("=====account_invoice_obj=========compute_material_cost=================",account_invoice_obj)
            # if account_invoice_obj:
            #     for invoice in account_invoice_obj:
            #         if invoice:
            #             total += invoice.amount_total
            # project.material_cost = total

    @api.depends('invoice_ids.amount_total', 'invoice_count')
    def compute_service_cost(self):
        for project in self:
            total = 0
            account_invoice_obj = self.env['account.move'].search(
                [('product_type_id', '=', 'service'), ('project_id', '=', project.id),('payment_state', '=', 'paid')])
            print("=====account_invoice_obj=========compute_material_cost=================", account_invoice_obj)
            if account_invoice_obj:
                for invoice in account_invoice_obj:
                    if invoice:
                        total += invoice.amount_total
            project.service_cost = total

    @api.depends('invoice_ids.amount_total', 'invoice_count')
    def compute_labour_cost(self):
        for project in self:
            total = 0
            account_invoice_obj = self.env['account.move'].search(
                [('product_type_id', '=', 'labour'), ('project_id', '=', project.id),('payment_state', '=', 'paid')])
            print("=====account_invoice_obj=========compute_labour_cost=================", account_invoice_obj)
            if account_invoice_obj:
                for invoice in account_invoice_obj:
                    if invoice:
                        total += invoice.amount_total
            project.labour_cost = total

    @api.depends('project_stock_ids','project_stock_ids.amount_total')
    def compute_equipment_cost(self):
        for project in self:
            total = 0
            project_stock_objs = self.env['project.stock'].search([('project_id', '=', project.id)])
            print("=====project_stock_objs=========compute_material_cost=================", project_stock_objs)
            if project_stock_objs:
                for project_stock in project_stock_objs:
                    if project_stock.product_id.product_type_id == 'equipment':
                        total += project_stock.amount_total
            project.equipment_cost = total
            # account_invoice_obj = self.env['account.move'].search(
            #     [('product_type_id', '=', 'equipment'), ('project_id', '=', project.id),('payment_state', '=', 'paid')])
            # print("=====account_invoice_obj=========compute_material_cost=================", account_invoice_obj)
            # if account_invoice_obj:
            #     for invoice in account_invoice_obj:
            #         if invoice:
            #             total += invoice.amount_total
            # project.equipment_cost = total
            # equipment_request_obj = self.env['equipment.request'].search([('project_id','=',project.id)])
            # if equipment_request_obj:
            #     total = 0
            #     for equipment in equipment_request_obj:
            #         if equipment:
            #             account_invoice_obj = self.env['account.move'].search([('invoice_origin','=',equipment.name)])
            #             if account_invoice_obj:
            #                 for invoice in account_invoice_obj:
            #                     if invoice:
            #                         total += invoice.amount_total
            #     project.equipment_cost = total

    @api.depends('invoice_ids.amount_total','invoice_count')
    def compute_vehicle_cost(self):
        for project in self:
            total = 0
            account_invoice_obj = self.env['account.move'].search(
                [('product_type_id', '=', 'vehicle'), ('project_id', '=', project.id),('payment_state', '=', 'paid')])
            print("=====account_invoice_obj=========compute_labour_cost=================", account_invoice_obj)
            if account_invoice_obj:
                for invoice in account_invoice_obj:
                    if invoice:
                        total += invoice.amount_total
            project.vehicle_cost = total
            # vehicle_request_obj = self.env['vehicle.request'].search([('project_id','=',project.id)])
            # if vehicle_request_obj:
            #     total = 0
            #     for vehicle in vehicle_request_obj:
            #         if vehicle:
            #             account_invoice_obj = self.env['account.move'].search([('invoice_origin','=',vehicle.name)])
            #             if account_invoice_obj:
            #                 for invoice in account_invoice_obj:
            #                     if invoice:
            #                         total += invoice.amount_total
            #     project.vehicle_cost = total

    @api.depends('contract_ids.contract_line_fixed_ids','contract_ids.sub_contract_amount_total', 'sub_contract_count')
    def compute_sub_contract_cost(self):
        for project in self:
            total = 0
            contract_obj = self.env['contract.contract'].search(([('project_id', '=', project.id), ('is_sub_contract','=',True)]))
            print("=====account_invoice_obj=========contract_obj=================", contract_obj)
            if contract_obj:
                for contract in contract_obj:
                    total += contract.sub_contract_amount_total
                    # for line in contract.contract_line_fixed_ids:
                    #     total += line.price_subtotal
            project.sub_contract_cost = total

    @api.depends('contract_ids.contract_line_fixed_ids', 'contract_ids.contract_amount_total', 'customer_contract_count')
    def compute_contract_amount_cost(self):
        for project in self:
            total = 0
            contract_obj = self.env['contract.contract'].search(
                ([('project_id', '=', project.id), ('is_customer_contract', '=', True)]))
            print("=====account_invoice_obj=========contract_obj=================", contract_obj)
            if contract_obj:
                for contract in contract_obj:
                    total += contract.contract_amount_total
                    # for line in contract.contract_line_fixed_ids:
                    #     total += line.price_subtotal
            project.contract_amount = total

    @api.depends('payment_ids.amount', 'customer_payment_count')
    def compute_customer_payment_cost(self):
        for project in self:
            # total = 0
            # account_invoice_obj = self.env['account.move'].search(
            #     [('is_customer_project', '=', True), ('project_id', '=', project.id), ('payment_state', '=', 'paid')])
            # print("=====account_invoice_obj=========compute_labour_cost=================", account_invoice_obj)
            # if account_invoice_obj:
            #     for invoice in account_invoice_obj:
            #         if invoice:
            #             total += invoice.amount_total
            # project.customer_payment = total
            total = 0
            payment_obj = self.env['account.payment'].search(([('project_id', '=', project.id),('is_customer_payment', '=', True)]))
            if payment_obj:
                for payment in payment_obj:
                    total += payment.amount
            project.customer_payment = total

    @api.depends('invoice_ids.amount_total')
    def compute_project_issue_cost(self):
        for project in self:
            project_issue_obj = self.env['project.issue'].search([('project_id','=',project.id)])
            if project_issue_obj:
                total = 0
                for issue in project_issue_obj:
                    if issue:
                        account_invoice_obj = self.env['account.move'].search([('project_issue_id','=',issue.id)])
                        if account_invoice_obj:
                            for invoice in account_invoice_obj:
                                if invoice:
                                    total += invoice.amount_total
                project.project_issue_cost = total

    def _comute_cost_sheet(self):
        for project in self:
            job_cost_sheet_obj = self.env['job.cost.sheet'].search([('project_id','=',project.id)])
            count = 0
            if job_cost_sheet_obj:
                for sheet in job_cost_sheet_obj:
                    if sheet:
                        count += 1
            project.cost_sheet_count = count

    @api.depends('task_ids.extra_material_amount')
    def compute_extra_material_cost(self):
        for project in self:
            total = 0
            if project.task_ids:
                for task in project.task_ids:
                    if task.extra_material_amount:
                        total += task.extra_material_amount
            project.extra_material_cost = total

    def _comute_notes_count(self):
        for project in self:
            project_notes_obj = self.env['project.notes'].search([('project_id','=',project.id)])
            count = 0
            if project_notes_obj:
                for note in project_notes_obj:
                    if note:
                        count += 1
            project.notes_count = count

    def action_view_cost_sheet(self):
        return {
                'name': _('Cost Sheet'),
                'domain': [('project_id','=',self.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'job.cost.sheet',
                'view_id': False,
                'views': [(self.env.ref('abs_construction_management_community.view_job_cost_sheet_menu_tree').id, 'tree'),(self.env.ref('abs_construction_management_community.view_job_cost_sheet_menu_form').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def action_view_project_notes(self):
        return {
                'name': _('Notes'),
                'domain': [('project_id','=',self.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'project.notes',
                'view_id': False,
                'views': [(self.env.ref('abs_construction_management_community.view_project_notes_menu_tree').id, 'tree'),(self.env.ref('abs_construction_management_community.view_project_notes_menu_form').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def action_view_invoices(self):
        return {
                'name': _('Invoices'),
                'domain': [('project_id','=',self.id)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'views': [(self.env.ref('account.view_in_invoice_tree').id, 'tree'),(self.env.ref('account.view_move_form').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def action_view_stock(self):
        return {
                'name': _('Project Stock'),
                'domain': [('project_id','=',self.id)],
                'context': {'search_default_product_id':1},
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'project.stock',
                'view_id': False,
                'type': 'ir.actions.act_window'
               }

    def action_view_sub_contract(self):
        return {
                'name': _('Sub Contract'),
                'domain': [('project_id','=',self.id), ('is_sub_contract','=',True)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'contract.contract',
                'view_id': False,
                'views': [(self.env.ref('contract.contract_contract_tree_view').id, 'tree'),(self.env.ref('contract.contract_contract_supplier_form_view').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def action_view_customer_contract(self):
        return {
                'name': _('Customer Contract'),
                'domain': [('project_id','=',self.id), ('is_customer_contract','=',True)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'contract.contract',
                'view_id': False,
                'views': [(self.env.ref('contract.contract_contract_tree_view').id, 'tree'),(self.env.ref('contract.contract_contract_customer_form_view').id, 'form')],
                'type': 'ir.actions.act_window'
               }

    def action_view_customer_payment(self):
        return {
                'name': _('Customer Payment'),
                'domain': [('project_id','=',self.id), ('is_customer_payment','=',True)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.payment',
                'view_id': False,
                'views': [(self.env.ref('account.view_account_payment_tree').id, 'tree'),(self.env.ref('account.view_account_payment_form').id, 'form')],
                'type': 'ir.actions.act_window'
               }
