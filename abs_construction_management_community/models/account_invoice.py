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

class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one('project.project', string = 'Project')
    project_issue_id = fields.Many2one('project.issue', string = 'Project Issue')
    equipment_invoice_id = fields.Many2one('equipment.request', string = 'Equipment Request')
    vehicle_invoice_id = fields.Many2one('vehicle.request', string = 'Vehicle Request')
    work_order_id = fields.Many2one('project.task', string='Work order')
    product_type_id = fields.Selection([('material','Material'),('equipment','Equipment'),('service','Service'),('labour','Labour'),('vehicle','Vehicle')],string = "Request Type")

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.product_type_id and self.project_id:
            print("=================self==============", self.product_type_id)
            if self.product_type_id=='material' or self.product_type_id=='equipment':
                for line in self.invoice_line_ids:
                    project_stock = self.env['project.stock'].sudo().create({
                        'product_id': line.product_id.id,
                        'project_id': self.project_id.id,
                        'qauntity': line.quantity,
                        'unit_price': line.price_unit,
                        'tax_id': line.tax_ids[0].id if line.tax_ids else False,
                    })
        return res