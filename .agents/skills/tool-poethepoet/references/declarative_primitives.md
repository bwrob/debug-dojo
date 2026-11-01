# Declarative Primitives Over Bash Scripting

Before writing a `shell` task, check if a declarative Poe feature expresses the
intent portably:

| Bash Idiom | Declarative Poe Equivalent |
| :--- | :--- |
| `REGION="${REGION:-eu-west-1}"` | arg `default = "${REGION:-eu-west-1}"` |
| `if [ -z "$X" ]; then exit 1; fi` | arg `required = true` |
| `case "$X" in a\|b) ;; *) exit 1 ;; esac` | arg `choices = ["a", "b"]` |
| `case "$TARGET" in ...` | `switch` with `control.expr = "TARGET"` |
| `[ -n "$TAG" ] && ARGS="--tag $TAG"` | `${TAG:+--tag ${TAG}}` in `cmd` |
| `NAME="$(some-command)"` | `uses = { _name = "_some-task" }` |
| `source .env` / `eval "$(creds)"` | `envfile = ".env"` / `uses_env = "_creds"` |
| `step-one && step-two` | `sequence = ["step-one", "step-two"]` |
| `a & b & wait` | `parallel = ["a", "b"]` |
| `cd subdir && ...` | `cwd = "subdir"` |
| `... \|\| true` | `ignore_fail = true` |
