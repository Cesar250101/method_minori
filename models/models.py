# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Productos(models.Model):
    _inherit = 'product.template'

    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    responsible_id = fields.Many2one(comodel_name='res.users',string='Responsable',related='marca_id.user_id')

    @api.model
    def calcular_costo(self):
        marcar=self.env['method_minori.marcas'].search([])
        for m in marcar:
            productos_marca=self.env['product.template'].search([('marca_id','=',m.id)])
            for p in productos_marca:
                costo=round(p.list_price/1.19)*(1-(m.comision_marca/100))
                p.standard_price=costo
    
class ProductosProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def calcular_costo(self):
        marcar=self.env['method_minori.marcas'].search([])
        for m in marcar:
            productos_marca=self.env['product.product'].search([('marca_id','=',m.id)])
            for p in productos_marca:
                costo=round(p.lst_price/1.19)*(1-(m.comision_marca/100))
                p.standard_price=costo
    
    
    
class Marcas(models.Model):
    _name = 'method_minori.marcas'
    _description = 'Marcas de Productos'

    name = fields.Char(string='Nombre Marca')
    user_id = fields.Many2one(comodel_name='res.users', string='Usuario')
    comision_marca = fields.Float(string='Comisión Marca')
    
    
    



