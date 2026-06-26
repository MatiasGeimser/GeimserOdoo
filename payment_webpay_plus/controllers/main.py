# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class WebpayController(http.Controller):
    _return_url = '/payment/webpay/return'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def webpay_return(self, **post):
        """ Webpay Plus Return Controller """
        _logger.info("Webpay Plus: entrando al return con la data:\n%s", pprint.pformat(post))
        
        # Odoo 16+ maneja la notificación a través del entorno de transacción
        try:
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('webpay', post)
            tx_sudo._process_notification_data(post)
        except Exception as e:
            _logger.error("Webpay Plus: Error procesando la notificación: %s", e)
            return request.make_response(f"<html><body><h1>Debug Webpay Error</h1><p>{str(e)}</p></body></html>")
            
        return request.redirect('/payment/status')
