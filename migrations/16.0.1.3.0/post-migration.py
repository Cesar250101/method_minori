# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

NEW_NAME = 'ConceptStore'


def migrate(cr, version):
    """Renombra la categoría de grupos «Stock Proveedores» a «ConceptStore».

    El registro vive en un bloque ``noupdate="1"``, por eso ``-u`` no lo
    actualiza en bases existentes. ``name`` es traducible (jsonb en Odoo 16),
    así que se escribe por ORM en cada idioma instalado. Idempotente.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    category = env.ref('method_minori.module_proveedor_stock_category', raise_if_not_found=False)
    if not category:
        return
    langs = {'en_US'} | {code for code, _name in env['res.lang'].get_installed()}
    for lang in sorted(langs):
        category.with_context(lang=lang).write({'name': NEW_NAME})
