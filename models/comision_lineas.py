# -*- coding: utf-8 -*-
#
# Comisión de marca almacenada en cada línea de venta.
#
# La vista `method_minori.ventas_report_marcas` ya calcula la comisión en vivo
# (subtotal × % de la marca); aquí además la persistimos en cada línea de detalle
# (pos.order.line / account.move.line) para que quede visible y auditable dentro de
# Odoo y para que la liquidación se acumule desde el dato guardado en la línea.
#
# El valor se mantiene como campo calculado-almacenado: se recalcula solo cuando
# cambia el subtotal de la línea, el producto, o el % de comisión de la marca.

from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    comision_marca_valor = fields.Float(
        string='Comisión Marca',
        compute='_compute_comision_marca_valor',
        store=True,
        help='Comisión de la marca aplicada a esta línea = subtotal neto × % de comisión de la marca.',
    )

    @api.depends(
        'price_subtotal',
        'product_id',
        'product_id.product_tmpl_id.marca_id.comision_marca',
    )
    def _compute_comision_marca_valor(self):
        for line in self:
            marca = line.product_id.product_tmpl_id.marca_id
            pct = marca.comision_marca if marca else 0.0
            # En POS las devoluciones ya vienen con subtotal negativo, por lo que el
            # signo de la comisión se hereda directamente del subtotal.
            line.comision_marca_valor = round(line.price_subtotal * (pct / 100.0))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    comision_marca_valor = fields.Float(
        string='Comisión Marca',
        compute='_compute_comision_marca_valor',
        store=True,
        help='Comisión de la marca aplicada a esta línea de factura/nota de crédito.',
    )

    @api.depends(
        'price_subtotal',
        'product_id',
        'move_id.move_type',
        'product_id.product_tmpl_id.marca_id.comision_marca',
    )
    def _compute_comision_marca_valor(self):
        for line in self:
            marca = line.product_id.product_tmpl_id.marca_id
            move_type = line.move_id.move_type
            if not marca or move_type not in ('out_invoice', 'out_refund'):
                line.comision_marca_valor = 0.0
                continue
            # Las notas de crédito (out_refund) restan: mismo criterio de signo que la
            # vista ventas_report_marcas.
            sign = -1.0 if move_type == 'out_refund' else 1.0
            line.comision_marca_valor = round(sign * line.price_subtotal * (marca.comision_marca / 100.0))
