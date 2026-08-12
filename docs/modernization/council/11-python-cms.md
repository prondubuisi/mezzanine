# 11 — Python CMS Landscape 2026
**General PYTHON-CMS · Byzantine Council**

## EXECUTIVE VERDICT

Do not modernize Mezzanine into “Wagtail but smaller.” That product exists twice (Wagtail 7.4 LTS, django CMS 5.1).

Wagtail is the Django CMS of record: custom admin, StreamField religion, Torchbox, NASA/Google/NHS. django CMS 5.1 revival is real. CodeRed CRX already occupies “Wagtail + batteries for marketing sites.”

Mezzanine’s unique slot: a *shippable Django website*, not a CMS framework. The empty cell is the product Wagtail’s Zen refuses: “not an instant website in a box.”

## How not to become Wagtail
- Stay on Django admin (modernize with HTMX), do not build a second React admin
- Content is models / relational blocks, not StreamField JSON
- Site kits, not page-type homework
- Track Django main; do not pin from above
- AI as content plane (embeddings, provenance), not an editor sidecar

## Mezzanine DNA to keep
Page/Displayable mixins, page processors, admin-editable settings, hostname multi-tenancy, `{% editable %}` contract, search-as-manager, batteries included, hackability, commerce-as-page-type.

## Positioning
Not “WordPress for Python people.” Frame: **the Django site you ship on Friday.** Relational content. Real models. Python-native intelligence.

## Revolutionary wedges Wagtail is not doing
1. Relational blocks (rows + FKs, makemigrations is the toolkit)
2. Vector plane on every Displayable
3. Provenance as a field
4. Agent/MCP native
5. Curated site kits (five that work)
6. HTMX inline editing 2.0
7. Friday-install on current Django
8. Content as data (parquet/pandas)
