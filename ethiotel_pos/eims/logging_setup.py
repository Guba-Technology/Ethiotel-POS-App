import logging
import os

import frappe


def get_eims_logger():
    logger = logging.getLogger("eims_connector")
    if not logger.handlers:
        log_dir = frappe.utils.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "eims_connector.log")
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # INFO by default so full request/response bodies (even redacted ones)
        # are not persisted to the debug log file in production. Set
        # eims_debug_logging=1 in site config to enable DEBUG diagnostics.
        level = logging.DEBUG if frappe.conf.get("eims_debug_logging") else logging.INFO
        logger.setLevel(level)
        logger.propagate = False
    return logger


eims_logger = get_eims_logger()
