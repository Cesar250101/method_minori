# -*- coding: utf-8 -*-
from odoo import http

# class MethodMinori(http.Controller):
#     @http.route('/method_minori/method_minori/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/method_minori/method_minori/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('method_minori.listing', {
#             'root': '/method_minori/method_minori',
#             'objects': http.request.env['method_minori.method_minori'].search([]),
#         })

#     @http.route('/method_minori/method_minori/objects/<model("method_minori.method_minori"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('method_minori.object', {
#             'object': obj
#         })