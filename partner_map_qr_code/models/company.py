# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64
import re

from reportlab.graphics.barcode import createBarcodeDrawing

from odoo import api, fields, models
from urllib.parse import urlparse, parse_qs


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

    def extract_lat_lng(self, link):
        # Regular expression patterns to match latitude and longitude
        patterns = [
            r'@(-?\d+\.\d+),(-?\d+\.\d+)',  # Matches coordinates after @ symbol
            r'place/(\d+\.\d+),(\d+\.\d+)',  # Matches coordinates after place/
            r'(\d+\.\d+),(\d+\.\d+)',  # Matches simple lat,lng format
        ]

        # Iterate through patterns and try to match each
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                lat = float(match.group(1))
                lng = float(match.group(2))
                return lat, lng

        # Return None if no coordinates found
        return None


    @api.onchange('map_url')
    def _onchange_map_url(self):
        self.map_qr = self.get_image(self.map_url, code='QR', width=200, height=200, hr=True) if self.map_url else False

        if self.map_url:
            lat_lng = self.extract_lat_lng(self.map_url)
            if lat_lng:
                self.partner_latitude, self.partner_longitude = lat_lng
            else:
                self.partner_latitude = self.partner_longitude = False

    @api.onchange('partner_latitude', 'partner_longitude')
    def geo_localize(self):
        self.ensure_one()  # Ensure that only one record is being processed

        if self.partner_latitude and self.partner_longitude:
            # Use the original map_url as a base and replace the old coordinates with the new ones
            new_map_url = re.sub(
                r'@(-?\d+\.\d+),(-?\d+\.\d+)',  # Replace the coordinates after @ symbol
                '@%s,%s' % (self.partner_latitude, self.partner_longitude),
                self.map_url
            )
            new_map_url = re.sub(
                r'place/(\d+\.\d+),(\d+\.\d+)',  # Replace the coordinates after place/
                'place/%s,%s' % (self.partner_latitude, self.partner_longitude),
                new_map_url
            )
            new_map_url = re.sub(
                r'(\d+\.\d+),(\d+\.\d+)',  # Replace simple lat,lng format
                '%s,%s' % (self.partner_latitude, self.partner_longitude),
                new_map_url
            )

            self.write({
                'date_localization': fields.Date.context_today(self),
                'map_url': new_map_url,  # Use the updated map URL with the correct coordinates
                'map_qr': self.get_image(new_map_url, code='QR', width=200, height=200, hr=True),
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
