# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('webpay', 'Webpay Plus')], ondelete={'webpay': 'set default'}
    )
    
    webpay_commerce_code = fields.Char(
        string="Commerce Code",
        help="The Commerce Code provided by Transbank"
    )
    
    webpay_api_key = fields.Char(
        string="API Key",
        help="The API Key provided by Transbank",
        groups="base.group_system"
    )

    def _get_webpay_api_url(self):
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://webpay3g.transbank.cl/rswebpaytransaction/api/webpay/v1.2/transactions'
        else:
            return 'https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.2/transactions'

    def _webpay_get_headers(self):
        self.ensure_one()
        # Default testing credentials if empty in test mode
        commerce_code = self.webpay_commerce_code
        api_key = self.webpay_api_key
        
        if self.state == 'test' and not commerce_code:
            commerce_code = '597055555532'
            api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
            
        return {
            'Tbk-Api-Key-Id': commerce_code,
            'Tbk-Api-Key-Secret': api_key,
            'Content-Type': 'application/json'
        }
