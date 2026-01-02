import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        """Override to find/create partner and set as internal user"""
        values = super()._generate_signup_values(provider, validation, params)

        email = validation.get("email") or params.get("email")

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
                    "name": validation.get("name"),
                    "email": email,
                    "company_type": "person",
                }
            )
            values["partner_id"] = partner.id

        # Make internal user
        internal_group = self.env.ref("base.group_user")
        values["groups_id"] = [(6, 0, [internal_group.id])]

        _logger.info("Created internal user %s", values["login"])

        return values

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

        # Make internal user
        internal_group = self.env.ref("base.group_user")
        values["groups_id"] = [(6, 0, [internal_group.id])]

        _logger.info("Created internal user %s", values["login"])

        self.env["res.users"].create(values)

        partner.write({"user_id": values["id"]})
