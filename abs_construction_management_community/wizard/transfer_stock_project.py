from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class TransferStoreProject(models.TransientModel):
    _name = "transfer.store.project"
    _description = "Wizard for Transfer Store To Project"

    # def get_move_line_domain(self):
    #     record_ids = self._context.get('active_ids')
    #     product = self.env['product.product'].browse(record_ids)
    #     print("===============product===================",product)
    #     print("===============product.total_stock_qty.ids===================",product.product_stock_ids.ids)
    #     if product:
    #         return [('id', 'in', product.product_stock_ids.ids),('qauntity','>',0)]
    #     else:
    #         return []

    # GET DEFAULT INVOICE LINE DATA INTO WIZARD
    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        result = super(TransferStoreProject, self).default_get(fields)
        print("================TransferProjectStore======================", result)

        if record_ids:
            if 'available_qty' in fields:
                product = self.env['product.product'].browse(record_ids)
                if product.total_stock_qty:
                    result['available_qty'] = product.total_stock_qty
                    result['product_id'] = product.id

        return result

    # product_stock_id = fields.Many2one(comodel_name="product.stock", string="Stock Entry",domain=get_move_line_domain)
    project_id = fields.Many2one(comodel_name="project.project", string="Project")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    available_qty = fields.Float(string='Available Qauntity', store=True)
    transfer_qty = fields.Float(string='Transfer Qauntity')
    unit_price = fields.Float(string='Unit Price')
    tax_id = fields.Many2one('account.tax', string="Taxes")

    @api.onchange('product_id')
    def onchange_product_id(self):
        for product in self:
            if product.product_id.lst_price:
                self.unit_price = product.product_id.lst_price
            if product.product_id.supplier_taxes_id:
                self.tax_id = product.product_id.supplier_taxes_id[0].id

    @api.onchange('product_stock_id')
    def onchange_product_stock_id(self):
        for stock in self:
            if stock.product_stock_id.unit_price:
                stock.unit_price = stock.product_stock_id.unit_price
            if stock.product_stock_id.tax_id:
                stock.tax_id = stock.product_stock_id.tax_id.id

    @api.onchange('transfer_qty')
    def onchange_transfer_qty(self):
        for stock in self:
            if stock.transfer_qty > stock.available_qty:
                raise ValidationError(_("Transfer Qauntity Never More Than Available Qauntity!"))

    def button_create(self):
        print("===========button_create==============")
        if self.transfer_qty == 0:
            raise ValidationError(_("Please Insert Transfer Qauntity !"))
        project_stock = self.env['project.stock'].sudo().create({
            'product_id': self.product_id.id,
            'project_id': self.project_id.id,
            'qauntity': self.transfer_qty,
            'unit_price': self.unit_price,
            'tax_id': self.tax_id.id if self.tax_id else False,
        })
        self.product_id.product_stock_ids = [(0, 0, {
            'project_id': self.project_id.id,
            'qauntity': -(self.transfer_qty),
            'unit_price': self.unit_price,
            'tax_id': self.tax_id.id if self.tax_id else False,
        })]
        # self.product_stock_id.write({
        #     'qauntity': self.product_stock_id.qauntity - self.transfer_qty,
        # })
        # record_ids = self._context.get('active_ids')
        # project_stock = self.env['project.stock'].browse(record_ids)
        # print("===========project_stock========",project_stock)
        # if self.product_id and self.transfer_qty>0:
        #     self.product_id.product_stock_ids = [(0,0,{
        #         'project_id':project_stock.project_id.id,
        #         'qauntity':self.transfer_qty,
        #         'unit_price':self.unit_price,
        #     })]




