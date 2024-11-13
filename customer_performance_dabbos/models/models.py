# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    payment_method= fields.Char( string='طريقة التسديد ',  )
    customer_extent   = fields.Char( string='مدى إلتزام الزبون بمواعيد السداد ',    )
    Customer_discount= fields.Char( string='خصم الزبون  حسب التارجت  ',     )
    receiving_time_goods= fields.Char( string='وقت إستلام البضاعة  ',    )
    administrator_time= fields.Char( string='وقت تواجد المسؤول ',    )
    nature_region_inhabitants= fields.Char( string='طبيعة المنطقة وسكانها',     )
    shop_location_on_gps = fields.Char(string='موقع المحل على GPS')
    product_returns = fields.Char(string='المرتجعات بالمنتجات ')
    customer_desires_products  = fields.Char(string='المنتجات التي يرغب بها الزبون وغير متواجدة حاليا')
    products_customer_not_work= fields.Char(string='المنتجات التي لا يعمل بها الزبون')
    information_shop_owner= fields.Char(string='معلومات عامة عن صاحب المحل او المسؤول ')
    general_notes= fields.Char(string='ملاحظات عامة ')
    pictures = fields.Binary(string='الصور ')
    opining_store_date= fields.Date(string='تاريخ فتح المحل ')
    powerful_companies_deal= fields.Char(string='أقوي الشركات التي يتعامل معها ')
    best_selling_products = fields.Char(string='اقوى المنتجات بيعاً من غير منتجاتنا ')
    proportion_our_goods_shop = fields.Char(string='نسبة بضاعتنا من المحل ')
    opinion_extent_his_satisfaction= fields.Char(string='رأيه في شركتنا ومدى رضاه عنها ')
    opinion_extent_strength_market = fields.Char( string='رأيه في شركتنا ومدى قوتها بالسوق', )



