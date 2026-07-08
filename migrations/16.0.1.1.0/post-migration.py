# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Asigna company_id=1 a los registros existentes de marcas y periodos."""
    cr.execute(
        "UPDATE method_minori_marcas SET company_id = 1 WHERE company_id IS NULL"
    )
    cr.execute(
        "UPDATE method_minori_periodos SET company_id = 1 WHERE company_id IS NULL"
    )
