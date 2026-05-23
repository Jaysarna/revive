import frappe

_BYPASS_ROLES = frozenset({"System Manager", "Projects Manager"})


def _user_is_bypassed(user: str) -> bool:
	if user == "Administrator":
		return True
	return bool(_BYPASS_ROLES.intersection(frappe.get_roles(user)))


def get_permission_query_conditions(user: str, **kwargs) -> str:
	"""Return SQL WHERE fragment restricting the Task list to rows the user can access.

	Empty allowed_users = locked (only bypassed roles can see it).
	Owner always passes. Direct user match or User Group membership grants access.
	Tasks are independent — no fallback to parent Project's allowed_users.
	"""
	if not user:
		user = frappe.session.user

	if _user_is_bypassed(user):
		return ""

	escaped_user = frappe.db.escape(user)

	return f"""(
		`tabTask`.owner = {escaped_user}
		OR EXISTS (
			SELECT 1 FROM `tabRevive Access Member` ram
			WHERE ram.parent = `tabTask`.name
			AND ram.parenttype = 'Task'
			AND ram.user = {escaped_user}
		)
		OR EXISTS (
			SELECT 1 FROM `tabRevive Access Member` ram
			INNER JOIN `tabUser Group Member` ugm ON ugm.parent = ram.user_group
			WHERE ram.parent = `tabTask`.name
			AND ram.parenttype = 'Task'
			AND ugm.user = {escaped_user}
		)
	)"""


def has_permission(doc, ptype=None, user=None, **kwargs):
	"""Doc-level access check. Returns None (defer) or False (deny)."""
	if not user:
		user = frappe.session.user

	if _user_is_bypassed(user):
		return None

	if doc.owner == user:
		return None

	members = doc.get("allowed_users") or []

	if not members:
		return False

	for row in members:
		if row.get("user") == user:
			return None

	for row in members:
		group = row.get("user_group")
		if group and frappe.db.exists("User Group Member", {"parent": group, "user": user}):
			return None

	return False
