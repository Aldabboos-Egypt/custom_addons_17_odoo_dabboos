# -*- coding: utf-8 -*-
# Copyright 2018 Openinside co. W.L.L.
{
    "name": "Amount in order & company currency",
    "summary": "Purchase Order - Show total amounts in order currency & company currency",
    "version": "17.0.1.1.0",
    'category': 'Purchases',
    "website": "https://www.open-inside.com",
	"description": """
		
		
		 
    """,
	'images':[
        'static/description/cover.png'
	],
    "author": "Openinside",
    "license": "OPL-1",
    "price" : 9.99,
    "currency": 'EUR',
    "installable": True,
    "depends": [
        'purchase'
    ],
    "data": [
        'view/purchase_order.xml',
        # 'view/web_assets.xml'
    ],    
    'odoo-apps' : True 
}

