odoo.define('web_notify.WebClient', function (require) {
    "use strict";

    var base_bus = require('bus.bus');
    var core = require('web.core');
    var WebClient = require('web.WebClient');
    var session = require('web.session');
    var Notification = require('web.notification').Notification;

    var UsersNotification = Notification.extend({
        template: "UsersNotification",

        init: function (parent, title, text, sticky, redirect) {
            this._super(parent, title, text, sticky);
            this.redirect = redirect;
            this.events = _.extend(this.events || {}, {
                'click .go_to_activity': function () {
                    var self = this;
                    this.do_action({
                        name: this.redirect.name,
                        type: 'ir.actions.act_window',
                        res_model: this.redirect.model,
                        target: 'current',
                        views: [[false, this.redirect.view], [false, 'form']],
                        domain: this.redirect.domain,
                        context: this.redirect.context
                    });
                },
            });
        },
    });

    WebClient.include({
        init: function (parent, client_options) {
            this._super(parent, client_options);
        },
        show_application: function () {
            this.start_polling();
            return this._super.apply(this, arguments);
        },
        on_logout: function () {
            var self = this;
            base_bus.bus.off('notification', this, this.bus_notification);
            this._super();
        },
        start_polling: function () {
            this.channel_warning = 'notify_warning_' + session.uid;
            this.channel_info = 'notify_info_' + session.uid;
            base_bus.bus.add_channel(this.channel_warning);
            base_bus.bus.add_channel(this.channel_info);
            base_bus.bus.on('notification', this, this.bus_notification);
            base_bus.bus.start_polling();
        },
        bus_notification: function (notifications) {
            var self = this;
            _.each(notifications, function (notification) {
                var channel = notification[0];
                var message = notification[1];
                if (message.redirect) {
                    self.on_message_redirect(message)
                } else if (channel === self.channel_warning) {
                    self.on_message_warning(message);
                } else if (channel == self.channel_info) {
                    self.on_message_info(message);
                }
            });
        },
        on_message_redirect: function (message) {
            if (this.notification_manager) {
                var notification = new UsersNotification(this.notification_manager, message.title, message.message, message.sticky, message.redirect);
                this.notification_manager.display(notification);
            }
        },
        on_message_warning: function (message) {
            if (this.notification_manager) {
                this.notification_manager.do_warn(message.title, message.message, message.sticky);
            }
        },
        on_message_info: function (message) {
            if (this.notification_manager) {
                this.notification_manager.do_notify(message.title, message.message, message.sticky);
            }
        }
    });
});