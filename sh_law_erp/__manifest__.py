# -*- coding: utf-8 -*-

{
    "name": "Law Management System",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",

    "category": "Extra Tools",
    "version": "17.0.0",
    "license": "OPL-1",
    "summary": """
Legal Case Management,
Law Firm ERP,
Legal & Law Practice Management,
Law ERP Module,
Manage Law Cases App,
Law Matter Management System,
Track Law Cases With Full Step,
Handle Law Acts, Law Articles Management Odoo
""",
    "description": """
Do you want the "Law ERP" system in odoo?
Do you want to manage all "Law Matters" from a single system?
In today"s competition, you need a "Law ERP" system to track
every step of the case/matter quickly.
So we have made a "Law ERP Management" system that provides
the full lifecycle of laws.
You can manage every matter with end to end law process.
Using this module you can handle every type of law matters.
Law Management System Odoo, Law ERP System Odoo,
Legal & Law Practice Management, Law ERP Module, Manage Law Cases,
Law Matter Management System, Legal Case Management, Law Firm ERP,
Track Law Cases With Full Step, Handle Law Acts,
Law Articles Management Odoo, Legal Case Management,
Law Firm ERP, Legal & Law Practice Management,
Law ERP Module, Manage Law Cases App,
Law Matter Management System, Track Law Cases With Full Step,
Handle Law Acts, Law Articles Management Odoo
""",
    "depends": [
        "sale_management",
        "hr",
        "utm",
    ],
    "data": [
        "security/sh_law_erp_security.xml",
        "security/ir.model.access.csv",
        "wizards/reason_wizard.xml",
        "wizards/mark_lost_wizard.xml",
        "wizards/invoice_wizard.xml",
        "views/law_practise_area.xml",
        "views/client_request.xml",
        "views/courts.xml",
        "views/judge.xml",
        "views/opposition_lawyer.xml",
        "views/opposition_parties.xml",
        "views/victim.xml",
        "views/act_article.xml",
        "views/evidence.xml",
        "views/matter.xml",
        "views/trial.xml",
        "views/hr.xml",
        "views/metter_type.xml",
        "views/matter_category.xml",
        "views/favor.xml",
        "views/account_move.xml",
        "views/customer.xml",
        "reports/matter_detailed_report.xml",
        "views/corp.xml"
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/description/background.png", ],
    "price": 61,
    "currency": "USD"
}
