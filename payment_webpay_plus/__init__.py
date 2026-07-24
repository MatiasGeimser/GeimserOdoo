from . import models
from . import controllers

import odoo.addons.payment as payment


def post_init_hook(env):
    """Create the accounting payment method and journal line for Webpay."""
    payment.setup_provider(env, 'webpay')


def uninstall_hook(env):
    payment.reset_payment_provider(env, 'webpay')
