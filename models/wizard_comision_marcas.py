from odoo import api, models, fields, tools
import time


class ComisionMarcas(models.TransientModel):
    _name = 'method_minori.wizard_comision_marca'
    _description = 'Reporte de comisiones por marca'

    marca_id = fields.Many2one(comodel_name='method_minori.marcas',string='Marca')
    periodo_id = fields.Many2one(comodel_name='method_minori.periodos', string='Periodo')
    nota = fields.Text(string='Nota',related="periodo_id.nota")
    
        
    

    def _get_domain_comision(self):
        search_domain = [('date_order','>=',self.fecha_inicio),
                            ('date_order','<=',self.fecha_final)]
        return search_domain

    @api.multi
    def imprimir_pdf(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'marca_id': self.marca_id,
                'periodo': self.periodo_id,
            },
        }

        return self.env.ref('method_minori.comision_marca_report').report_action(self, config=False)

    @api.multi
    def imprimir_excel(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'marca_id': self.marca_id,
                'periodo': self.periodo_id,
            },
        }
        datos=self._comision_mes()
        print(datos)


