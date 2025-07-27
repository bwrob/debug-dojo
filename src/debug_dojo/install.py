"""Install debugging tools based on the project configuration."""

from ._config import load_config
from ._installers import install_by_config

config = load_config()
install_by_config(config)
