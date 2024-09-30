# -*- coding: utf-8 -*-
{
    'name': "dabbos_reports",

    'summary': """
       Invoice - Sale - Purchase - Stock Reports
       
       """,


    'author': "Mohsen Sayed ",

    'category': 'reports',
    'version': '17.2',

    'depends': ['base','account','sale','nati_arabic_font','partner_map_qr_code'],

    'data': [

        'views/views.xml',
        'views/invoice_report.xml',
        'views/sale_report.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
    ],

}
