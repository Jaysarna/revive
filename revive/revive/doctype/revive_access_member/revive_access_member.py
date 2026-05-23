import frappe
from frappe import _
from frappe.model.document import Document


class ReviveAccessMember(Document):
	def validate(self):
		if not self.user and not self.user_group:
			frappe.throw(_("Each row must specify either a User or a User Group."))
		if self.user and self.user_group:
			frappe.throw(_("Each row must specify either a User or a User Group, not both."))
