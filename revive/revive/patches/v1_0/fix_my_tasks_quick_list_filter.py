import frappe

NEW_FILTER = '[["Task","_assign","like",\'%"\' + frappe.session.user + \'"%\',false]]'


def execute():
	"""The 'My Tasks' Quick List on the Projects workspace was created with an
	inert filter (comparing `_assign` to null with `=`), so it effectively
	showed every Task the viewer had permission to see instead of only tasks
	assigned to them. Rewrite it to filter on the current session user,
	matching the idiom ERPNext core uses for `_assign` filters elsewhere
	(see erpnext/projects/workspace/projects/projects.json stats_filter).
	"""
	rows = frappe.get_all(
		"Workspace Quick List",
		filters={
			"parenttype": "Workspace",
			"parent": "Projects",
			"document_type": "Task",
			"label": "My Tasks",
		},
		fields=["name", "quick_list_filter"],
	)

	changed = False
	for row in rows:
		if row.quick_list_filter == NEW_FILTER:
			continue
		frappe.db.set_value(
			"Workspace Quick List",
			row.name,
			"quick_list_filter",
			NEW_FILTER,
			update_modified=False,
		)
		changed = True

	if changed:
		frappe.clear_document_cache("Workspace", "Projects")
