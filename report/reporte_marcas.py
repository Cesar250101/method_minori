from odoo import api, models, fields, tools

class Ventas(models.Model):
    _name = 'method_minori.ventas_dia_report'
    _description = "Ventas por marca"
    _auto = False
    _order = 'fecha_dia'

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
                    date(po.date_order) as fecha_dia,
                    EXTRACT(day FROM po.date_order) as dia,
                    sum(po.amount_total) as total,sum(po.amount_tax) as impuesto,
                    sum(po.amount_total-po.amount_tax) as neto,
                    max(po.sii_document_number)  as Ultimo,min(po.sii_document_number) as Primero,
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
                    group by date(po.date_order),EXTRACT(day FROM po.date_order),es_propia 
                    order by date(po.date_order)
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

