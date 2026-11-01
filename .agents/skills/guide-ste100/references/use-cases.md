# Use Cases Beyond Documentation

The aerospace industry created ASD-STE100 for maintenance manuals.
The core properties transfer directly to software engineering:
- One meaning per word
- Short sentences
- Active voice
- Condition before command

Apply these rules whenever text ambiguity has an engineering or operational cost.

## Error Messages and CLI Diagnostics

Mode: Procedural.
An error message instructs a stressed operator during an outage.

Follow this three-part pattern:
1. State what happened (simple past tense).
2. State the cause if known.
3. State the imperative action to fix it.

<!-- ste-lint-disable -->
> **Before:** Oops! Something went wrong while attempting to establish a connection. Please ensure your credentials are properly configured and try again.
<!-- ste-lint-enable -->
> **After:** Connection to the database failed. The password for user `app` was not valid. Set `DB_PASSWORD` and connect again.

## Runbooks and Standard Operating Procedures (SOPs)

Mode: Strict Procedural.
An on-call runbook is an operational maintenance manual.

- Write each step as an imperative command.
- Keep one instruction per sentence.
- Place conditions before actions (`If the service fails to start, check the logs`).
- Place warnings and cautions before the step they apply to.
- Enforce the 20-word sentence limit strictly.

## Incident Reports and Postmortems

Mode: Descriptive.
Use simple past tense only.
Do not use compound tenses (`we have identified`) that hide when events occurred.

<!-- ste-lint-disable -->
> **Before:** We have identified an issue that may have impacted some users' ability to access the service.
<!-- ste-lint-enable -->
> **After:** Between 14:02 and 14:31 UTC, 12% of requests failed. A deploy at 14:00 removed the cache warmup step.

Do not use hedges (`may have impacted`).
State confirmed facts directly.
Write `unknown` when data is missing.

## Commit Messages and Pull Request Descriptions

Mode: Descriptive body, imperative summary.
Standard git hygiene already aligns with STE:
- Write the first line in the imperative mood (`fix: handle socket timeout`).
- Write the body in simple past facts.
- Remove marketing phrases (`this PR aims to seamlessly streamline`).
- Keep sentences under 25 words.

## API Changelogs and Release Notes

Mode: Descriptive.
Write one change per sentence.
For breaking changes, follow the safety instruction pattern: command first, risk second.

> **Example:** Update all client calls to `v2/users`. The `name` field is split into `first_name` and `last_name`.

## Instructions for AI Agents (Prompts, AGENTS.md, Skills)

Mode: Procedural.
A system prompt or agent skill provides instructions to an autonomous system.

- Use one instruction per sentence so rules remain independently enforceable.
- Use one word for one concept (`check`, `verify`, `validate` must not rotate).
- Put conditions before commands (`If the test fails, stop`).
- Do not use `should`. Models read `should` as optional. Write `must` or state the fact.

## Translation and Localization Preparation

Mode: Strict.
STE removes ambiguity for machine translation pipelines and non-native readers.
Do not omit articles (`a`, `an`, `the`) or conjunctions (`that`).
Complete grammatical structures prevent machine translation errors.

## UI Copy and Empty States

Mode: Procedural.
Buttons, tooltips, and empty states require extreme economy of language.

> **Example:** No projects found. Create a project to start.

## Where STE Does Not Apply

Do not apply STE to:
- Marketing pages
- Product announcements
- Advocacy writing
- Persuasive creative copy
- User-facing documentation in `docs/` (STE serves as a clarity suggestion, not a rule)

STE deliberately removes nuance, voice, and emotional appeal.
Write marketing copy in your brand voice, then apply STE to agent skills and docstrings.
