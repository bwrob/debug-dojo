"""Install debugging tools into the current Python runtime."""

from __future__ import annotations

from debug_dojo._config_models import DojoSettings
from debug_dojo._installers import install_tools

settings: DojoSettings = DojoSettings()
config: DojoSettings = settings
install_tools(settings)
