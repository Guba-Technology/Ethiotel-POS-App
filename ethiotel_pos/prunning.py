"""
Utility to prune Frappe/ERPNext to LITE mode.
Handles Workspace pruning, DocType metadata locking, and URL-based security.
"""
import frappe
import json
import os
from frappe.modules import reload_doc 
from frappe import _

# Configuration
ALLOWED_WORKSPACES = [
    "Home", "Selling", "Tele POS"]

HIDDEN_BY_DEFAULT = ["CRM","POS Awesome", "Quality Management", "Quality", "Projects", "Assets", "Manufacturing"]
MANIFEST_FILE = "lite_mode_lock_manifest.json"

def get_lit_modules():
    """Safely fetch Allowed Modules dynamically to avoid import-time DB errors."""
    lit_modules = [
        "Selling", "Ethio Telecom POS App", "POSAwesome","Sales and Marketing","Buying"
    ]
    try:
        # Include all core frappe modules by default
        frappe_modules = frappe.get_all("Module Def", pluck="name", filters={"app_name": "frappe"})
        lit_modules.extend(frappe_modules)
    except Exception:
        pass
    return lit_modules

def get_manifest_path():
    return os.path.join(frappe.get_site_path(), MANIFEST_FILE)

def read_manifest():
    path = get_manifest_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception: 
            return {}
    return {}

def write_manifest(data):
    path = get_manifest_path()
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

@frappe.whitelist()
def get_locked_manifest(url=None):
    """
    Returns a comprehensive list of locked components for the JS Locker.
    If the frontend sends a URL route array (e.g. ["List", "Employee", "List"]), 
    the frontend JS should check these lists to block access.
    """
    if url:
        print(f"Checking lock status against URL: {url}")
        
    data = read_manifest()
    if not data:
        return {"modules": [], "doctypes": [], "reports": [], "pages": [], "workspaces": []}
    
    all_doctypes, all_reports, all_pages, all_workspaces = [], [], [], []
    
    # Extract data securely from structured manifest
    modules_dict = data.get("modules", {})
    for mod, snapshot in modules_dict.items():
        if isinstance(snapshot, dict):
            all_doctypes.extend(snapshot.get("doctypes", []))
            all_reports.extend(snapshot.get("reports", []))
            all_pages.extend(snapshot.get("pages", []))
            all_workspaces.extend(snapshot.get("workspaces", []))

    # Add workspaces hidden independently of modules
    all_workspaces.extend(data.get("standalone_workspaces", []))

    return {
        "modules": list(modules_dict.keys()),
        "doctypes": list(set(all_doctypes)),
        "reports": list(set(all_reports)),
        "pages": list(set(all_pages)),
        "workspaces": list(set(all_workspaces))
    }

@frappe.whitelist()
def run(mode="lite"):
    is_lite = (mode == "lite")
    print(f"Switching to {mode.upper()} mode...")
    try:
        if is_lite:
            apply_lite_mode()
        else:
            restore_full_mode()
        
        frappe.clear_cache()
        print(f"Successfully updated to {mode.upper()} mode.")
        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LITE Mode Toggle Error")
        print(f"Error: {e}")
        return False

def apply_lite_mode():
    """Bulk apply Lite mode while creating snapshots."""
    manifest = read_manifest()
    if "modules" not in manifest:
        manifest["modules"] = {}
    
    allowed_modules = get_lit_modules()
    modules = frappe.get_all("Module Def", pluck="name")
    
    # 1. Handle Module Selections
    for mod in modules:
        if mod not in allowed_modules:
            toggle_module_visibility(mod, hide=True, manifest_ref=manifest)
            frappe.db.sql("DELETE FROM `tabRoute History` WHERE route LIKE %s", f"/app/{mod.lower()}%")
    for mod in allowed_modules:
        toggle_module_visibility(mod, hide=False, manifest_ref=manifest)
    # 2. Handle Workspace Visibility based on ALLOWED_WORKSPACES
    workspaces = frappe.get_all("Workspace", fields=["name", "label"])
    hidden_standalone_ws = []
    
    for ws in workspaces:
        label = ws.label or ws.name
        if label not in ALLOWED_WORKSPACES:
            frappe.db.set_value("Workspace", ws.name, "is_hidden", 1, update_modified=False)
            hidden_standalone_ws.append(ws.name)

    manifest["standalone_workspaces"] = hidden_standalone_ws
    write_manifest(manifest)

    toggle_metadata(True)

def restore_full_mode():
    """Precision restore using the manifest snapshots."""
    manifest = read_manifest()
    
    # 1. Restore modules recorded in manifest
    modules_dict = manifest.get("modules", {})
    for module_name in list(modules_dict.keys()):
        toggle_module_visibility(module_name, hide=False, manifest_ref=manifest)

    # 2. Global reset for Workspaces
    # Sets is_hidden to 0 AND public to 1 to ensure visibility in the sidebar
    frappe.db.sql("UPDATE `tabWorkspace` SET is_hidden = 0, public = 1")
    
    # 3. Clear manifest and cache
    write_manifest({"modules": {}, "standalone_workspaces": []})
    frappe.db.commit()
    frappe.clear_cache()

def toggle_module_visibility(module_name, hide=True, manifest_ref=None):
    """Selective toggle for a single module's visibility and URL security."""
    status = 1 if hide else 0
    search = 0 if hide else 1

    if frappe.db.has_column("Module Def", "disabled"):
        frappe.db.set_value("Module Def", module_name, "disabled", status)

    frappe.db.sql("UPDATE `tabDocType` SET read_only=%s, show_name_in_global_search=%s WHERE module=%s", (status, search, module_name))
    frappe.db.sql("UPDATE `tabWorkspace` SET is_hidden=%s WHERE module=%s", (status, module_name))
    
    # Sync with URL locker manifest
    should_save = False
    if manifest_ref is None:
        manifest_ref = read_manifest()
        if "modules" not in manifest_ref:
            manifest_ref["modules"] = {}
        should_save = True
        
    toggle_structure_lock(module_name, lock=hide, manifest=manifest_ref)
    
    if should_save:
        write_manifest(manifest_ref)
    
    frappe.db.commit()
    frappe.clear_cache()
    print(f"Module '{module_name}' is now {'Hidden/Locked' if hide else 'Visible/Unlocked'}.")

def toggle_structure_lock(module_name, lock=True, manifest=None):
    """Records EVERYTHING attached to a module into the manifest."""
    if lock:
        manifest["modules"][module_name] = {
            "doctypes": frappe.get_all("DocType", filters={"module": module_name}, pluck="name"),
            "reports": frappe.get_all("Report", filters={"module": module_name}, pluck="name"),
            "pages": frappe.get_all("Page", filters={"module": module_name}, pluck="name"),
            "workspaces": frappe.get_all("Workspace", filters={"module": module_name}, pluck="name")
        }
    else:
        manifest["modules"].pop(module_name, None)

def toggle_metadata(is_lite):
    status, search = (1, 0) if is_lite else (0, 1)
    lit_modules = get_lit_modules()
    
    frappe.db.sql("""UPDATE `tabDocType` SET read_only = %s, show_name_in_global_search = %s 
                     WHERE (module IN %s OR (module NOT IN %s AND %s = 1)) AND custom = 0""", 
                  (status, search, tuple(HIDDEN_BY_DEFAULT), tuple(lit_modules), status))
    frappe.db.sql("""UPDATE `tabDashboard` SET is_standard = %s WHERE module IN %s""", 
                  (0 if is_lite else 1, tuple(HIDDEN_BY_DEFAULT)))
    frappe.db.commit()

@frappe.whitelist()
def get_init_data():
    """Fetches current state based on detailed Snapshot manifest."""
    data = read_manifest()
    modules_dict = data.get("modules", {})
    all_mods = frappe.get_all("Module Def", pluck="name")
    
    locked_modules = list(modules_dict.keys())
    locked_doctypes, locked_reports, locked_pages, locked_workspaces = [], [], [], []

    for mod, snapshot in modules_dict.items():
        locked_doctypes.extend(snapshot.get("doctypes", []))
        locked_reports.extend(snapshot.get("reports", []))
        locked_pages.extend(snapshot.get("pages", []))
        locked_workspaces.extend(snapshot.get("workspaces", []))

    locked_workspaces.extend(data.get("standalone_workspaces", []))

    settings = {
        "lite_modules": [m for m in all_mods if m not in locked_modules],
        "locked_doctypes": list(set(locked_doctypes)),
        "locked_reports": list(set(locked_reports)),
        "locked_pages": list(set(locked_pages)),
        "locked_workspaces": list(set(locked_workspaces)),
        "allowed_workspaces": frappe.get_all("Workspace", filters={"label": ["in", ALLOWED_WORKSPACES]}, pluck="name")
    }

    return {
        "workspaces": frappe.get_all("Workspace", pluck="name"),
        "modules": all_mods,
        "settings": settings,
        "is_lite": 'LITE' if len(locked_modules) > 0 else 'FULL'
    }

@frappe.whitelist()
def save_settings(workspaces=None, modules=None):
    if workspaces is not None:
        frappe.db.set_global("lite_allowed_workspaces", json.dumps(workspaces))
    if modules is not None:
        frappe.db.set_global("lite_modules", json.dumps(modules))
    frappe.db.commit()
    return "Settings Saved"

@frappe.whitelist()
def get_system_summary():
    data = read_manifest()
    return {
        "hidden_workspaces": frappe.get_all("Workspace", filters={"is_hidden": 1}, pluck="name"),
        "readonly_doctypes": frappe.get_all("DocType", filters={"read_only": 1}, pluck="name"),
        "locked_modules": list(data.get("modules", {}).keys())
    }

def print_status():
    summary = get_system_summary()
    print(f"System Mode: {'LITE' if summary['locked_modules'] else 'FULL'}")
    print(f"Hidden Workspaces: {len(summary['hidden_workspaces'])}")
    print(f"Locked Modules: {len(summary['locked_modules'])}")

@frappe.whitelist()
def toggle_module_visibility_from_gui(module_name, hide):
    hide = bool(int(hide))
    toggle_module_visibility(module_name, hide)