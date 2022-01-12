
# Copyright 2017 Pesol (<http://pesol.es>)
#                Angel Moya <angel.moya@pesol.es>
#                Luis Adan Jimenez Hernandez <luis.jimenez@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.osv import expression


class EducationTimetableLine(models.Model):
    _name = 'education.timetable.line'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name', required=True, default=lambda self: _('New'))

    course_id = fields.Many2one(
        comodel_name='education.course',
        string='Course',
        required=True)

    group_id = fields.Many2one(
        comodel_name='education.group',
        string='Group',
        required=True)

    subject_id = fields.Many2one(
        comodel_name='education.subject',
        string='Subject',
        required=True)

    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        required=True)

    timerange_id = fields.Many2one(
        comodel_name='education.timerange',
        string='Time Range',
        required=True)

    day_ids = fields.Many2many(
        comodel_name='education.day',
        relation='timetable_day_rel',
        column1='timetable_id',
        column2='day_id',
        string='Days')

    date_from = fields.Date(
        string='Start Date',
        required=True)

    date_to = fields.Date(
        string='End Date',
        required=True)

    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Done')],
        string='Status',
        default='draft',
        required=True)

    session_ids = fields.One2many(
        comodel_name='education.session',
        inverse_name='timetable_id',
        string='Sessions')

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        index=True,
        track_visibility='onchange',
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)

    @api.onchange('group_id')
    def _change_group_id(self):
        if not self.group_id:
            return {'domain': {'subject_id': expression.FALSE_DOMAIN}}
        subject_fields_domain = [
            ('id', 'in', self.course_id.subject_ids.mapped('subject_id').ids)]
        return {'domain': {'subject_id': subject_fields_domain}}

    @api.multi
    def get_days(self, start, end):
        step = timedelta(days=1)
        for i in range((end - start).days + 1):
            yield start + i * step

    @api.multi
    def generate_new_sessions(self):
        self.ensure_one()
        self.state = 'done'
        session_obj = self.env['education.session']
        end = fields.Date.from_string(self.date_from)
        start = fields.Date.from_string(self.date_to)
        days = []
        day_ids_codes = []
        for code in self.day_ids:
            day_ids_codes.append(code.code)
        for day in self.get_days(end, start):
            if day.weekday() in day_ids_codes:
                days.append(day)
        for record in self:
            for day in days:
                session_obj.create({
                    'timetable_id': record.id,
                    'timerange_id': record.timerange_id.id,
                    'date': day,
                    'teacher_id': record.teacher_id.id
                })

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'education.timetable.line') or 'New'
        return super(EducationTimetableLine, self).create(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if record.mapped('session_ids').filtered(
                    lambda s: s.state in ['done']):
                raise ValidationError(
                    _('You can not remove timetable with done sessions'))
        return super(EducationTimetableLine, self).unlink()

    @api.onchange('group_id')
    def _onchange_group_id(self):
        for record in self:
            record.date_from = record.group_id.date_from
            record.date_to = record.group_id.date_to
