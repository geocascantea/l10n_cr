# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import phonenumbers
import logging
from . import api_facturae

_logger = logging.getLogger(__name__)


class PartnerElectronic(models.Model):
    _inherit = "res.partner"

    commercial_name = fields.Char(string="Nombre comercial", required=False, )
    state_id = fields.Many2one(
        "res.country.state", string="Provincia", required=False, )
    district_id = fields.Many2one(
        "res.country.district", string="Distrito", required=False, )
    county_id = fields.Many2one(
        "res.country.county", string="Cantón", required=False, )
    neighborhood_id = fields.Many2one(
        "res.country.neighborhood", string="Barrios", required=False, )
    identification_id = fields.Many2one("identification.type", string="Tipo de identificacion",
                                        required=False, )
    payment_methods_id = fields.Many2one(
        "payment.methods", string="Métodos de Pago", required=False, )

    has_exoneration = fields.Boolean(string="Posee exoneración", required=False)
    type_exoneration = fields.Many2one("aut.ex", string="Tipo Autorizacion", required=False, )
    exoneration_number = fields.Char(string="Número de exoneración", required=False, )
    institution_name = fields.Char(string="Institucion Emisora", required=False, )
    date_issue = fields.Date(string="Fecha de Emisión", required=False, )
    date_expiration = fields.Date(string="Fecha de Vencimiento", required=False, )
    activity_id = fields.Many2one("economic.activity", string="Actividad Económica por defecto", required=False, )
    economic_activities_ids = fields.Many2many('economic.activity', string=u'Actividades Económicas',)


    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone:
            phone = phonenumbers.parse(self.phone,
            self.country_id and self.country_id.code or 'CR')
            valid = phonenumbers.is_valid_number(phone)
            if not valid:
                alert = {
                    'title': 'Atención',
                    'message': _('Número de teléfono inválido')
                }
                return {'value': {'phone': ''}, 'warning': alert}

    @api.onchange('mobile')
    def _onchange_mobile(self):
        if self.mobile:
            mobile = phonenumbers.parse(self.mobile, 
                self.country_id and self.country_id.code or 'CR')
            valid = phonenumbers.is_valid_number(mobile)
            if not valid:
                alert = {
                    'title': 'Atención',
                    'message': 'Número de teléfono inválido'
                }
                return {'value': {'mobile': ''}, 'warning': alert}

    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            if not re.match(r'^(\s?[^\s,]+@[^\s,]+\.[^\s,]+\s?,)*(\s?[^\s,]+@[^\s,]+\.[^\s,]+)$', self.email.lower()):
                vals = {'email': False}
                alerta = {
                    'title': 'Atención',
                    'message': 'El correo electrónico no cumple con una estructura válida. ' + str(self.email)
                }
                return {'value': vals, 'warning': alerta}

    @api.onchange('vat')
    def _onchange_vat(self):
        if self.identification_id and self.vat:
            if self.identification_id.code == '05':
                if len(self.vat) == 0 or len(self.vat) > 20:
                    raise UserError(
                        'La identificación debe tener menos de 20 carateres.')
            else:
                # Remove leters, dashes, dots or any other special character.
                self.vat = re.sub(r"[^0-9]+", "", self.vat)
                if self.identification_id.code == '01':
                    if self.vat.isdigit() and len(self.vat) != 9:
                        raise UserError(
                            'La identificación tipo Cédula física debe de contener 9 dígitos, sin cero al inicio y sin guiones.')
                elif self.identification_id.code == '02':
                    if self.vat.isdigit() and len(self.vat) != 10:
                        raise UserError(
                            'La identificación tipo Cédula jurídica debe contener 10 dígitos, sin cero al inicio y sin guiones.')
                elif self.identification_id.code == '03' and self.vat.isdigit():
                    if self.vat.isdigit() and len(self.vat) < 11 or len(self.vat) > 12:
                        raise UserError(
                            'La identificación tipo DIMEX debe contener 11 o 12 dígitos, sin ceros al inicio y sin guiones.')
                elif self.identification_id.code == '04' and self.vat.isdigit():
                    if self.vat.isdigit() and len(self.vat) != 9:
                        raise UserError(
                            'La identificación tipo NITE debe contener 10 dígitos, sin ceros al inicio y sin guiones.')

    @api.multi
    def action_get_economic_activities(self):
        if self.vat:
            json_response = api_facturae.get_economic_activities(self)

            activities = json_response["activities"]
            activities_codes = list()
            for activity in activities:
                if activity["estado"] == "A":
                    activities_codes.append(activity["codigo"])
            economic_activities = self.env['economic.activity'].search([('code', 'in', activities_codes)])

            self.economic_activities_ids = economic_activities
            print(economic_activities)
        else:
            alert = {
                'title': 'Atención',
                'message': _('Company VAT is invalid')
            }
            return {'value': {'vat': ''}, 'warning': alert}
