from odoo import api, models, fields, tools
from odoo.exceptions import AccessError
from collections import OrderedDict
import pandas as pd
import pytz
from datetime import datetime, timezone, timedelta

class ReporteComisionMarcas(models.TransientModel):
    _inherit = 'method_minori.wizard_comision_marca'



    def _comision_mes(self):
        allowed_brands = self.env['method_minori.marcas']._get_allowed_dashboard_brands()
        if self.marca_id not in allowed_brands:
            raise AccessError('No tiene acceso a la marca seleccionada.')

        fecha_inicial=self.periodo_id.fecha_inicial.date().isoformat()
        fecha_final=(self.periodo_id.fecha_final.date()- timedelta(days=1)).isoformat()
        qry="""select sdc.name as TipoDocto,po.sii_document_number as nrodocto,TO_CHAR(po.date_order , 'YYYY-MM-DD') as fecha,
                    mmm.name as marca,pp.default_code as sku,
                    COALESCE(pt.name->>%s, pt.name->>'es_CL', pt.name->>'es_ES', pt.name->>'en_US', pp.default_code, '')  as nombreproducto,
                    pol.qty as cantidad,price_unit as pvp,pol.discount,pol.price_subtotal_incl as subtotal,pol.price_subtotal as neto,
                    mmm.comision_marca,mmm.id as id_marca,(pol.price_subtotal*(mmm.comision_marca/100)) as valorcomision ,pc.name as sucursal
                    from pos_order po inner join pos_order_line pol on po.id=pol.order_id
                    inner join pos_session ps on po.session_id =ps.id 
                    inner join pos_config pc on ps.config_id =pc.id 
                    left join sii_document_class sdc on po.document_class_id =sdc.id
                    inner join product_product pp on pol.product_id  =pp.id
                    inner join product_template pt on pp.product_tmpl_id =pt.id
                    inner join method_minori_marcas mmm on pt.marca_id =mmm.id
                    where mmm.id = %s
                    and pc.id = %s
                    and po.date_order between %s and %s
                    and po.state in ('paid', 'done', 'invoiced')
                    order by po.date_order,po.sii_document_number,pol.product_id            
        """
        self._cr.execute(
            qry,
            (
                self.env.lang or 'en_US',
                self.marca_id.id,
                self.pos_id.id,
                '{} 00:00:00'.format(fecha_inicial),
                '{} 23:55:55'.format(fecha_final),
            ),
        )
        _res = self._cr.dictfetchall()
        return _res


    def _exe_query(self,qry):
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res        


class PeriodoComision(models.Model):
    _name = 'method_minori.periodos'

    name = fields.Char(string='Nombre del Periodo', compute='_compute_name', store=True, readonly=True)
    nota = fields.Text(string='Descripción')
    fecha_inicial = fields.Datetime(string='Fecha Inicial', required=True)
    fecha_final = fields.Datetime(string='Fecha Final', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Compañía', default=lambda self: self.env.company)

    # qry = fields.Text(string='Query', compute='_compute_qry')
    qry = fields.Text(string='Query')

    _MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
    }

    @api.depends('fecha_inicial')
    def _compute_name(self):
        for rec in self:
            if rec.fecha_inicial:
                rec.name = "{}{:02d}".format(rec.fecha_inicial.year, rec.fecha_inicial.month)
            else:
                rec.name = False

    @api.onchange('fecha_inicial','fecha_final')
    def _onchange_fecha(self):
        if self.fecha_inicial and self.fecha_final:
            self.nota="""
            El periodo tiene como fechas de corte:
            Fecha Inicial ={}
            Fecha Final ={}
            """.format(self.fecha_inicial.strftime('%d-%m-%y') ,self.fecha_final.strftime('%d-%m-%y'))



    @api.depends('fecha_inicial','fecha_final')
    def _compute_qry(self):
        qry="""select sdc.name as TipoDocto,po.sii_document_number as nrodocto,
            TO_CHAR(po.date_order , 'YYYY-MM-DD') as fecha,
            mmm.name as marca,pp.default_code as sku,
            concat(pt.name,' ',var.variant) as nombreproducto
            ,pol.qty as cantidad,pol.price_unit as pvp,pol.discount,pol.price_subtotal_incl as subtotal,pol.price_subtotal as neto,
            case when mmm.comision_marca is null then 0 else mmm.comision_marca end comision_marca,mmm.id as id_marca,(pol.price_subtotal*(mmm.comision_marca/100)) as valorcomision ,pc.name as sucursal
            from pos_order po inner join pos_order_line pol on po.id=pol.order_id
            inner join pos_session ps on po.session_id =ps.id 
            inner join pos_config pc on ps.config_id =pc.id 
            inner join sii_document_class sdc on po.document_class_id =sdc.id
            inner join product_product pp on pol.product_id  =pp.id
            inner join product_template pt on pp.product_tmpl_id =pt.id
            inner join method_minori_marcas mmm on pt.marca_id =mmm.id
            left join (select pavppr.product_product_id, string_agg(pav.name, '-') as variant
            from product_product pp , product_attribute_value_product_product_rel pavppr, 
            product_attribute_value pav 
            where pp.id =pavppr.product_product_id 
            and pavppr.product_attribute_value_id =pav.id
            group by pavppr.product_product_id) var on pp.id=var.product_product_id 
            where mmm.id = {}
            and pc.id ={}
            and po.date_order between @fecha_inicial and @fecha_final
            order by po.date_order,po.sii_document_number,pol.product_id            
        """
        try:
            if self.fecha_inicial and self.fecha_final:
                fechai=self.fecha_inicial.strftime("%Y-%m-%d %H:%M:%S")
                fechai="'"+fechai+"'"
                fechaf=self.fecha_final.strftime("%Y-%m-%d %H:%M:%S")
                fechaf="'"+fechaf+"'"

                qry=qry.replace('@fecha_inicial',str(fechai))
                qry=qry.replace('@fecha_final',str(fechaf))
                self.qry= qry
        except:
            pass    

    
    
        
