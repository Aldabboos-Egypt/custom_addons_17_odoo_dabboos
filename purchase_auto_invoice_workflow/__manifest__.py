# -*- coding: utf-8 -*-

{
    "name": "Purchase Automatic Workflow | Quotation Automatic Workflow",

    "author": "Dabbos",

    "license": "OPL-1",



    "version": "14.0.1",

    "category": "Purchase",

    "summary": "Purchase Order Automatic Workflow,Purchase Automatic Workflow,Purchase Auto Workflow,Purchase Order Auto Workflow ",
    
    "description": """This module helps to create an auto workflow in Purchase order/rfq. """,
    "depends": ["purchase","stock",'purchase_stock'],
    "data": [

        'security/ir.model.access.csv',
        'security/purchase_workflow_security.xml',
        'views/res_config_settings.xml' ,
        'views/auto_purchase_workflow.xml',
        'views/purchase_order.xml',
        'views/res_partner.xml',
       
    ],          
    "auto_install":False,
    "installable": True,

} 
