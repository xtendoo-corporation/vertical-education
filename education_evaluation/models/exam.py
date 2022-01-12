# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class EducationExam(models.Model):
    _name = 'education.exam'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        compute='_compute_name', readonly=True)

    state = fields.Selection(
        [('draft', 'Draft'),
         ('planned', 'Planned'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        string='Status',
        default="draft")

    weight = fields.Float(
        string='Weight')

    group_id = fields.Many2one(
        comodel_name='education.group',
        string='Group',
        required=True)

    subject_id = fields.Many2one(
        comodel_name='education.subject',
        string='Subject',
        required=True)

    result_ids = fields.One2many(
        comodel_name='education.result',
        inverse_name='exam_id',
        string='Results')

    date = fields.Date(
        string='Date',
        required=True)

    grading_id = fields.Many2one(
        comodel_name='education.grading.scale',
        string='Grading',
        required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        readonly=True)

    @api.onchange('group_id')
    def _change_group_id(self):
        if not self.group_id:
            return {'domain': {'subject_id': expression.FALSE_DOMAIN}}
        subject_fields_domain = [
            ('id', 'in', self.group_id.course_id.subject_ids.mapped(
                'subject_id').ids)]
        return {'domain': {'subject_id': subject_fields_domain}}

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = record.group_id.name + \
                '/' + record.subject_id.name + '/' + record.date

    @api.multi
    def set_planned(self):
        if not len(self.group_id.enrollment_ids) > 0:
            raise ValidationError(
                _('There must be at least one student enrolled in the group'))
        self.ensure_one()
        self.state = 'planned'
        values = []
        for record_subject_group in self.group_id.enrollment_ids.mapped(
                'record_id.record_subject_ids').filtered(
                    lambda r: r.subject_id == self.subject_id).mapped(
                    'record_subject_group_ids'):
            values.append((0, 0, {
                'record_subject_group_id': record_subject_group and
                record_subject_group.id}))
        self.result_ids = values

    @api.multi
    def set_done(self):
        self.state = 'done'

    @api.multi
    def set_cancel(self):
        self.state = 'cancel'

    @api.multi
    def unlink(self):
        for record in self:
            if record.state not in ['done']:
                record.result_ids.unlink()
            else:
                raise ValidationError(
                    _('You only can delete draft and planned exams'))
        return super(EducationExam, self).unlink()
