# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Static site for the Brain Image Library, served at `www.brainimagelibrary.org` (see `CNAME`) via GitHub Pages using Jekyll.

## Serving locally

GitHub Pages runs Jekyll on push - local preview must too, or the `_layouts/default.html` chrome (nav, footer) won't render.

```bash
# Requires Ruby 3+ (system macOS Ruby 2.6 is too old for the current ffi gem).
brew install ruby   # or use rbenv/asdf, whichever you prefer
gem install bundler jekyll
bundle install
bundle exec jekyll serve --livereload
# → http://localhost:4000
```

`python3 -m http.server` will *not* work anymore because pages depend on Jekyll to expand `layout: default` and `{% include %}` directives.

## Structure

- `_layouts/default.html` - wraps every page's `{{ content }}` with head, nav, and footer.
- `_includes/head.html` - `<head>` fragment: BS5 CSS, Bootstrap Icons, Inter, `site.css`, Google Analytics. Applied to every page.
- `_includes/nav.html` - top navbar. Edit here to change navigation for the whole site.
- `_includes/footer.html` - footer + announcement banner. Edit here to change the footer for the whole site.
- `_includes/announcements.html` - empty by default; populate + set `home_announcement: true` in the page's front matter to display.
- `_includes/stats-block.html` - landing page's headline stat panel (skeleton; `assets/js/stats.js` fills it in).
- `assets/css/site.css` - the entire custom design system. Design tokens (colors, type, spacing) live in `:root`. Component classes below.
- `assets/js/stats.js` - reads `data/stats.json` and renders the landing page's headline numbers and bar charts. Same-origin fetch.
- `data/stats.json` - generated daily by `.github/workflows/stats.yml`. Do not hand-edit; the workflow overwrites it.
- `scripts/build_stats.py` - the generator. Also runnable locally to refresh `data/stats.json`.
- `scripts/bs4_to_bs5.py` - the one-shot BS4→BS5 rewriter used during modernization. Kept in-tree in case a future page needs the same treatment.
- `scripts/convert_page.py` - helper used once to extract legacy page bodies and wrap in Jekyll front matter. Kept as reference.
- `scripts/check_links.py`, `scripts/validate_stats_schema.py`, `scripts/verify.sh` - pre-push verification.

Each `*.html` page has Jekyll front matter (`---\nlayout: default\ntitle: ...\n---`) followed by the page body. Never re-introduce a full `<html>`/`<head>`/nav-loader per page - that pattern is gone.

## Framework and dependencies

- Bootstrap 5.3.3 (pinned) - from jsDelivr, loaded in `_includes/head.html` and `_layouts/default.html`.
- Bootstrap Icons 1.11.3 - from jsDelivr.
- Inter (Google Fonts) for headings; system-ui for body.
- No jQuery. No Font Awesome. No standalone Popper (BS5 bundles it).

When editing HTML, use BS5 attribute and utility names: `data-bs-toggle`, `data-bs-target`, `.text-start` (not `.text-left`), `.ms-*` / `.me-*` (not `.ml-*` / `.mr-*`), `.form-select` (not `.custom-select`), `.visually-hidden` (not `.sr-only`), `.mb-3` (not `.form-group`). If in doubt, run:

```bash
python3 scripts/bs4_to_bs5.py path/to/file.html
```

Which applies the mechanical rewrites in-place.

## Editing content

- Change a page's copy: edit the page's `*.html` body (below the `---` front matter). Do not touch the layout.
- Change nav links: edit `_includes/nav.html`. Applies site-wide.
- Change the footer: edit `_includes/footer.html`. Applies site-wide.
- Add a homepage announcement: put the markup in `_includes/announcements.html`; set `home_announcement: true` in `index.html`'s front matter.

## Stats block

The landing page's stats are driven by `data/stats.json`, refreshed daily by `.github/workflows/stats.yml`.

- To refresh manually: `python3 scripts/build_stats.py` then commit the updated `data/stats.json`.
- To trigger the workflow now: GitHub → Actions → "Refresh stats.json" → Run workflow.
- The species merge table lives in `scripts/build_stats.py` - `SPECIES_MERGE`. Add or edit entries there.

**CORS note.** The site fetches `data/stats.json` same-origin from GitHub Pages, not from the API directly. This is because `api.brainimagelibrary.org` does not currently emit `Access-Control-Allow-Origin`. When that changes on the API side, swap `assets/js/stats.js` to fetch `https://api.brainimagelibrary.org/stats?type=all` and retire the GitHub Action.

## External services

Two subdomains host related tooling - those are separate deployments, not in this repo:

- `api.brainimagelibrary.org` - data + metadata API. `web/search.html` is iframed in the homepage hero.
- `submit.brainimagelibrary.org` - data submission portal, linked from the nav.

## Before pushing

```bash
./scripts/verify.sh
```

Runs the Jekyll build (if bundler is available), checks source pages for BS4/jQuery/Font Awesome remnants, validates the stats JSON schema, and lints the stats JS. Prints a manual visual-pass checklist at the end.
