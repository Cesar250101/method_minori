# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Productos(models.Model):
    _inherit = 'product.template'

    marca_id = fields.Many2one(comodel_name='method_minori.marcas', string='Marca')
    responsible_id = fields.Many2one(comodel_name='res.users',string='Responsable',related='marca_id.user_id.id')
    
    
    
class Marcas(models.Model):
    _name = 'method_minori.marcas'
    _description = 'Marcas de Productos'

    name = fields.Char(string='Nombre Marca')
    user_id = fields.Many2one(comodel_name='res.users', string='Usuario')
    



