# -*- coding: utf-8 -*-
{
    'name': "method_minori",

    'summary': """
        Localización Empresa Minori""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Method ERP",
    'website': "https://www.method.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/Reporting',
    'version': '16.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'stock',
        'purchase',
        'sale',
        'account',
        'point_of_sale',
        'l10n_cl_dte_point_of_sale',
        'report_xlsx',
    ],

    # always loaded
    'data': [
        'data/marcas_propias.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/stock_report.xml',
        'report/comision_marca.xml',
        'report/reporte_marcas.xml',
        'wizard/wizard_comision_marcas.xml',
        'report/pos_order_report_view.xml',
        'views/sales_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'method_minori/static/src/js/sales_dashboard.js',
            'method_minori/static/src/xml/sales_dashboard.xml',
            'method_minori/static/src/scss/sales_dashboard.scss',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
