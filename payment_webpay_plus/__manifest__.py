# -*- coding: utf-8 -*-
{
    'name': 'Webpay Plus (Transbank) Payment Provider',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'A payment provider for Webpay Plus (Transbank) in Chile',
    'description': """
Webpay Plus Payment Provider
=============================

This module integrates Transbank Webpay Plus for Odoo 19.
It uses the REST API v1.2 to process payments securely.
    """,
    'author': 'Geimser',
    'website': 'https://github.com/matiasgeimser/geimserodoo',
    'depends': ['payment', 'website_sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_webpay_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'application': False,
    'license': 'LGPL-3',
}
