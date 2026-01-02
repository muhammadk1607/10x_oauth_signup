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

        # Create user
        new_user = super()._signup_create_user(values)

        if is_company_email:
            _logger.info("Upgrading user %s to internal", new_user.login)

            # Get groups using env.ref
            internal_group = self.env.ref("base.group_user")
            portal_group = self.env.ref("base.group_portal")

            _logger.info(
                "Internal group ID: %s, Portal group ID: %s",
                internal_group.id,
                portal_group.id,
            )

            # Remove from portal
            self.env.cr.execute(
                """
                DELETE FROM res_groups_users_rel
                WHERE uid = %s AND gid = %s
            """,
                (new_user.id, portal_group.id),
            )

            # Add to internal
            self.env.cr.execute(
                """
                INSERT INTO res_groups_users_rel (uid, gid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """,
                (new_user.id, internal_group.id),
            )

            # Invalidate cache so changes are visible
            new_user.invalidate_recordset(["groups_id"])

            _logger.info("User %s upgraded to internal user", new_user.login)

        return new_user
