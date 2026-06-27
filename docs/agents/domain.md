# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This repo uses a single-context layout:

- `CONTEXT.md` at the repo root for project domain language
- `docs/adr/` at the repo root for architectural decisions

## Before exploring, read these

- `CONTEXT.md`, if it exists
- `docs/adr/`, if it exists, for decisions relevant to the area being changed

If these files do not exist, proceed silently. The domain-modeling workflow creates them lazily when terms or decisions are resolved.

## Use the glossary's vocabulary

When output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept is missing from the glossary, note it as a possible domain-modeling gap.

## Flag ADR conflicts

If output contradicts an existing ADR, surface that conflict explicitly instead of silently overriding the decision.
