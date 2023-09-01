import datetime
from odoo import api, models, fields, tools
from collections import OrderedDict
import pandas as pd

class ReporteComisionMarcas(models.TransientModel):
    _inherit = 'method_minori.wizard_comision_marca'


    @api.multi
    def _comision_mes(self):
        periodo=self.env['method_minori.periodos'].search([('id','=',self.periodo_id.id)])
        pos_ids=[]
        for i in self.pos_ids:
            pos_ids.append(i.id)
        pos_ids=tuple(pos_ids) 
        qry=periodo.qry.format(self.marca_id.id,pos_ids)
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res

    @api.multi
    def _exe_query(self,qry):
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res        


class PeriodoComision(models.Model):
    _name = 'method_minori.periodos'

    name = fields.Char(string='Nombre del Periodo',requiered=True)
    nota = fields.Text(string='Descripción')    
    fecha_inicial = fields.Datetime(string='Fecha Inicial',requiered=True)
    fecha_final = fields.Datetime(string='Fecha Final',requiered=True)

    qry = fields.Text(string='Query', compute='_compute_qry')

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
            mmm.comision_marca,mmm.id as id_marca,(pol.price_subtotal*(mmm.comision_marca/100)) as valorcomision ,pc.name as sucursal
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
            and pc.id in{}
            and po.date_order between @fecha_inicial and @fecha_final
            order by po.date_order,po.sii_document_number,pol.product_id            
        """
        if self.fecha_inicial and self.fecha_final:
            fechai=self.fecha_inicial.strftime("%Y-%m-%d %H:%M:%S")
            fechai="'"+fechai+"'"
            fechaf=self.fecha_final.strftime("%Y-%m-%d %H:%M:%S")
            fechaf="'"+fechaf+"'"

            qry=qry.replace('@fecha_inicial',str(fechai))
            qry=qry.replace('@fecha_final',str(fechaf))
            self.qry= qry
    

    
    
        