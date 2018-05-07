# -*- coding: utf-8 -*-
# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    @api.depends('create_date')
    def _compute_channel_names(self):
        for record in self:
            res_id = record.id
            record.notify_info_channel_name = 'notify_info_%s' % res_id
            record.notify_warning_channel_name = 'notify_warning_%s' % res_id

    notify_info_channel_name = fields.Char(
        compute='_compute_channel_names')
    notify_warning_channel_name = fields.Char(
        compute='_compute_channel_names')

    @api.multi
    def notify_info(self, message, title=None, sticky=False, redirect=False):
        title = title or _('Information')
        self._notify_channel(
            'notify_info_channel_name', message, title, sticky, redirect)

    @api.multi
    def notify_warning(self, message, title=None, sticky=False,
                       redirect=False):
        title = title or _('Warning')
        self._notify_channel(
            'notify_warning_channel_name', message, title, sticky, redirect)

    @api.multi
    def _notify_channel(self, channel_name_field, message, title, sticky,
                        redirect):
        bus_message = {
            'message': message,
            'title': title,
            'sticky': sticky,
            'redirect': redirect
        }
        notifications = [(getattr(record, channel_name_field), bus_message)
                         for record in self]
        self.env['bus.bus'].sendmany(notifications)

    @api.multi
    def notify(self, message, title=None, sticky=None, redirect=False,
               warning=False):
        if warning:
            self.notify_warning(message, title, sticky, redirect)
        else:
            self.notify_info(message, title, sticky, redirect)
