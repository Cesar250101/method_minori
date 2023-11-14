# Copyright 2020 Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, tools

class Ventas(models.Model):
    _name = 'method_minori.ventas_report_marcas'
    _description = "Ventas por marca"
    _auto = False
    _order = 'product_id desc'

    tipodocto = fields.Char(string='Tipo Documento')  
    origen = fields.Char(string='Origen')  
    date_order = fields.Datetime(string='Fecha Orden')    
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    product_product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    product_template_id = fields.Many2one(comodel_name='product.template', string='Plantilla Producto')
    cantidad = fields.Integer(string='Cantidad')    
    price_unit = fields.Integer(string='Precio Unitario')
    price_subtotal = fields.Integer(string='Subtotal Línea')
    price_subtotal_incl = fields.Integer(string='Subtotal Línea c/IVA')
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    categ_id = fields.Many2one(comodel_name='product.category', string='Categoria Producto')
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        readonly=True,
    )    
    comision = fields.Integer(string='Comisión Marca')
    comision_marca = fields.Char(string='Comisión Marca')    
    session_id = fields.Many2one(comodel_name='pos.session', string='Sesión')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')

    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT 
                ROW_NUMBER() OVER() AS id,'POS' as origen,
                sdc.name as tipodocto,
                po.date_order,
                rp.id as cliente_id,
                pp.id as product_product_id,
                pt.id as product_template_id,
                pol.qty as cantidad,
                pol.price_unit,
                pol.price_subtotal,
                pol.price_subtotal_incl,         
                mmm.id as marca_id,
                pc.id as categ_id,
                mmm.user_id,
                mmm.comision_marca ,
                round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                ps.id as session_id , 
                pc2.id as sucursal_id
                from pos_order po left join sii_document_class sdc on po.document_class_id =sdc.id
                inner join pos_order_line pol on po.id =pol.order_id 
                inner join product_product pp on pol.product_id =pp.id
                inner join product_template pt on pp.product_tmpl_id =pt.id  
                left join res_partner rp on po.partner_id =rp.id
                left join method_minori_marcas mmm on pt.marca_id =mmm.id
                left join product_category pc on pt.categ_id =pc.id 
                left join pos_session ps on po.session_id =ps.id 
                left join pos_config pc2 on ps.config_id =pc2.id  
                union 
                SELECT 
                ROW_NUMBER() OVER() AS id,'Ventas' as origen,
                sdc.name as tipodocto,
                po.date_invoice,
                rp.id as cliente_id,
                pp.id as product_product_id,
                pt.id as product_template_id,
                pol.quantity as cantidad,
                pol.price_unit,
                pol.price_subtotal as neto,
                mmm.id as marca_id,
                pc.id as categ_id,
                mmm.user_id,
                mmm.comision_marca ,
                round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                0 as session_id , 
                0 as sucursal_id
                from account_invoice po left join sii_document_class sdc on po.document_class_id =sdc.id
                inner join account_invoice_line pol on po.id =pol.invoice_id 
                inner join product_product pp on pol.product_id =pp.id
                inner join product_template pt on pp.product_tmpl_id =pt.id  
                left join res_partner rp on po.partner_id =rp.id
                left join method_minori_marcas mmm on pt.marca_id =mmm.id
                left join product_category pc on pt.categ_id =pc.id
            )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))

# Informe de ventas por marcar con segmentación de marcas propias
class MarcasPropias(models.Model):
    _name = 'method_minori.report_marcas_propias'
    _description = "Ventas por marca y segmentación por marcas propias y no propias"
    _auto = False
    _order = 'product_id desc'

    tipodocto = fields.Char(string='Tipo Documento')
    origen = fields.Char(string='Origen')    
    date_order = fields.Date(string='Fecha Orden')    
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    product_product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    product_template_id = fields.Many2one(comodel_name='product.template', string='Plantilla Producto')
    cantidad = fields.Integer(string='Cantidad')    
    price_unit = fields.Integer(string='Precio Unitario')
    neto = fields.Integer(string='Neto Línea')
    bruto = fields.Integer(string='Bruto Línea')
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    categ_id = fields.Many2one(comodel_name='product.category', string='Categoria Producto')
    user_id = fields.Many2one(
        're.users',
        string='Usuario',
        readonly=True,
    )    
    comision = fields.Integer(string='Comisión Marca')
    comision_marca = fields.Char(string='Comisión Marca')    
    session_id = fields.Many2one(comodel_name='pos.session', string='Sesión')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')
    es_propia = fields.Boolean(string='Es marca propia?')

    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT 
                    ROW_NUMBER() OVER() AS id,
                    sdc.name as tipodocto,
                    'POS' as origen,
                    po.date_order,
                    rp.id as cliente_id,
                    pp.id as product_product_id,
                    pt.id as product_template_id,
                    pol.qty as cantidad,
                    pol.price_unit,
                    pol.price_subtotal as neto,
                    pol.price_subtotal_incl as bruto,
                    mmm.id as marca_id,
                    pc.id as categ_id,
                    mmm.user_id,
                    mmm.comision_marca ,
                    round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                    ps.id as session_id , 
                    pc2.id as sucursal_id,
                    mmm.es_propia
                    from pos_order po left join sii_document_class sdc on po.document_class_id =sdc.id
                    inner join pos_order_line pol on po.id =pol.order_id 
                    inner join product_product pp on pol.product_id =pp.id
                    inner join product_template pt on pp.product_tmpl_id =pt.id  
                    left join res_partner rp on po.partner_id =rp.id
                    left join method_minori_marcas mmm on pt.marca_id =mmm.id
                    left join product_category pc on pt.categ_id =pc.id 
                    left join pos_session ps on po.session_id =ps.id 
                    left join pos_config pc2 on ps.config_id =pc2.id
                    union
                    SELECT 
                    ROW_NUMBER() OVER() AS id,
                    sdc.name as tipodocto,
                    'Ventas' as origen,
                    po.date_invoice,
                    rp.id as cliente_id,
                    pp.id as product_product_id,
                    pt.id as product_template_id,
                    pol.quantity as cantidad,
                    pol.price_unit,
                    pol.price_subtotal as neto,
                    pol.price_total as bruto,
                    mmm.id as marca_id,
                    pc.id as categ_id,
                    mmm.user_id,
                    mmm.comision_marca ,
                    round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                    0 as session_id , 
                    0 as sucursal_id,
                    mmm.es_propia
                    from account_invoice po left join sii_document_class sdc on po.document_class_id =sdc.id
                    inner join account_invoice_line pol on po.id =pol.invoice_id 
                    inner join product_product pp on pol.product_id =pp.id
                    inner join product_template pt on pp.product_tmpl_id =pt.id  
                    left join res_partner rp on po.partner_id =rp.id
                    left join method_minori_marcas mmm on pt.marca_id =mmm.id
                    left join product_category pc on pt.categ_id =pc.id  
  
            )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))


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
