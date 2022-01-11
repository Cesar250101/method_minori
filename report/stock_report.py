# Copyright 2020 Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, tools


class StockReport(models.Model):
    _name = 'method_minori.stock_report'
    _description = "Respote stock por proveedor"
    _auto = False
    _order = 'product_id desc'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        readonly=True,
    )
    product_categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        readonly=True,
    )
    stock = fields.Integer(
        string="Stock",
        readonly=True,
    )
    marca_id = fields.Many2one(
        'method_minori.marcas',
        string='Marca',
        readonly=True,
    )

    user_id = fields.Many2one(
        're.users',
        string='Usuario',
        readonly=True,
    )




    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT 
                ROW_NUMBER() OVER() AS id,
                sq.product_id AS product_id,
                pp.product_tmpl_id ,
                pt.categ_id AS product_categ_id,
                sum(sq.quantity) AS Stock,
                pt.marca_id,
                mmm.user_id
                FROM stock_quant sq, product_product pp ,product_template pt,method_minori_marcas mmm 
                where sq.product_id =pp.id 
                and pp.product_tmpl_id =pt.id
                and pt.marca_id =mmm.id
                and sq.quantity >0
                group by sq.product_id ,pp.product_tmpl_id ,pt.categ_id ,pt.marca_id,mmm.user_id                
            )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))
