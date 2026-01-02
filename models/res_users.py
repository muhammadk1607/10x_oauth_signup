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
            _logger.info("Processing company email: %s", email)

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

            # In Odoo 19, set share=False to make internal user
            values["share"] = False

        # Create user
        new_user = super()._signup_create_user(values)

        if is_company_email:
            _logger.info("Setting user %s as internal user", new_user.login)

            # Ensure share is False (internal user)
            new_user.sudo().write({"share": False})

            # Add to internal user group explicitly
            internal_group = self.env.ref("base.group_user")
            portal_group = self.env.ref("base.group_portal")

            # Update groups via SQL for reliability
            self.env.cr.execute(
                """
                DELETE FROM res_groups_users_rel
                WHERE uid = %s AND gid = %s
            """,
                (new_user.id, portal_group.id),
            )

            self.env.cr.execute(
                """
                INSERT INTO res_groups_users_rel (uid, gid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """,
                (new_user.id, internal_group.id),
            )

            # Clear cache
            new_user.invalidate_recordset()

            _logger.info(
                "User %s created as internal user (share=False)", new_user.login
            )

        return new_user
