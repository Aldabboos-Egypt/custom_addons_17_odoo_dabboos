{
    "name": "Dabbos Rest API",
    "version": "17.2.10",
    "category": "API",
    "summary": "Dabbos Rest API",

    'depends': [
        'account',
        'base',
        'base_geolocalize',
        'base_setup',
        'dabbos_reports',
        'sale_management',
        'sh_sales_person_customer',
        'sh_sales_person_products',
        'stock',
        'web',
    ],
    "data": ["views/ir_model.xml", "views/res_users.xml","views/data.xml", "security/ir.model.access.csv",],

}
