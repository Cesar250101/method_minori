# Copyright 2020 Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, models, fields, tools

class VentasMarcas(models.Model):
    _name = 'method_minori.ventas_report_marcas'
    _description = "Point of Sale Orders Report"
    _auto = False
    _order = 'date desc'
        
    date = fields.Datetime(string='Order Date', readonly=True)
    order_id = fields.Many2one('pos.order', string='Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    state = fields.Selection(
        [('draft', 'New'), ('paid', 'Paid'), ('done', 'Posted'),
         ('invoiced', 'Invoiced'), ('cancel', 'Cancelled')],
        string='Status')
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    price_total = fields.Float(string='Total Price', readonly=True)
    price_sub_total = fields.Float(string='Subtotal w/o discount', readonly=True)
    total_discount = fields.Float(string='Total Discount', readonly=True)
    average_price = fields.Float(string='Average Price', readonly=True, group_operator="avg")
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    nbr_lines = fields.Integer(string='Sale Line Count', readonly=True, oldname='nbr')
    product_qty = fields.Integer(string='Product Quantity', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    delay_validation = fields.Integer(string='Delay Validation')
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    invoiced = fields.Boolean(readonly=True)
    config_id = fields.Many2one('pos.config', string='Point of Sale', readonly=True)
    pos_categ_id = fields.Many2one('pos.category', string='PoS Category', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True)
    session_id = fields.Many2one('pos.session', string='Session', readonly=True)
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marcas')
    es_propia = fields.Boolean(string='Marca Propia?')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')

    def _select(self):
        return """
            SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                s.date_order AS date,
                SUM(l.qty) AS product_qty,
                SUM(l.qty * l.price_unit) AS price_sub_total,
                SUM((l.qty * l.price_unit) * (100 - l.discount) / 100) AS price_total,
                SUM((l.qty * l.price_unit) * (l.discount / 100)) AS total_discount,
                (SUM(l.qty*l.price_unit)/SUM(l.qty * u.factor))::decimal AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                s.location_id AS location_id,
                s.company_id AS company_id,
                s.sale_journal AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pt.pos_categ_id,
                s.pricelist_id,
                s.session_id,
                s.invoice_id IS NOT NULL AS invoiced,
                pt.marca_id ,mmm.es_propia,pc.id as sucursal_id  
        """

    def _from(self):
        return """
            FROM pos_order_line AS l
                LEFT JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                left join method_minori_marcas mmm on (pt.marca_id=mmm.id )
                left join pos_config pc on ps.config_id =pc.id 
        """

    def _group_by(self):
        return """
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.location_id, s.company_id, s.sale_journal,
                s.pricelist_id, s.invoice_id, s.create_date, s.session_id,
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pt.marca_id,mmm.es_propia,pc.id  
        """

    def _having(self):
        return """
            HAVING
                SUM(l.qty * u.factor) != 0
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._group_by(),self._having())
        )


# Informe de ventas por marcar con segmentación de marcas propias
class MarcasPropias(models.Model):
    _name = 'method_minori.report_marcas_propias'
    _description = "Ventas por marca y segmentación por marcas propias y no propias"
    _auto = False
    _order = 'product_id desc'

    origen = fields.Char(string='Origen Venta')    
    date = fields.Datetime(string='Order Date', readonly=True)
    order_id = fields.Many2one('pos.order', string='Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    state = fields.Selection(
        [('draft', 'New'), ('paid', 'Paid'), ('done', 'Posted'),
         ('invoiced', 'Invoiced'), ('cancel', 'Cancelled')],
        string='Status')
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    price_total = fields.Float(string='Total', readonly=True)
    price_sub_total = fields.Float(string='Neto', readonly=True)
    total_discount = fields.Float(string='Total Discount', readonly=True)
    average_price = fields.Float(string='Average Price', readonly=True, group_operator="avg")
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    nbr_lines = fields.Integer(string='Sale Line Count', readonly=True, oldname='nbr')
    product_qty = fields.Integer(string='Product Quantity', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    delay_validation = fields.Integer(string='Delay Validation')
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    invoiced = fields.Boolean(readonly=True)
    config_id = fields.Many2one('pos.config', string='Point of Sale', readonly=True)
    pos_categ_id = fields.Many2one('pos.category', string='PoS Category', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True)
    session_id = fields.Many2one('pos.session', string='Session', readonly=True)
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marcas')
    es_propia = fields.Boolean(string='Marca Propia?')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')

    def _select(self):
        return """
                SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                'POS' as origen,
                s.date_order AS date,
                SUM(l.qty) AS product_qty,
                round( SUM((l.qty * l.price_unit) * (100 - l.discount) / 100)/1.19,0) AS price_sub_total,
                SUM((l.qty * l.price_unit) * (100 - l.discount) / 100) AS price_total,
                SUM((l.qty * l.price_unit) * (l.discount / 100)) AS total_discount,
                (SUM(l.qty*l.price_unit)/SUM(l.qty * u.factor))::decimal AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                s.location_id AS location_id,
                s.company_id AS company_id,
                s.sale_journal AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pt.pos_categ_id,
                s.pricelist_id,
                s.session_id,
                s.invoice_id IS NOT NULL AS invoiced,
                pt.marca_id ,mmm.es_propia,pc.id as sucursal_id  
            FROM pos_order_line AS l
                LEFT JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                left join method_minori_marcas mmm on (pt.marca_id=mmm.id )
                left join pos_config pc on ps.config_id =pc.id 
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.location_id, s.company_id, s.sale_journal,
                s.pricelist_id, s.invoice_id, s.create_date, s.session_id,
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pt.marca_id,mmm.es_propia,pc.id  
            HAVING
                SUM(l.qty * u.factor) != 0
          union      
            SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                'Sale' as origen,
                s.date_order AS date,
                SUM(l.product_uom_qty) AS product_qty,
                SUM(l.price_subtotal) AS price_sub_total,
                SUM((l.product_uom_qty * l.price_unit) * (100 - l.discount) / 100) AS price_total,
                SUM((l.product_uom_qty * l.price_unit) * (l.discount / 100)) AS total_discount,
                (SUM(l.product_uom_qty*l.price_unit)/SUM(l.product_uom_qty * u.factor))::decimal AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                null  AS location_id,
                s.company_id AS company_id,
                null  AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                p.product_tmpl_id,
                null as config_id,
                pt.pos_categ_id,
                s.pricelist_id,
                null as session_id,
                null AS invoiced,
                pt.marca_id ,mmm.es_propia,null  as sucursal_id  
            FROM sale_order_line  AS l
                LEFT JOIN sale_order  s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                left join method_minori_marcas mmm on (pt.marca_id=mmm.id ) 
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.company_id, 
                s.pricelist_id,  s.create_date, 
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                pt.marca_id,mmm.es_propia  
            HAVING
                SUM(l.product_uom_qty  * u.factor) != 0

        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s

            )
        """ % (self._table, self._select())
        )



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
    precio_venta = fields.Integer(string='Precio de Venta')
    location_id = fields.Many2one(
        'stock.location',
        string='Ubicacion Stock',
        readonly=True,
    )
    nombre_producto = fields.Char(string='Nombre Producto')
    sku = fields.Char(string='SKU')

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
                    sq.quantity AS Stock,
                    pt.marca_id,
                    mmm.user_id,pt.list_price AS precio_venta,
                    sl.id as location_id,
                    pt.name as nombre_producto,
                    pp.default_code as sku
                    FROM stock_quant sq, product_product pp ,product_template pt,method_minori_marcas mmm,stock_location sl  
                    where sq.product_id =pp.id 
                    and pp.product_tmpl_id =pt.id
                    and pt.marca_id =mmm.id
                    and sq.location_id =sl.id 
                    and sl.usage='internal'
                    and pp.active=true                     
            )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))
