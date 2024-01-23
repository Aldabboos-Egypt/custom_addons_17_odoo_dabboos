# -*- coding: utf-8 -*-
{
    'name': "dabbos_reports",

    'summary': """
       Invoice - Sale - Purchase - Stock Reports
       
       """,


    'author': "Mohsen Sayed ",

    'category': 'reports',
    'version': '17.0',

    'depends': ['base','account','sale'],

    'data': [

        'views/views.xml',
        'views/invoice_report.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
    ],

}
