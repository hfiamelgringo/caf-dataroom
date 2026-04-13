# CLAUDE.md — CAF Innovation Strategy Dataroom

## Project Overview
Consulting engagement for **CAF** (caf.com), the Latin American development bank. We are advising them on how to build an **innovation and venture strategy for small countries in Latin America**.

The deliverable is NOT a static paper — it is an **interactive website / dataroom** designed to:
- Impress development bank executives
- Make recommendations and supporting data easily accessible
- Demonstrate our capability so CAF wants to work with us again

## Tech Stack
- **Backend:** Django (per monorepo defaults)
- **Frontend:** Custom HTML/CSS/JS following the "Architectural Institutionalism" design system (see `docs/DESIGN.md`)
- **Database:** PostgreSQL (SQLite for dev)
- **Data Sources:**
  - **Airtable** — structured data and document inventory (needs API integration)
  - **Google Drive / Google Docs** — copy and long-form content being refined collaboratively
- **Deployment:** Railway (TBD)
- **OS/Shell:** Windows 11, PowerShell

## Design System
See `docs/DESIGN.md` for the full spec. Key principles:
- **"Architectural Institutionalism"** — editorial, gallery-like, not SaaS-template
- **Fonts:** Plus Jakarta Sans (headlines), Manrope (body)
- **Palette:** Institutional Navy (#001F3F), Emerald Pulse (#9EF3D6), Neutral Surface (#F9F9FF)
- **No borders** — use tonal layering (background color shifts) for structure
- **Glassmorphism** for floating nav (70% opacity, 20px backdrop-blur)
- **Generous whitespace**, asymmetric layouts, no traditional 3-column grids

## Data Pipeline (Planned)
Content lives in Google Docs and Airtable. Options to sync to the site:
1. **Google Docs API** — pull doc content on build/deploy, render as HTML sections
2. **Airtable API** — pull structured records (frameworks, country data, recommendations)
3. **Django management commands** — `sync_airtable`, `sync_gdocs` to refresh content
4. **Hybrid:** Airtable as the "CMS index" pointing to Google Doc IDs; Django pulls both

## Key Directories
```
caf/
  docs/           # Design specs, planning docs, reference material
  CLAUDE.md       # This file — project context for Claude Code
  README.md       # Standard readme
```

## Common Commands (once scaffolded)
```powershell
conda activate caf
python manage.py runserver
python manage.py sync_airtable
python manage.py sync_gdocs
```

## Open Decisions
- [ ] Airtable base structure / API key setup
- [ ] Google Docs publishing workflow (API pull vs. export-to-markdown)
- [ ] URL structure for the dataroom
- [ ] Auth: should CAF execs need a login, or is it a private URL?
- [ ] Hosting domain (subdomain of hf.capital?)
