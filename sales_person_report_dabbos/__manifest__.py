{
    'name' : 'Sales Person  Report Dabbos',
    'author': "Mohsen",
    'version' : '17.1',
     'summary' : 'Sales Person Report Dabbos',

    'depends' : ['base','sale_management','purchase','stock','account'],
    "license" : "OPL-1",
    'data': [
            'security/ir.model.access.csv',
            'view/sales_partner.xml',
            ],
    'qweb' : [],
    'demo' : [],
    'installable' : True,
    'auto_install' : False,
    'category' : 'sales',
}
