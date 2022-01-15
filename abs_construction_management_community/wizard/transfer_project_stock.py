from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class TransferProjectStore(models.TransientModel):
    _name = "transfer.project.store"
    _description = "Wizard for Transfer Project To Store"

    # GET DEFAULT INVOICE LINE DATA INTO WIZARD
    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        result = super(TransferProjectStore, self).default_get(fields)
        print("================TransferProjectStore======================", result)

        if record_ids:
            if 'product_id' in fields:
                project_stock = self.env['project.stock'].browse(record_ids)
                if project_stock.product_id:
                    result['product_id'] = project_stock.product_id.id
                    result['available_qty'] = project_stock.remain_qty
                    result['unit_price'] = project_stock.unit_price
                if project_stock.tax_id:
                    result['tax_id'] = project_stock.tax_id.id

        return result

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    available_qty = fields.Float(string='Available Qauntity')
    transfer_qty = fields.Float(string='Transfer Qauntity')
    unit_price = fields.Float(string='Unit Price')
    tax_id = fields.Many2one('account.tax', string="Taxes")


    @api.onchange('transfer_qty')
    def onchange_transfer_qty(self):
        for stock in self:
            if stock.transfer_qty > stock.available_qty:
                raise ValidationError(_("Transfer Qauntity Never More Than Available Qauntity!"))

    def button_create(self):
        print("===========button_create==============")
        if self.transfer_qty == 0:
            raise ValidationError(_("Please Insert Transfer Qauntity !"))
        record_ids = self._context.get('active_ids')
        project_stock = self.env['project.stock'].browse(record_ids)
        print("===========project_stock========",project_stock)
        if self.product_id and self.transfer_qty>0:
            store_transfer = self.env['store.transfer'].sudo().create({
                'product_id': self.product_id.id,
                'project_id': project_stock.project_id.id,
                'project_stock_id': project_stock.id,
                'transfer_qty': self.transfer_qty,
                'unit_price': self.unit_price,
                'state':'draft',
                'tax_id': self.tax_id.id if self.tax_id else False,
            })
            # self.product_id.product_stock_ids = [(0,0,{
            #     'project_id':project_stock.project_id.id,
            #     'qauntity':self.transfer_qty,
            #     'unit_price':self.unit_price,
            #     'tax_id': self.tax_id.id if self.tax_id else False,
            # })]
            # project_stock.write({
            #     'qauntity': project_stock.qauntity - self.transfer_qty,
            # })




