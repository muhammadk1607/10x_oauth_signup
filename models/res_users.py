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

        self.env["res.users"].create(values)

        _logger.info("Created internal user %s", values["login"])

        partner.write({"user_id": values["id"]})

        _logger.info("Set partner user_id to %s", values["login"])
