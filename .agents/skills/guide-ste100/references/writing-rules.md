# ASD-STE100 Writing Rules — Summary and Sources

This file summarizes the public, official description of ASD-STE100 (Simplified Technical English). It paraphrases rule *categories*. It does not reproduce the standard's text or its ~900-word dictionary verbatim. For the official document, request the free download at the official site.

## What ASD-STE100 Is

ASD-STE100 is a controlled natural language. ASD (the AeroSpace and
Defense Industries Association of Europe) first released the standard in 1986.
European airlines requested it for maintenance documentation that
technicians cannot misread.

A misread instruction on an aircraft can kill people. The Simplified
Technical English Maintenance Group (STEMG) maintains the standard. It is
free to download. The current edition is Issue 9 (January 2025).

## Structure

- **53 writing rules across 9 sections** covering word choice, grammar,
  sentence structure, and style.
- **A dictionary** of roughly 900 approved words. The dictionary restricts each word
  to one meaning and one part of speech. It also lists unapproved words with replacements.
- **A terminology allowance**: Organizations may define approved technical
  nouns and verbs. This covers domain-specific vocabulary beyond the base words.

## Rule Categories (Paraphrased)

**Word choice**
- Use approved words only in their approved meaning and part of speech.
- Each word maps to exactly one meaning. Do not rely on context to disambiguate a word that has several dictionary senses.
- Prefer the plainer, shorter, more common word over a formal or rare synonym.
- Use an approved verb for an action, not a noun derived from that verb (Rule 3.7).
- Do not make phrasal verbs by putting a verb and a preposition together (Rule 9.3). Their meaning is not predictable from the parts, and non-native readers and translation systems both mishandle them.

**Verb forms**
- Permitted forms: infinitive, imperative, simple present, simple past, simple future, and past participle used only as an adjective.
<!-- ste-lint-disable -->
- No present perfect, past perfect, or other compound constructions. Use "We received", never "We have received".
<!-- ste-lint-enable -->
- Use "-ing" forms only as a technical noun or as part of a technical noun, not as a verb form.

**Voice**
- Use active voice for procedures and instructions.
- Use passive voice only in descriptive text, and only when the actor performing the action is genuinely unknown or irrelevant to the reader.

**Sentence structure**
- One instruction per sentence.
- Maximum ~20 words per sentence for procedures and instructions. Maximum ~25 words for descriptive text.
- Do not omit sentence parts (verb, subject, article) just to shorten the sentence — the standard explicitly warns that this creates ambiguity rather than clarity.
- Limit noun clusters (strings of nouns stacked as a modifier) to 3 words.
- Semicolons are not permitted (Rule 8.1). Do not use the semicolon (`;`). Write separate sentences instead. Every other standard mark remains permitted.

**Paragraph and document structure**
- One topic per paragraph.
- Maximum ~6 sentences per paragraph.
- Use vertical (numbered or bulleted) lists for sequences, conditions, or complex enumerations instead of burying them in prose.

**Safety instructions**
- Safety-critical instructions must open with a clear command or condition, not be buried mid-sentence.

## Why This Skill Repurposes STE for Agent Output

AeroSpace and Defense designed STE to eliminate ambiguity for readers who cannot ask follow-up questions.
A technician on a tarmac works from a manual with no author to call.
An AI agent parsing another agent's output is in the same position.
It has no back-channel to resolve ambiguous instructions.
The same rules that protect an airline mechanic protect a downstream agent from misreading a prompt.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100 — About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe — Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English — Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe — ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary — Simplified Technical English (STE)](https://skybrary.aero/articles/simplified-technical-english-ste)
