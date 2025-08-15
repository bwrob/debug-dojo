# Configuration

You can configure the debugging tools using a `dojo.toml` or
`pyproject.toml` file. The configuration allows you to specify which
debugger to use, enable or disable features, and set other options.

**Example `dojo.toml`:**

``` toml
[debuggers]
    default = "ipdb"

    debugpy = { port = 1992 }
    ipdb    = { context_lines = 20 }

[exceptions]
    locals_in_traceback = false
    post_mortem         = true
    rich_traceback      = true

[features]
    breakpoint   = "b"
    # Empty string means disable the feature
    comparer     = ""
    rich_inspect = "i"
    rich_print   = "p"
```
