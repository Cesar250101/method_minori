# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    liquidacion_mode = fields.Selection(
        selection=[
            ('periodos', 'Períodos definidos (method_minori.periodos)'),
            ('mes_cerrado', 'Mes cerrado (del 1 al fin de mes)'),
        ],
        string='Modo de liquidación',
        default='periodos',
        required=True,
        help='Define cómo se construyen los períodos del reporte de liquidaciones en el '
             'portal:\n'
             '- Períodos definidos: usa los registros de method_minori.periodos.\n'
             '- Mes cerrado: usa meses calendario completos (del 1 al último día de cada mes).',
    )
