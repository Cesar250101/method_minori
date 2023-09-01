import math
from odoo import api, models, fields, tools
import time
import xlsxwriter
import base64
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz

class ComisionMarcas(models.TransientModel):
    _name = 'method_minori.wizard_comision_marca'
    _description = 'Reporte de comisiones por marca'

    marca_id = fields.Many2one(comodel_name='method_minori.marcas',string='Marca')
    periodo_id = fields.Many2one(comodel_name='method_minori.periodos', string='Periodo')
    nota = fields.Text(string='Nota',related="periodo_id.nota")
    pos_ids = fields.Many2many(comodel_name='pos.config', string='Sucursal')
    
        
    

    def _get_domain_comision(self):
        search_domain = [('date_order','>=',self.fecha_inicio),
                            ('date_order','<=',self.fecha_final)]
        return search_domain

    @api.multi
    def imprimir_pdf(self):
        pos_ids=[]
        for i in self.pos_ids:
            pos_ids.append(i.id)
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'marca_id': self.marca_id,
                'periodo': self.periodo_id,
                'sucursales':pos_ids
            },
        }

        return self.env.ref('method_minori.comision_marca_report').report_action(self, config=False)

    @api.multi
    def imprimir_excel(self):

        data = self.read()[0]
        marca_id = data['marca_id']
        periodo_id = data['periodo_id']
        datos=self._comision_mes()
        datos_lista=list(datos)                
        data={
            'datos':datos,
            'form_data':self.read()[0]
        }
        return self.env.ref('method_minori.report_comision_marcas_xlsx').report_action(self,data=data)

class ComisionMarcasExcel(models.AbstractModel):
    _name='report.method_minori.report_comision_excel'
    _inherit='report.report_xlsx.abstract'

    def generate_xlsx_report(self,workbook,data,comision):
        sheet=workbook.add_worksheet(data['form_data']['marca_id'][1])
        bold=workbook.add_format({'bold':True})
        row=3
        col=3
        total=0
        neto=0
        iva=0
        porc_comision=0
        comision=0
        factura_bruta=0
        sheet.write(row-2,col,'VENTAS :'+ data['form_data']['periodo_id'][1],bold)
        sheet.write(row-2,col+3,'MARCA :'+ data['form_data']['marca_id'][1],bold)
        sheet.write(row,col,'Tipodocto',bold)
        sheet.write(row,col+1,'NroDocto',bold)
        sheet.write(row,col+2,'Fecha',bold)
        sheet.write(row,col+3,'Marca',bold)
        sheet.write(row,col+4,'Sku',bold)
        sheet.write(row,col+5,'Producto',bold)
        sheet.write(row,col+6,'Cantidad',bold)
        sheet.write(row,col+7,'Pvp',bold)
        sheet.write(row,col+8,'Descuento',bold)
        sheet.write(row,col+9,'SubTotal',bold)
        sheet.write(row,col+10,'Comisión',bold)

        for d in data['datos']:
            row+=1
            sheet.write(row,col,d['tipodocto'])
            sheet.write(row,col+1,d['nrodocto'])
            sheet.write(row,col+2,d['fecha'])
            sheet.write(row,col+3,d['marca'])
            sheet.write(row,col+4,d['sku'])
            sheet.write(row,col+5,d['nombreproducto'])
            sheet.write(row,col+6,d['cantidad'])
            sheet.write(row,col+7,d['pvp'])
            sheet.write(row,col+8,d['discount'])
            sheet.write(row,col+9,d['subtotal'])
            sheet.write(row,col+10,d['comision_marca'])
            porc_comision=d['comision_marca']
            total+=d['subtotal']
        #Total
        sheet.write(row+2,col+8,'Total Venta Bruta',bold)
        sheet.write(row+2,col+9,total,bold)
        #Iva
        neto=round(total/1.19) 
        iva=total-neto
        sheet.write(row+3,col+8,'Iva',bold)
        sheet.write(row+3,col+9,iva,bold)
        #Neto
        sheet.write(row+4,col+8,'Neto',bold)
        sheet.write(row+4,col+9,neto,bold)
        #Comisión
        comision=round(neto*(porc_comision/100)) 
        sheet.write(row+5,col+8,str(porc_comision) +' Margen',bold)
        sheet.write(row+5,col+9,comision,bold)
        #Venta neto        
        sheet.write(row+6,col+8, 'Total Venta Neta',bold)
        sheet.write(row+6,col+9,neto-comision,bold)
        #Factura Bruta
        factura_bruta=round((neto-comision)*1.19) 
        sheet.write(row+7,col+8, 'Factuta Bruta',bold)
        sheet.write(row+7,col+9,round((neto-comision)*1.19),bold)




