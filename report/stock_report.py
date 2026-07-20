# Copyright 2020 Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, tools

class Ventas(models.Model):
    _name = 'method_minori.ventas_report_marcas'
    _description = "Ventas por marca"
    _auto = False
    _order = 'date_order desc'

    tipodocto = fields.Char(string='Tipo Documento')  
    origen = fields.Char(string='Origen')  
    date_order = fields.Datetime(string='Fecha Orden')    
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    product_product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    product_template_id = fields.Many2one(comodel_name='product.template', string='Plantilla Producto')
    cantidad = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Precio Unitario')
    price_subtotal = fields.Float(string='Subtotal Línea')
    price_subtotal_incl = fields.Float(string='Subtotal Línea c/IVA')
    discount = fields.Float(string='% Descuento')
    nrodocto = fields.Char(string='Nro. Documento')
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    categ_id = fields.Many2one(comodel_name='product.category', string='Categoria Producto')
    user_id = fields.Many2one(
        'res.users',
        string='Responsable Marca',
        readonly=True,
    )
    vendedor_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        readonly=True,
    )
    comision = fields.Float(string='Comisión Marca')
    comision_marca = fields.Float(string='% Comisión Marca')
    session_id = fields.Many2one(comodel_name='pos.session', string='Sesión')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')
    company_id = fields.Many2one(comodel_name='res.company', string='Compañía')


    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        tools.create_index(
            self._cr,
            'method_minori_product_template_marca_idx',
            'product_template',
            ['marca_id'],
        )
        tools.create_index(
            self._cr,
            'method_minori_pos_order_state_date_idx',
            'pos_order',
            ['state', 'date_order'],
        )
        tools.create_index(
            self._cr,
            'method_minori_account_move_state_type_date_idx',
            'account_move',
            ['state', 'move_type', 'invoice_date'],
        )
        tools.create_index(
            self._cr,
            'method_minori_account_move_line_product_idx',
            'account_move_line',
            ['move_id', 'product_id'],
            where="display_type IS NULL OR display_type = 'product'",
        )
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT
                (pol.id * 2) AS id,'POS' as origen,
                sdc.name as tipodocto,
                po.date_order,
                po.partner_id as cliente_id,
                pol.product_id as product_product_id,
                pp.product_tmpl_id as product_template_id,
                pol.qty as cantidad,
                pol.price_unit,
                pol.price_subtotal,
                pol.price_subtotal_incl,
                pol.discount as discount,
                po.sii_document_number::text as nrodocto,
                mmm.id as marca_id,
                pt.categ_id as categ_id,
                mmm.user_id,
                po.user_id as vendedor_id,
                mmm.comision_marca ,
                round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                ps.id as session_id ,
                ps.config_id as sucursal_id,
                po.company_id as company_id
                from pos_order po left join sii_document_class sdc on po.document_class_id =sdc.id
                inner join pos_order_line pol on po.id =pol.order_id 
                inner join product_product pp on pol.product_id =pp.id
                inner join product_template pt on pp.product_tmpl_id =pt.id  
                left join method_minori_marcas mmm on pt.marca_id =mmm.id
                left join pos_session ps on po.session_id =ps.id 
                where po.state in ('paid', 'done', 'invoiced')
                UNION ALL
                SELECT 
                (pol.id * 2 + 1) AS id,'Ventas' as origen,
                sdc.name as tipodocto,
                po.invoice_date::timestamp as date_order,
                po.partner_id as cliente_id,
                pol.product_id as product_product_id,
                pp.product_tmpl_id as product_template_id,
                case when po.move_type = 'out_refund' then -pol.quantity else pol.quantity end as cantidad,
                pol.price_unit,
                case when po.move_type = 'out_refund' then -pol.price_subtotal else pol.price_subtotal end as neto,
                case when po.move_type = 'out_refund' then -pol.price_total else pol.price_total end as price_subtotal_incl,
                pol.discount as discount,
                po.sii_document_number::text as nrodocto,
                mmm.id as marca_id,
                pt.categ_id as categ_id,
                mmm.user_id,
                po.invoice_user_id as vendedor_id,
                mmm.comision_marca ,
                round(((case when po.move_type = 'out_refund' then -pol.price_subtotal else pol.price_subtotal end) * (mmm.comision_marca/100))) as comision,
                0 as session_id ,
                0 as sucursal_id,
                po.company_id as company_id
                from account_move po left join sii_document_class sdc on po.document_class_id =sdc.id
                inner join account_move_line pol on po.id =pol.move_id 
                inner join product_product pp on pol.product_id =pp.id
                inner join product_template pt on pp.product_tmpl_id =pt.id  
                left join method_minori_marcas mmm on pt.marca_id =mmm.id
                where po.state = 'posted'
                and po.move_type in ('out_invoice', 'out_refund')
                and (pol.display_type IS NULL OR pol.display_type = 'product')
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
    _order = 'date_order desc'

    tipodocto = fields.Char(string='Tipo Documento')
    origen = fields.Char(string='Origen')    
    date_order = fields.Date(string='Fecha Orden')    
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    product_product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    product_template_id = fields.Many2one(comodel_name='product.template', string='Plantilla Producto')
    cantidad = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Precio Unitario')
    neto = fields.Float(string='Neto Línea')
    bruto = fields.Float(string='Bruto Línea')
    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    categ_id = fields.Many2one(comodel_name='product.category', string='Categoria Producto')
    user_id = fields.Many2one(
        'res.users',
        string='Responsable Marca',
        readonly=True,
    )
    vendedor_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        readonly=True,
    )
    comision = fields.Float(string='Comisión Marca')
    comision_marca = fields.Float(string='% Comisión Marca')
    session_id = fields.Many2one(comodel_name='pos.session', string='Sesión')
    sucursal_id = fields.Many2one(comodel_name='pos.config', string='Sucursal')
    es_propia = fields.Boolean(string='Es marca propia?')


    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT 
                    (pol.id * 2) AS id,
                    sdc.name as tipodocto,
                    'POS' as origen,
                    po.date_order,
                    rp.id as cliente_id,
                    pp.id as product_product_id,
                    pt.id as product_template_id,
                    pol.qty as cantidad,
                    pol.price_unit,
                    (pol.price_subtotal-pol.discount) as neto,
                    (pol.price_subtotal_incl-pol.discount) as bruto,
                    mmm.id as marca_id,
                    pc.id as categ_id,
                    mmm.user_id,
                    po.user_id as vendedor_id,
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
                    where po.state in ('paid', 'done', 'invoiced')
                    union
                    SELECT 
                    (pol.id * 2 + 1) AS id,
                    'Nota de Venta' as tipodocto,
                    'Ventas' as origen,
                    po.date_order ,
                    rp.id as cliente_id,
                    pp.id as product_product_id,
                    pt.id as product_template_id,
                    pol.product_uom_qty  as cantidad,
                    pol.price_unit,
                    pol.price_subtotal as neto,
                    pol.price_total as bruto,
                    mmm.id as marca_id,
                    pc.id as categ_id,
                    mmm.user_id,
                    po.user_id as vendedor_id,
                    mmm.comision_marca ,
                    round((pol.price_subtotal * (mmm.comision_marca/100))) as comision,
                    0 as session_id , 
                    0 as sucursal_id,
                    mmm.es_propia
                    from sale_order  po inner join sale_order_line  pol on po.id =pol.order_id 
                    inner join product_product pp on pol.product_id =pp.id
                    inner join product_template pt on pp.product_tmpl_id =pt.id  
                    left join res_partner rp on po.partner_id =rp.id
                    left join method_minori_marcas mmm on pt.marca_id =mmm.id
                    left join product_category pc on pt.categ_id =pc.id
                    where po.state in ('sale', 'done')
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
        'res.users',
        string='Responsable Marca',
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
                    COALESCE(pt.name->>'es_CL', pt.name->>'es_ES', pt.name->>'en_US', pp.default_code, '') as nombre_producto,
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
