from odoo import api, models, fields, tools

class Ventas(models.Model):
    _name = 'method_minori.ventas_dia_report'
    _description = "Ventas por marca"
    _auto = False
    _order = 'fecha_dia'

    origen = fields.Char(string='Origen Venta')
    fecha_dia = fields.Date(string='Fecha')
    dia = fields.Integer(string='Día')
    total = fields.Integer(string='Total')
    impuesto = fields.Integer(string='impuesto')
    neto = fields.Integer(string='neto')
    ultimo = fields.Integer(string='Ultimo')
    primero = fields.Integer(string='Primero')
    es_propia = fields.Boolean(string='Marca Propia?')

    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT
                    ROW_NUMBER() OVER() AS id,
                    'POS' as origen,
                    date(s.date_order) as fecha_dia,
                    EXTRACT(day FROM s.date_order) as dia,
                   SUM((l.qty * l.price_unit) * (100 - l.discount) / 100) as total,
                    SUM((l.qty * l.price_unit) * (100 - l.discount) / 100)- (SUM((l.qty * l.price_unit) * (100 - l.discount) / 100)/1.19) as impuesto,
                    round( SUM((l.qty * l.price_unit) * (100 - l.discount) / 100)/1.19,0) as neto,
                    max(s.sii_document_number)  as Ultimo,min(s.sii_document_number) as Primero,
                    mmm.es_propia 
            FROM pos_order_line AS l
                LEFT JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                left join method_minori_marcas mmm on (pt.marca_id=mmm.id )
                left join pos_config pc on ps.config_id =pc.id 
				group by date(s.date_order),EXTRACT(day FROM s.date_order),es_propia             
				 union 
                    SELECT 
                    ROW_NUMBER() OVER() AS id,
                    'Sale' as origen,
                    date(po.date_order) as fecha_dia,
                    EXTRACT(day FROM po.date_order) as dia,
                    sum(pol.price_total) as total,
                    sum(pol.price_total-pol.price_subtotal) as impuesto,
                    sum(pol.price_subtotal) as neto,
                    0  as Ultimo,
                    0 as Primero,
                    mmm.es_propia 
                    from sale_order po inner join sale_order_line  pol on po.id =pol.order_id
                    inner join product_product pp on pol.product_id =pp.id
                    inner join product_template pt on pp.product_tmpl_id =pt.id  
                    left join res_partner rp on po.partner_id =rp.id
                    left join method_minori_marcas mmm on pt.marca_id =mmm.id
                    left join product_category pc on pt.categ_id =pc.id  
                    group by date(po.date_order),EXTRACT(day FROM po.date_order),es_propia 

            )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))

class NotasCredito(models.Model):
    _name = 'method_minori.notas_credito_report'
    _description = "Notas de crédito emitidas"
    _auto = False
    _order = 'fecha_dia'

    fecha = fields.Date(string='Fecha')
    tipo = fields.Char(string='Tipo Docto')
    nro = fields.Char(string='Nro. Docto')
    bruto = fields.Integer(string='Bruto')
    impuesto = fields.Integer(string='Impuesto')
    neto = fields.Integer(string='neto')

    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (select ROW_NUMBER() OVER() AS id,
                    po.date_order as fecha,
                    sdc.name as tipo,
                    po.sii_document_number as nro,
                    po.amount_total as bruto,
                    po.amount_tax as impuesto,
                    (po.amount_total-po.amount_tax) as neto
                    from pos_order po left join res_partner rp on po.partner_id =rp.id
                    inner join sii_document_class sdc  on po.document_class_id =sdc.id
                    where sdc.sii_code =61
                                )
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))

