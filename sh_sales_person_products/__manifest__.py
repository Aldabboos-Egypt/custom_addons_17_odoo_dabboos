# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Salesperson Own Products",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "version": "0.0.1",
    "category": "Sales",    
    "summary": "Salespersons own Products Sales Person Own Product Salesperson Products Salesperson specific Products salesperson see particular product special product By salesperson Salesperson can see own Products user wise product,use own product Odoo",
    "description": """Currently, in odoo all products are visible to the salesperson, sometimes it necessary that salesperson can see their products only. Our module will help to show only specific products to the salesperson. You can assign a salesperson to a particular product so that salesperson only can see the product and its variants in odoo.""",
    "depends": [
        "sale_management"
    ],
    "data": [
        "views/product_template_views.xml",
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "25",
    "currency": "EUR"
}
