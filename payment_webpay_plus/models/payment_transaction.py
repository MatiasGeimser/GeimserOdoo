# -*- coding: utf-8 -*-
import logging
import requests
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Webpay-specific rendering values. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'webpay':
            return res

        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, '/payment/webpay/return')
        
        # Webpay requires integer amount
        amount = int(self.amount)
        if self.currency_id.name != 'CLP':
            raise ValidationError(_("Webpay Plus solo soporta pagos en CLP."))

        payload = {
            "buy_order": self.reference[:26], # Webpay max length is 26
            "session_id": self.reference[:61], # Max length is 61
            "amount": amount,
            "return_url": return_url,
        }

        api_url = self.provider_id._get_webpay_api_url()
        headers = self.provider_id._webpay_get_headers()

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            res.update({
                'api_url': data.get('url'),
                'token_ws': data.get('token'),
            })
            return res
        except requests.exceptions.RequestException as e:
            _logger.error("Webpay Plus: Error conectando a Transbank: %s", e)
            raise ValidationError(_("Error al conectar con Transbank Webpay Plus. Por favor intente más tarde."))

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override to find the transaction based on Transbank data. """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'webpay' or len(tx) == 1:
            return tx

        token = notification_data.get('token_ws')
        if not token:
            # En caso de anulación, Transbank envía TBK_TOKEN
            token = notification_data.get('TBK_TOKEN')
            
        if not token:
            raise ValidationError("Webpay: No se encontró el token de la transacción.")

        # Dado que Transbank solo devuelve el token_ws al return_url,
        # es difícil buscar la TX sin haber guardado el token en Odoo antes.
        # Alternativa en Odoo: Transbank no nos da la referencia en el return GET original, 
        # debemos consultar el token a TBK para obtener la orden de compra.
        # Para Odoo < 19, generalmente se busca haciendo la llamada a Transbank primero aquí, 
        # o guardando el token temporalmente.
        # Odoo requiere encontrar la tx localmente *antes* de validarla. 
        
        provider = self.env['payment.provider'].search([('code', '=', 'webpay')], limit=1)
        api_url = f"{provider._get_webpay_api_url()}/{token}"
        headers = provider._webpay_get_headers()
        
        try:
            response = requests.put(api_url, headers=headers, timeout=10)
            data = response.json()
            buy_order = data.get('buy_order')
            if not buy_order:
                # Si falla o es anulación, el PUT podría fallar
                # Si hay TBK_ORDEN_COMPRA en los params de anulación:
                buy_order = notification_data.get('TBK_ORDEN_COMPRA')
        except Exception as e:
            buy_order = notification_data.get('TBK_ORDEN_COMPRA')

        if not buy_order:
            raise ValidationError("Webpay: No se pudo determinar la orden de compra desde el token.")

        tx = self.search([('reference', '=', buy_order), ('provider_code', '=', 'webpay')])
        if not tx:
            raise ValidationError(f"Webpay: No se encontró la transacción con referencia {buy_order}.")
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Transbank data. """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'webpay':
            return
            
        token = notification_data.get('token_ws')
        if not token:
            # Caso de anulación
            self._set_canceled()
            return
            
        api_url = f"{self.provider_id._get_webpay_api_url()}/{token}"
        headers = self.provider_id._webpay_get_headers()
        
        try:
            response = requests.put(api_url, headers=headers, timeout=10)
            data = response.json()
            
            status = data.get('status')
            response_code = data.get('response_code')
            
            if status == 'AUTHORIZED' and response_code == 0:
                self._set_done()
            else:
                self._set_canceled()
                
        except Exception as e:
            _logger.error("Webpay: Error confirmando la transacción con Transbank: %s", e)
            self._set_error(_("Transbank API Error"))
