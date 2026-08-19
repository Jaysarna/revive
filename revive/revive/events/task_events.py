import frappe
from frappe import _
from frappe.desk.form import assign_to


def sync_allowed_users_assignment(doc, method=None):
	"""Give newly-added individual users in Task.allowed_users full assignment
	parity with clicking "Assigned To" in the UI: a ToDo, `_assign` update,
	sharing (if needed), auto-follow, and a Notification Log entry / email —
	exactly what frappe.desk.form.assign_to.add() already does.

	Only rows that set `user` (not `user_group`) trigger this. Group rows
	continue to grant read-only visibility only, via
	revive.revive.permissions.task_permissions — group membership is
	intentionally NOT expanded into individual assignments/notifications here.
	"""
	old_doc = doc.get_doc_before_save()
	old_users = {
		row.user for row in ((old_doc.get("allowed_users") if old_doc else []) or []) if row.user
	}

	new_users = [
		row.user
		for row in (doc.get("allowed_users") or [])
		if row.user and row.user not in old_users
	]

	if not new_users:
		return

	project_name = None
	if doc.project:
		project_name = frappe.db.get_value("Project", doc.project, "project_name") or doc.project

	description = _("You've been given access to Task {0}: {1}").format(
		doc.name, doc.subject or doc.name
	)
	if project_name:
		description += _(" (Project: {0})").format(project_name)
	description += ". " + _("You can now view and update this task.")

	assign_to.add(
		{
			"doctype": "Task",
			"name": doc.name,
			"assign_to": new_users,
			"description": description,
		},
		ignore_permissions=True,
	)
