from . import models
from . import controllers

import odoo.addons.payment as payment


def post_init_hook(env):
    """Create the accounting payment method and journal line for Webpay."""
    provider = env['payment.provider'].search([('code', '=', 'webpay')], limit=1)
    if not provider:
        return

    provider._setup_payment_method('webpay')
    payment_method = provider._get_provider_payment_method('webpay')
    payment_line = env['account.payment.method.line'].search([
        ('payment_provider_id', '=', provider.id),
        ('journal_id', '!=', False),
    ], limit=1)
    if payment_method and provider.journal_id and not payment_line:
        # Let account_payment determine the provider from the payment method.
        env['account.payment.method.line'].create({
            'name': 'Webpay Plus (Transbank)',
            'payment_method_id': payment_method.id,
            'journal_id': provider.journal_id.id,
        })


def uninstall_hook(env):
    payment.reset_payment_provider(env, 'webpay')
