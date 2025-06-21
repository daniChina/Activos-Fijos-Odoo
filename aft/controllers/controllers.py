# -*- coding: utf-8 -*-
# from odoo import http


# class Aft(http.Controller):
#     @http.route('/aft/aft/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/aft/aft/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('aft.listing', {
#             'root': '/aft/aft',
#             'objects': http.request.env['aft.aft'].search([]),
#         })

#     @http.route('/aft/aft/objects/<model("aft.aft"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('aft.object', {
#             'object': obj
#         })
