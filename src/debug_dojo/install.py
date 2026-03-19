"""Install debugging tools based on the project configuration."""

from debug_dojo._config import load_config
from debug_dojo._installers import install_by_config

config = load_config()
install_by_config(config)
