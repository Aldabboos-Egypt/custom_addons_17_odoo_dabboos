# -*- coding: utf-8 -*-
# Part of Softhealer Technologies

{
    "name": "Sale Order Automatic Workflow | Quotation Automatic Workflow",

    "author": "Softhealer Technologies",

    "license": "OPL-1",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "14.0.1",

    "category": "Sales",

    "summary": "Sales Order Automatic Workflow,Sales Automatic Workflow,Sales Auto Workflow,Sale Order Auto Workflow,Quotation Auto Workflow,Auto create delivery order,auto create invoice,auto validate invoice,default payment,auto invoice send by email Odoo",
    
    "description": """This module helps to create an auto workflow in sale order/quotation. A salesperson can quickly perform all sales-related operations in one shoot. You can create workflows with automatization and apply it to sales orders. When you create a quotation if you select auto workflow then press the "Confirm" button to proceed with workflow as per the configuration. You can configure auto workflow as per the requirement, for example, Automatically create the delivery order, auto-create & validate invoice, default payment journal & default payment method, auto register payments, auto invoice send by email, etc.""",
    "depends": ["sale_management","stock"],
    "data": [

        'security/ir.model.access.csv',
        'security/sale_workflow_security.xml',
        'views/res_config_settings.xml' ,
        'views/auto_sale_workflow.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
       
    ],          
    "auto_install":False,
    "installable": True,
    "application" : True, 
    "images": ["static/description/background.png", ], 
    "price": "30",
    "currency": "EUR"   
} 
