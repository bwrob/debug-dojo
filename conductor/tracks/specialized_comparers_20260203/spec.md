# Specification: Specialized Comparers

## Overview
Improve the `c()` (compare) helper to provide clearer, structural diffs for complex Python types, specifically `list` and `dict`. The current comparison might be too generic; this enhancement aims to show exactly *what* changed (added keys, modified indices, type changes) in a readable format.

## Requirements
- specialized comparison logic for `dict` (keys added, removed, modified).
- specialized comparison logic for `list` (items added, removed, reordered).
- visual highlighting of differences using `rich`.
- recursive comparison for nested structures.
