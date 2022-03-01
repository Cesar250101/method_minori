import datetime
from odoo import api, models, fields, tools
from collections import OrderedDict
import pandas as pd

class ReporteComisionMarcas(models.TransientModel):
    _inherit = 'method_minori.wizard_comision_marca'


    @api.multi
    def _comision_mes(self):
        periodo=self.env['method_minori.periodos'].search([('id','=',self.periodo_id.id)])
        qry=periodo.qry.format(self.marca_id.id)
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

    name = fields.Char(string='Nombre del Periodo')
    nota = fields.Text(string='Descripción')    
    fecha_inicial = fields.Datetime(string='Fecha Inicial')
    fecha_final = fields.Datetime(string='Fecha Final')

    qry = fields.Text(string='Query', compute='_compute_qry')

    @api.onchange('fecha_inicial','fecha_final')
    def _onchange_fecha(self):
        self.nota="""
        El periodo tiene como fechas de corte:
        Fecha Inicial ={}
        Fecha Final ={}
        """.format(self.fecha_inicial.strftime('%d-%m-%y') ,self.fecha_final.strftime('%d-%m-%y'))
        
    

    @api.depends('fecha_inicial','fecha_final')
    def _compute_qry(self):
        qry="""select sdc.name as TipoDocto,po.sii_document_number as nrodocto,
            TO_CHAR(po.date_order , 'YYYY-MM-DD') as fecha,
            mmm.name as marca,pp.default_code as sku,pt.name as nombreproducto,pol.qty as cantidad,pol.price_unit as pvp,pol.price_subtotal as subtotal,
            mmm.comision_marca,mmm.id as id_marca,(pol.price_subtotal*(mmm.comision_marca/100)) as valorcomision 
            from pos_order po, pos_order_line pol,sii_document_class sdc,method_minori_marcas mmm, product_template pt,product_product pp  
            where po.id=pol.order_id 
            and po.document_class_id =sdc.id 
            and pol.product_id  =pp.id 
            and pp.product_tmpl_id =pt.id 
            and pt.marca_id =mmm.id    
            and mmm.id = {}
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
    

    
    
        