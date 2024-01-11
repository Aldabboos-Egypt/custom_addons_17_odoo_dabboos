# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Salesperson Own Customers",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "version": "0.0.1",
    "category": "Sales",
    "summary": "salesperson specific customer vendor see particular customer special customer salesperson customer seller get particular client Odoo Salesperson own contact Salesperson own contacts saleperson own contacts saleperson own contact saleperson own customer saleperson own customers salesperson own partner salesperson own partners saleperson own partner saleperson own partners sales person own contact sale person own contact sale person own contacts sales person own contacts sales own contact sales own customer own contact own contacts Own Customer for salesperson Own Customers for salesperson Own Customer for sales person Own Customer for saleperson Own Customer for sale person Own contact for salesperson Own contacts for salesperson user own customer user own customers user own contact user own contacts salesperson customer salesperson contact own customer sale order own customers sale order own customers so own contact sale order own contact sale order own contact so own customer quotation own customers quotation own contact quotation own contact quotation",
    "description": """
Currently in odoo all customers are visible to salesperson,
For this our module will help to show only specific customers to salesperson.
""",
    "depends": ["sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizard/sh_sales_person_customer_views.xml",
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "19",
    "currency": "EUR"
}
