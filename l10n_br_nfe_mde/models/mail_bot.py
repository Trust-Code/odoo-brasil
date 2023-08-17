from odoo import api, fields, models


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'
    
    def _find_channel(self, bot_id, partner):
        return self.env['mail.channel'].with_context(mail_create_nosubscribe=True).create({
            'channel_partner_ids': [(4, partner.id), (4, bot_id)],
            'public': 'private',
            'channel_type': 'chat',
            'email_send': False,
            'name': 'OdooBot'
        })
    
    def send_message_to_user(self, user, message):
        partner = user.partner_id
        _, odoobot_id = self.env['ir.model.data']._xmlid_to_res_model_res_id("base.partner_root")
        channel = self._find_channel(odoobot_id, partner)
        channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
