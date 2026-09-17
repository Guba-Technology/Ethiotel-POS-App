import frappe


WORKSPACE_NAME = "Tele POS"
HIDE_LINK_LABELS = {"EIMS Manual Invoice"}


def execute():
    if not frappe.db.table_exists("Workspace"):
        return

    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        return

    workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
    changed = False
    for link in workspace.links or []:
        if link.type == "Link" and link.label in HIDE_LINK_LABELS:
            if not link.hidden:
                link.hidden = 1
                changed = True
    if changed:
        workspace.save(ignore_permissions=True)
