# 12 — AI-Native Content OS
**General AI-NATIVE · Byzantine Council**

## EXECUTIVE VERDICT

AI must not be a chatbot bolted onto Grappelli. It is the content operating system: every action is a **Proposal** against typed `Displayable`/`Page` fields, never a silent publish.

Default brain: SpaceXAI / Grok. Law: provider-agnostic, citation required, deny-by-default, human publish.

## Architecture

```
Editor action / agent tool
        │
        ▼
  Ability (JSON Schema in/out, permission callback)
        │
        ▼
  Proposal (diff against typed fields + citations + model id)
        │
        ▼
  Policy (who can accept; a11y/SEO/provenance gates)
        │
        ▼
  Revision → human Publish
```

Package: `mezzanine_ai` (or product-name `_ai`).

### Models
- `Ability` — named tool, JSON Schema, permission, provider
- `Proposal` — target GFK, JSON patch, citations[], model, prompt hash, status (draft/accepted/rejected)
- `ProvenanceEvent` — who/what/when/source/model on every generated span
- `Embedding` — per Displayable, on publish
- `MigrationJob` — WP/Wix import → inferred schema → human confirm

### First-class abilities
outline, draft, rewrite, SEO fields, translate, alt-text, internal link, schema-from-brief, migrate-from-wp, site-copilot (create/move/schedule — still Proposal-gated)

### Retrieval
Search the site's own content (hybrid icontains + pgvector). Do not hallucinate the brand. If you cannot cite, do not write the sentence.

### What NOT to do
Auto-publish blogs. SEO sludge farms. Sidebar ChatGPT. Provider lock-in. Training on private campus content without a contract.

### Evals
Citation precision, schema-valid structured output rate, no-unpublished-leak, a11y-alt coverage, migrate URL fidelity.
