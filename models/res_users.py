import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        """Override to create internal users for 10xengineers.ai domain"""

        email = values.get("email")

        # Check if this is a 10xengineers.ai email
        if email and email.endswith("@10xengineers.ai"):
            _logger.info("Creating internal user for %s", email)

            # Find or create partner
            partner = self.env["res.partner"].search([("email", "=", email)], limit=1)

            if partner:
                _logger.info("Found existing partner for %s", email)
                values["partner_id"] = partner.id
            else:
                _logger.info("Creating new partner for %s", email)
                partner = self.env["res.partner"].create(
                    {
                        "name": values.get("name"),
                        "email": email,
                        "company_type": "person",
                    }
                )
                values["partner_id"] = partner.id

            # Don't set groups_id in values - it will be handled after user creation
            # Call parent to create the user
            new_user = super()._signup_create_user(values)

            # Now add internal user group
            internal_group = self.env.ref("base.group_user")
            portal_group = self.env.ref("base.group_portal")

            # Remove portal group and add internal user group
            new_user.write(
                {"groups_id": [(3, portal_group.id), (4, internal_group.id)]}
            )

            _logger.info("Successfully created internal user: %s", new_user.login)
            return new_user

        # For non-10xengineers.ai emails, use default behavior
        return super()._signup_create_user(values)
