# Clarification Interview Matrix

This reference provides standard questions to probe for ambiguities before authoring a specification.
The requirements analyst must ask two to four targeted questions from this matrix.

---

## 1. Boundary Limits & Capacities

- What maximum payload size or batch size must the system handle?
- What timeout limits apply to external network or disk calls?
- What rate limits or request thresholds must trigger throttling?

---

## 2. Error Modalities & Recovery

- How must the system react when a required file or resource is missing?
- What specific error code or exception class must the system raise on bad input?
- If an operation fails midway, how must the system clean up partial state?

---

## 3. State Transitions & Concurrency

- Is the operation idempotent when callers invoke it multiple times with identical inputs?
- What behavior occurs when two workers access the same resource simultaneously?
- Does the system require atomic state updates or optimistic locking?

---

## 4. Backward Compatibility & Public Signatures

- Will this feature modify existing function parameters or return values?
- Must the system maintain compatibility with prior serialized configuration files?
- Are deprecation warnings required for superseded interfaces?

---

## 5. Dependency & Environment Limits

- Are new external third-party packages allowed for this feature?
- Does this feature require specific operating system capabilities?
- What minimum Python runtime version applies?

---

## 6. Explicit Out-of-Scope Limits

- What adjacent capabilities or future extensions must the developer explicitly exclude?
- Are user interface additions or command-line flags required now or deferred?
- What legacy behaviors will the team deliberately not support?
