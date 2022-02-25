import datetime
from odoo import api, models, fields, tools
from collections import OrderedDict
import pandas as pd

class ReporteComisionMarcas(models.TransientModel):
    _inherit = 'method_minori.wizard_comision_marca'


    @api.multi
    def _comision_mes(self):
        fecha_desde=self.fecha_inicio
        fecha_hasta=self.fecha_final

        qry="""
            select sdc.name as TipoDocto,po.sii_document_number as nrodocto,
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
            and po.date_order between '2022-01-31' and '2022-02-26'
            order by po.date_order,po.sii_document_number,pol.product_id
        """.format(self.marca_id.id)
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res

    @api.multi
    def _exe_query(self,qry):
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res        