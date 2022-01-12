# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class EducationGroup(models.Model):
    _inherit = 'education.group'

    exam_ids = fields.One2many(
        comodel_name='education.exam',
        inverse_name='group_id',
        string='Exams')
