# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import route

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class WebsiteSaleVariantController(WebsiteSaleVariantController):

    @route()
    def get_combination_info_website(self, *args, **kwargs):
        res = super().get_combination_info_website(*args, **kwargs)
        res['price'] = int(res['price']) if res['price'].is_integer() else res['price']
        res['list_price'] = int(res['list_price']) if res['list_price'].is_integer() else res['list_price']
        res['base_unit_price'] = int(res['base_unit_price']) if res['base_unit_price'].is_integer() else res['base_unit_price']
        return res