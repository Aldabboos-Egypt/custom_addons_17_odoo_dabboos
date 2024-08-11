# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64
from reportlab.graphics.barcode import createBarcodeDrawing

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    map_url = fields.Char(string='Google Map URL')
    map_qr = fields.Binary(string='Map QR')

    # @api.onchange('street', 'street2', 'zip', 'city', 'state_id')
    # def _onchange_address(self):
    #     for partner in self.with_context(lang='en_US'):
    #         result = partner._geo_localize(partner.street,
    #                                        partner.zip,
    #                                        partner.city,
    #                                        partner.state_id.name,
    #                                        partner.country_id.name)
    #         if result:
    #             url = 'http://www.google.com/maps/place/%s,%s' % (result[0], result[1])
    #             partner.partner_latitude = result[0]
    #             partner.partner_longitude = result[1]
    #             partner.date_localization = fields.Date.context_today(partner)
    #             partner.map_url = 'http://www.google.com/maps/place/%s,%s' % (result[0], result[1])
    #             partner.map_qr = self.get_image(url, code='QR', width=200, height=200, hr=True)

    @api.onchange('map_url')
    def _onchange_map_url(self):
        self.map_qr = self.get_image(self.map_url, code='QR', width=200, height=200, hr=True) if self.map_url else False


    @api.onchange('partner_latitude','partner_longitude')
    def geo_localize(self):

        if self.partner_latitude and self.partner_longitude:
            url = 'http://www.google.com/maps/place/%s,%s' % (self.partner_latitude, self.partner_longitude)
            self.write({

                'date_localization': fields.Date.context_today(self),
                'map_url': 'http://www.google.com/maps/place/%s,%s' % (self.partner_latitude,self.partner_longitude),
                'map_qr': self.get_image(url, code='QR', width=200, height=200, hr=True),

            })


    def get_image(self, value, width, height, hr, code='QR'):
        """ genrating image for barcode """
        options = {}
        if hr:
            options['humanReadable'] = True
        try:
            ret_val = createBarcodeDrawing(code, value=str(value), **options)
        except Exception:
            raise 'error'
        return base64.encodebytes(ret_val.asString('jpg'))
