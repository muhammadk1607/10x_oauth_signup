import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        """signup a new user using the template user"""

        email = values.get("email")

        if not email or not email.endswith("@10xengineers.ai"):
            # Not a 10xengineers.ai email, return
            return values

        # Try to find existing partner by email
        partner = self.env["res.partner"].search([("email", "=", email)], limit=1)

        if partner:
            _logger.info("Found existing partner for %s", email)
            # Partner exists, use it
            values["partner_id"] = partner.id
        else:
            _logger.info("Creating new partner for %s", email)
            # Create new partner
            partner = self.env["res.partner"].create(
                {
                    "name": values.get("name"),
                    "email": email,
                    "company_type": "person",
                }
            )
            values["partner_id"] = partner.id

        _logger.info("Creating internal user %s", values["login"])

        # Create internal user with base.group_user access
        new_user = self.env["res.users"].create(
            {
                "name": values.get("name"),
                "login": values.get("login"),
                "email": email,
                "oauth_provider_id": values.get("oauth_provider_id"),
                "oauth_uid": values.get("oauth_uid"),
                "partner_id": partner.id,
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

        return new_user
