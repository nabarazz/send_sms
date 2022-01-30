import datetime
import logging
import urllib
from urllib.request import urlopen

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SendMessage(models.TransientModel):
    _name = 'message.send_sms'
    _description = 'Send SMS'

    message = fields.Char()
    channel = fields.Many2one('sms.channel')

    
    def default_data(self):
        for record in self.env['res.partner'].browse(self._context.get('active_ids', [])):
            _logger.info("Checking for %s mobile number", record.name)
            if record.mobile:
                return record[0].mobile
            else:
                raise UserError(_("Partner does not have mobile number"))

    def send_sms(self):
        try:
            setting = self.env['res.config.settings'].search([])[-1]
        except IndexError:
            raise UserError(_("Please tick the 'Send SMS' box in general settings"))

        if setting and setting.group_send_sms:
            mobile = self.default_data()
            _logger.info("Checking message content")
            if self.message:
                message = self.message
            else:
                raise UserError(_("You are trying to send empty message"))
            _logger.info("Checking channel availability")
            if self.channel:
                sms_auth_key = self.channel.sms_auth_key
                
                
                
            else:
                raise UserError(_("Please set SMS channel under general settings to send message."))

            _logger.info("Sending message to %s", mobile)
            msg = message
            values = {
                'auth_key': sms_auth_key,
                'to': mobile,
                'text': msg,
                
            }

            post_data = urllib.parse.urlencode(values).encode("utf-8")  # URL encoding the data here.
            req = urllib.request.Request('https://sms.aakashsms.com/sms/v3/send', post_data)
            response = urlopen(req)

            partner = self.env['res.partner'].browse(self._context.get('active_ids', []))[0]
            channel = self.env['sms.channel'].search([('name', '=', self.channel.name)])
            output = response.read()  # Get Response
            _logger.info("Adding message to sent message table")
            self.env['sent.sms'].create({
                'partner': partner.id,
                'channel': channel.id,
                'mobile': mobile,
                'time': datetime.datetime.now(),
                'message': msg,
                'status': response.msg,
            })
            _logger.info("Message sent to %s successfully", mobile)

        else:
            raise UserError(_("Please check the 'Send SMS' in general settings"))
