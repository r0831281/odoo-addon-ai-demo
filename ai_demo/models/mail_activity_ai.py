from datetime import date

from odoo import models


class CrmLeadActivityAI(models.Model):
    """Activity management methods on the CRM Lead for AI-driven planning."""
    _inherit = 'crm.lead'

    def _ai_get_open_activities(self):
        """Return all open activities on this lead."""
        self.ensure_one()
        activities = self.env['mail.activity'].sudo().search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', self.id),
        ])
        if not activities:
            return "No open activities on this lead."
        lines = []
        for act in activities:
            lines.append(
                f"- [{act.activity_type_id.name}] "
                f"{act.summary or '(no summary)'} | "
                f"Deadline: {act.date_deadline} | "
                f"Assigned: {act.user_id.display_name}"
            )
        return "Open activities:\n" + "\n".join(lines)

    def _ai_suggest_activities(self):
        """Suggest next-best activities based on lead stage and contact history."""
        self.ensure_one()
        stage = self.stage_id.name if self.stage_id else 'Unknown'
        last_msg = self.env['mail.message'].sudo().search([
            ('res_id', '=', self.id),
            ('model', '=', 'crm.lead'),
            ('message_type', 'in', ('email', 'comment', 'email_outgoing')),
        ], order='date desc', limit=1)
        last_activity = self.env['mail.activity'].sudo().search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', self.id),
        ], order='date_deadline desc', limit=1)

        today = date.today()
        days_since_contact = 'unknown'
        if last_msg and last_msg.date:
            days_since_contact = (today - last_msg.date.date()).days

        info = [
            f"Lead stage: {stage}",
            f"Days since last message: {days_since_contact}",
        ]
        if last_activity:
            info.append(
                f"Last planned activity: {last_activity.activity_type_id.name} "
                f"due {last_activity.date_deadline}"
            )
        else:
            info.append("No activities planned yet.")

        suggestions = []
        if isinstance(days_since_contact, int) and days_since_contact > 14:
            suggestions.append(
                "→ Schedule a follow-up call – no contact for over 2 weeks."
            )
        if stage in ('New', 'Qualified', 'Proposition'):
            suggestions.append(
                f"→ Send a quotation or email to advance from stage '{stage}'."
            )
        if stage == 'Won':
            suggestions.append(
                "→ Plan a customer satisfaction check-in."
            )
        if not suggestions:
            suggestions.append("→ Review current stage and decide on next contact.")

        return "\n".join(info + ["", "Suggested next steps:"] + suggestions)

    def _ai_create_activity(
        self, activity_type, summary, date_deadline,
        note=None, user_id=None
    ):
        """Create a mail.activity on this lead and return a confirmation."""
        self.ensure_one()
        type_map = {
            'call': 'Phone Call',
            'email': 'Email',
            'meeting': 'Meeting',
            'todo': 'To-Do',
        }
        type_name = type_map.get(str(activity_type).lower(), activity_type)
        act_type = self.env['mail.activity.type'].sudo().search(
            [('name', 'ilike', type_name)], limit=1
        )
        if not act_type:
            return f"Activity type '{activity_type}' not found. Available types: call, email, meeting, todo."

        self.activity_schedule(
            activity_type_id=act_type.id,
            summary=summary or '',
            date_deadline=date_deadline,
            note=note or '',
            user_id=int(user_id) if user_id else self.env.user.id,
        )
        return f"Activity '{summary}' ({type_name}) planned for {date_deadline}."
