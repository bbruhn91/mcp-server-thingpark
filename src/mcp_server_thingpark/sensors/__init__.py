"""
Auto-discovery for sensor helper modules.

Drop a .py file in this directory with a `register(mcp, send_downlink)` function
and it will be loaded automatically on server startup.
"""

import importlib
import logging
import pkgutil

log = logging.getLogger(__name__)


def load_all(mcp, send_downlink):
    """Scan this package for sensor modules and call their register() function.

    Each sensor module must define:
        def register(mcp, send_downlink):
            ...
    """
    package_path = __path__
    loaded = []

    for importer, modname, ispkg in pkgutil.iter_modules(package_path):
        if modname.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{__name__}.{modname}")
            if hasattr(module, "register"):
                module.register(mcp, send_downlink)
                loaded.append(modname)
                log.info(f"Loaded sensor module: {modname}")
            else:
                log.debug(f"Skipped {modname} (no register function)")
        except Exception as e:
            log.warning(f"Failed to load sensor module '{modname}': {e}")

    return loaded
