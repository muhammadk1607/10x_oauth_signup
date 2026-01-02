import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        """Override to create internal users for 10xengineers.ai domain"""

        email = values.get("email")
        is_company_email = email and email.endswith("@10xengineers.ai")

        if is_company_email:
            # Find or create partner
            partner = self.env["res.partner"].search([("email", "=", email)], limit=1)
            if not partner:
                partner = self.env["res.partner"].create(
                    {
                        "name": values.get("name"),
                        "email": email,
                        "company_type": "person",
                    }
                )
            values["partner_id"] = partner.id

        # Create user (will be portal by default)
        new_user = super()._signup_create_user(values)

        if is_company_email:
            # Upgrade to internal user via direct SQL
            self._make_user_internal(new_user.id)
            _logger.info(
                "Created internal user: %s (ID: %s)", new_user.login, new_user.id
            )

        return new_user

    def _make_user_internal(self, user_id):
        """Upgrade user to internal via SQL"""
        # Get group IDs
        self.env.cr.execute(
            """
            SELECT id FROM res_groups WHERE xml_id = 'base.group_user'
        """
        )
        internal_group_result = self.env.cr.fetchone()

        self.env.cr.execute(
            """
            SELECT id FROM res_groups WHERE xml_id = 'base.group_portal'
        """
        )
        portal_group_result = self.env.cr.fetchone()

        if internal_group_result:
            internal_group_id = internal_group_result[0]

            # Add internal user group
            self.env.cr.execute(
                """
                INSERT INTO res_groups_users_rel (uid, gid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """,
                (user_id, internal_group_id),
            )

        if portal_group_result:
            portal_group_id = portal_group_result[0]

            # Remove portal group
            self.env.cr.execute(
                """
                DELETE FROM res_groups_users_rel
                WHERE uid = %s AND gid = %s
            """,
                (user_id, portal_group_id),
            )
