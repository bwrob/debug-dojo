"""Install debugging tools based on the project configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from debug_dojo._config import load_config
from debug_dojo._installers import install_by_config

if TYPE_CHECKING:
    from debug_dojo._config_models import DebugDojoConfig

config: DebugDojoConfig = load_config()
install_by_config(config)
