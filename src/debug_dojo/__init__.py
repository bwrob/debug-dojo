"""Debugging tools for Python.

This module provides functions to set up debugging tools like PuDB and Rich Traceback.
It checks for the availability of these tools and configures them accordingly.

Importing this module will install the debugging tools based on the configuration.
Example usage:

```python
import debug_dojo.install

b()
```

This will install the debugging tools and put debug breakpoint at this line.

Another way to use this module is to run the desired script or module with the
`dojo` command-line interface.

```console
$ dojo --verbose --config dojo.toml target_script.py --arg_1_for_script value1
```
"""
