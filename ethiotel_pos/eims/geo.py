import json
import re

import frappe
from frappe.utils import now_datetime

# MoR EIRMS device-location reporting route. Stubbed until MoR publishes the
# exact endpoint; keep it in one place so wiring it is a one-line change.
DEVICE_LOCATION_REPORT_ENDPOINT = "/v1/device/location"


def parse_polygon_wkt_or_json(raw):
    """Parse a fence as WKT POLYGON((lng lat, ...)) or a JSON [[lng, lat], ...].

    Returns a list of (lng, lat) tuples, or [] when unparseable/empty."""
    if not raw:
        return []
    text = str(raw).strip()
    wkt = re.match(r"^\s*POLYGON\s*\(\((.*?)\)\)\s*$", text, re.IGNORECASE | re.DOTALL)
    if wkt:
        coords = []
        for pair in wkt.group(1).split(","):
            parts = pair.strip().split()
            if len(parts) >= 2:
                try:
                    coords.append((float(parts[0]), float(parts[1])))
                except (TypeError, ValueError):
                    pass
        return coords
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return []
    if isinstance(data, list):
        coords = []
        for point in data:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                try:
                    coords.append((float(point[0]), float(point[1])))
                except (TypeError, ValueError):
                    pass
        return coords
    return []


def point_in_polygon(lat, lng, polygon):
    """Ray-casting point-in-polygon test. Polygon is [(lng, lat), ...].

    A missing fence or missing coordinates is treated as 'inside' (no data,
    no restriction)."""
    if not polygon or lat is None or lng is None:
        return True
    x, y = float(lng), float(lat)
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _fence_for_device(device):
    raw = None
    if device and frappe.db.exists("mPOS Device", device):
        raw = frappe.db.get_value("mPOS Device", device, "fence_polygon") or ""
    if not raw:
        raw = frappe.get_doc("EIMS Setting").get("geo_fence_polygon") or ""
    return parse_polygon_wkt_or_json(raw)


def log_geo(
    lat,
    lng,
    accuracy=None,
    device=None,
    invoice_name=None,
    invoice_type=None,
    in_fenced_area=True,
    source="Heartbeat",
):
    """Best-effort location record. Joins the caller's transaction."""
    if frappe.db.exists("DocType", "EIMS Geo Log"):
        try:
            frappe.get_doc(
                {
                    "doctype": "EIMS Geo Log",
                    "timestamp": now_datetime(),
                    "device": device,
                    "source": source,
                    "latitude": lat,
                    "longitude": lng,
                    "accuracy": accuracy,
                    "in_fenced_area": 1 if in_fenced_area else 0,
                    "invoice_type": invoice_type,
                    "invoice": invoice_name,
                }
            ).insert(ignore_permissions=True)
            frappe.db.flush()
            if device and frappe.db.exists("mPOS Device", device):
                frappe.db.set_value(
                    "mPOS Device",
                    device,
                    {
                        "last_heartbeat_at": now_datetime(),
                        "last_heartbeat_latitude": lat,
                        "last_heartbeat_longitude": lng,
                    },
                    update_modified=False,
                )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "EIMS Geo Log write failed")


@frappe.whitelist()
def log_device_location(latitude, longitude, accuracy=None, device=None):
    """Server hook for POS clients reporting periodic device heartbeats."""
    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        frappe.throw("Invalid latitude/longitude supplied.")
    fence = _fence_for_device(device)
    inside = point_in_polygon(lat, lng, fence) if fence else True
    log_geo(lat, lng, accuracy=accuracy, device=device, in_fenced_area=inside, source="Heartbeat")
    return {"status": "ok", "in_fenced_area": inside}


def enforce_geo_fence(lat, lng, device=None, invoice_name=None, invoice_type=None):
    """Block a sale whose transaction point is outside the authorized fence.

    Only applies when the EIMS Setting has geo-fence enforcement enabled AND
    the coordinates are present; otherwise it is a no-op. Art 4(5)(c)."""
    if lat is None or lng is None:
        return True
    settings = frappe.get_doc("EIMS Setting")
    if not settings.get("enforce_geo_fence"):
        return True
    polygon = _fence_for_device(device)
    if not polygon:
        return True
    inside = point_in_polygon(lat, lng, polygon)
    log_geo(
        lat,
        lng,
        device=device,
        invoice_name=invoice_name,
        invoice_type=invoice_type,
        in_fenced_area=inside,
        source="Transaction",
    )
    if not inside:
        frappe.throw(
            f"Sale location (lat {lat}, lng {lng}) is outside the authorized geo-fenced work area. "
            "EIMS compliance (Directive Art 4(5)(c)) blocks this transaction.",
            title="Geo-Fence Violation",
        )
    return inside