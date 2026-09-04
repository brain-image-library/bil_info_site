# BIL Info Site — BS5 Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the static BIL info site from Bootstrap 4 + jQuery + Font Awesome 4.7 to Bootstrap 5.3 + Bootstrap Icons on Jekyll, with a custom design-token layer and a live-looking stats block on the landing page fed by a nightly GitHub Actions job.

**Architecture:** Jekyll on GitHub Pages provides shared chrome via `_layouts/default.html` + `_includes/*`. A single hand-authored `assets/css/site.css` layers BIL's palette and components on Bootstrap 5 (loaded from jsDelivr). A daily GitHub Actions workflow runs `scripts/build_stats.py`, which fetches `https://api.brainimagelibrary.org/stats?type=all`, merges duplicate species, and writes `data/stats.json`; the landing page's `assets/js/stats.js` fetches that JSON same-origin (no CORS) and renders the numbers.

**Tech Stack:** Jekyll (GH Pages native, Ruby), Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Inter font, Python 3.12 (stats + rewrite scripts), GitHub Actions.

**Spec:** [`docs/superpowers/specs/2026-08-21-bs5-modernization-design.md`](../specs/2026-08-21-bs5-modernization-design.md)

## Global Constraints

- **Do not run `git add`, `git commit`, `git push`, or any git-writing operation.** The user handles all git operations personally. Commit steps in this plan are *checkpoints* — recommendations for when the user may want to review a slice — not commands the agent runs.
- Bootstrap version pinned exactly: `bootstrap@5.3.3` from `cdn.jsdelivr.net`.
- Bootstrap Icons pinned exactly: `bootstrap-icons@1.11.3`.
- No jQuery anywhere in the final site.
- No Font Awesome anywhere in the final site.
- Only `datasets.html` may be deleted. All other pages are preserved and converted.
- Nav dropdown structure and link targets in `_includes/nav.html` must exactly match the current `menu.html` — every dropdown item, every href, every label. The nav is *restyled*, not restructured.
- `data/stats.json` is served same-origin from GH Pages; the browser fetch uses `cache: "no-store"` so daily updates are visible.
- All Jekyll paths in HTML use `{{ '/path' | relative_url }}` so the site works when hosted at either the root or a sub-path.
- Species merge table (spec §4.4) is authoritative — implementers do not adjust taxonomy without user sign-off.
- CDN pins matter: never use `@5` or `@latest`; always the pinned patch version.

---

## File Structure

**New files (created by this plan):**

```
_config.yml
Gemfile
_layouts/default.html
_includes/head.html
_includes/nav.html
_includes/footer.html
_includes/announcements.html
_includes/stats-block.html
assets/css/site.css
assets/js/stats.js
data/stats.json
scripts/build_stats.py
scripts/bs4_to_bs5.py
scripts/check_links.py
scripts/validate_stats_schema.py
scripts/verify.sh
tests/test_build_stats.py
tests/test_bs4_to_bs5.py
tests/test_check_links.py
tests/test_validate_stats_schema.py
.github/workflows/stats.yml
```

**Modified files:**
- Every `*.html` in the repo (except `datasets.html`, `menu.html`, `footer.html` which are deleted). Each page is rewritten to Jekyll front matter + BS5 body.
- `CLAUDE.md` — updated to describe the new Jekyll workflow.

**Deleted files:**
- `datasets.html` (4.6 MB orphan)
- `menu.html` (contents moved to `_includes/nav.html`)
- `footer.html` (contents moved to `_includes/footer.html`)
- `my.css` (contents folded into `assets/css/site.css`)
- `css/bootstrap.css` (BS4)
- `js/bootstrap.min.js` (BS4)
- `js/popper.min.js` (BS5 bundles Popper)
- `js/jquery.min.js` (jQuery removed)

---

## Task 1: Jekyll bootstrap and `.gitignore`

**Files:**
- Create: `_config.yml`
- Create: `Gemfile`
- Create: `.gitignore` (append to existing)
- Test: local `bundle exec jekyll build`

**Interfaces:**
- Consumes: nothing
- Produces: a working Jekyll build that outputs `_site/` containing the current HTML pages (unchanged content — the layouts don't exist yet, so Jekyll passes pages through unmodified when they have no front matter).

- [ ] **Step 1: Create `_config.yml`**

```yaml
title: Brain Image Library
description: A BRAIN Initiative data archive helping neuroscientists preserve, analyze, and share microscopy data.
url: https://www.brainimagelibrary.org
baseurl: ""

markdown: kramdown
kramdown:
  input: GFM

exclude:
  - Gemfile
  - Gemfile.lock
  - README.md
  - CLAUDE.md
  - docs/
  - scripts/
  - tests/
  - node_modules/
  - vendor/
  - .github/
  - "*.xlsx"

keep_files:
  - .nojekyll

plugins: []
```

- [ ] **Step 2: Create `Gemfile`**

```ruby
source "https://rubygems.org"

# Pin to the version GitHub Pages runs so local preview matches production.
gem "github-pages", group: :jekyll_plugins
```

- [ ] **Step 3: Append to `.gitignore`**

The existing `.gitignore` is one line (`*~`). Append the Jekyll ignores:

```
_site/
.jekyll-cache/
.jekyll-metadata
.sass-cache/
vendor/
```

- [ ] **Step 4: Install and build**

Run:
```bash
bundle install
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds. `_site/` directory now exists and contains a copy of every current HTML file (Jekyll passes files without front matter through unchanged).

- [ ] **Step 5: Verify local serve works**

Run:
```bash
bundle exec jekyll serve --livereload
```
Open `http://localhost:4000` in a browser. Expected: current site renders identically to how it does today (still Bootstrap 4, still jQuery-loaded nav — this task changes nothing user-visible).
Stop with Ctrl-C.

- [ ] **Step 6: Checkpoint (user commits when ready)**

Suggested commit message: `chore: bootstrap Jekyll build (no user-visible change)`

---

## Task 2: Design tokens CSS

**Files:**
- Create: `assets/css/site.css`

**Interfaces:**
- Consumes: nothing
- Produces: `assets/css/site.css` containing `:root` design tokens and a base reset. Loaded by every page via `_includes/head.html` (Task 4). Component classes are added later in Task 8.

- [ ] **Step 1: Create `assets/css/site.css` with tokens and base**

```css
/* BIL design tokens. Change values here; every component uses these vars. */
:root {
  /* Palette */
  --bil-primary:      #1f6fb2;
  --bil-primary-hov:  #185891;
  --bil-primary-deep: #0f2f4c;
  --bil-accent:       #14b8a6;
  --bil-ink:          #132030;
  --bil-ink-soft:     #4a5b6e;
  --bil-muted:        #8496a6;
  --bil-line:         #e4ebf1;
  --bil-surface:      #ffffff;
  --bil-surface-2:    #f5f8fb;

  /* Bootstrap 5 theme overrides — palette flows into BS components */
  --bs-primary:       var(--bil-primary);
  --bs-primary-rgb:   31, 111, 178;
  --bs-body-color:    var(--bil-ink);
  --bs-body-color-rgb: 19, 32, 48;
  --bs-body-bg:       var(--bil-surface);
  --bs-border-color:  var(--bil-line);
  --bs-link-color:    var(--bil-primary);
  --bs-link-hover-color: var(--bil-primary-hov);

  /* Type scale */
  --fs-100: 12.5px; --fs-200: 14px; --fs-300: 16px; --fs-400: 18px;
  --fs-500: 22px;   --fs-600: 28px; --fs-700: 36px; --fs-800: 44px;

  /* Spacing scale */
  --sp-1: 4px; --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;

  /* Radii, shadows */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-xl: 20px;
  --shadow-card: 0 20px 50px -30px rgba(20, 28, 45, .3);
  --shadow-hero: 0 20px 50px -30px rgba(20, 28, 45, .4);

  /* Type families */
  --font-heading: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-body:    system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif;
}

/* Base */
html { -webkit-text-size-adjust: 100%; }
body {
  font-family: var(--font-body);
  font-size: var(--fs-300);
  line-height: 1.55;
  color: var(--bil-ink);
  background-color: var(--bil-surface);
}
h1, h2, h3, h4 {
  font-family: var(--font-heading);
  font-weight: 800;
  letter-spacing: -.02em;
  color: var(--bil-ink);
}
a { color: var(--bil-primary); text-decoration: none; }
a:hover { color: var(--bil-primary-hov); text-decoration: underline; }

.eyebrow {
  font-size: var(--fs-100);
  font-weight: 700;
  letter-spacing: .11em;
  text-transform: uppercase;
  color: var(--bil-primary);
}
```

- [ ] **Step 2: Verify build still succeeds**

Run:
```bash
bundle exec jekyll build
ls _site/assets/css/site.css
```
Expected: file is present in `_site/`. No layout task yet references it — that's fine, it just sits there.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat(css): add design tokens and base typography`

---

## Task 3: Default layout skeleton

**Files:**
- Create: `_layouts/default.html`

**Interfaces:**
- Consumes: `_includes/head.html`, `_includes/nav.html`, `_includes/footer.html` (created in Tasks 4-6). Those includes must not error when empty — Jekyll tolerates empty include files.
- Produces: A layout named `default` that pages can select with `layout: default` in their front matter. Renders `{{ content }}` (page body) surrounded by nav and footer.

- [ ] **Step 1: Create the three include files as empty placeholders**

This unblocks Task 3 — Jekyll would fail if `default.html` referenced non-existent includes.

```bash
mkdir -p _includes _layouts
: > _includes/head.html
: > _includes/nav.html
: > _includes/footer.html
: > _includes/announcements.html
```

- [ ] **Step 2: Create `_layouts/default.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="x-ua-compatible" content="ie=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if page.title %}{{ page.title }} · {{ site.title }}{% else %}{{ site.title }}{% endif %}</title>
  {% if page.description %}<meta name="description" content="{{ page.description }}">{% else %}<meta name="description" content="{{ site.description }}">{% endif %}
  {% include head.html %}
</head>
<body>
  {% include nav.html %}
  <main id="content">
    {{ content }}
  </main>
  {% include footer.html %}
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{{ '/assets/js/stats.js' | relative_url }}" defer></script>
</body>
</html>
```

- [ ] **Step 3: Verify build**

Run:
```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds. No page uses this layout yet, so nothing user-visible changes.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `feat(layout): add default Jekyll layout skeleton`

---

## Task 4: `_includes/head.html`

**Files:**
- Modify: `_includes/head.html` (populate from empty placeholder)

**Interfaces:**
- Consumes: `assets/css/site.css` (Task 2), Bootstrap 5 CDN, Bootstrap Icons CDN, Google Fonts.
- Produces: A `<head>` fragment loaded on every page. Provides BS5 CSS, Bootstrap Icons CSS, Inter font, `site.css`, favicon, Google Analytics.

- [ ] **Step 1: Populate `_includes/head.html`**

```html
<link rel="icon" href="{{ '/assets/BIL_logo.png' | relative_url }}">

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap">
<link rel="stylesheet" href="{{ '/assets/css/site.css' | relative_url }}">

<!-- Google Analytics (moved from index.html to fire on every page) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-R1YK9CG4GL"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-R1YK9CG4GL');
</script>
```

- [ ] **Step 2: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
grep -q "bootstrap@5.3.3" _site/index.html || echo "WARN: no page uses layout yet, so head.html won't render — that's expected at this task."
```
Expected: build succeeds. `head.html` is not yet applied because no page has front matter selecting the layout.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat(layout): head include with BS5, Bootstrap Icons, Inter, analytics`

---

## Task 5: `_includes/nav.html`

**Files:**
- Modify: `_includes/nav.html`
- Reference: existing `menu.html` (source of dropdown structure and hrefs — do not deviate)

**Interfaces:**
- Consumes: BS5 dropdowns loaded via `bootstrap.bundle.min.js` from the layout.
- Produces: A dark topbar with a logo and dropdown-driven primary nav. Exact same dropdown items and hrefs as today's `menu.html`.

**Notes:**
- Every dropdown item's `href` must match today's `menu.html` verbatim.
- `data-toggle` becomes `data-bs-toggle`; `data-target` becomes `data-bs-target`.
- The `.navbar-toggler-icon` in BS4 was a background-image sprite; BS5 has the same class and it works. Keep it.
- The hamburger icon `fa fa-bars` from the current `menu.html` is not present in `menu.html` today (spec grep confirms only `fa fa-bars` is the site's only Font Awesome usage, and it isn't in `menu.html`). If found during implementation, replace with `<i class="bi bi-list"></i>`.

- [ ] **Step 1: Populate `_includes/nav.html`**

```html
<header class="topbar">
  <div class="topbar-in">
    <a class="logo" href="{{ '/' | relative_url }}">
      <img src="{{ '/assets/brainicon.png' | relative_url }}" alt="" height="30">
      <span>Brain Image Library</span>
    </a>

    <nav class="navbar navbar-expand-lg topbar-nav" aria-label="Primary">
      <button class="navbar-toggler" type="button"
              data-bs-toggle="collapse" data-bs-target="#bilPrimaryNav"
              aria-controls="bilPrimaryNav" aria-expanded="false"
              aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="bilPrimaryNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button"
               data-bs-toggle="dropdown" aria-expanded="false">About</a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="{{ '/about.html' | relative_url }}">About BIL</a></li>
              <li><a class="dropdown-item" href="{{ '/people.html' | relative_url }}">BIL Staff</a></li>
              <li><a class="dropdown-item" href="{{ '/partners.html' | relative_url }}">Partners</a></li>
              <li><a class="dropdown-item" href="{{ '/braindataarchives.html' | relative_url }}">BRAIN Initiative Data Archives</a></li>
            </ul>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button"
               data-bs-toggle="dropdown" aria-expanded="false">Data Submission</a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="{{ '/datarequirements.html' | relative_url }}">Data Depositor FAQ</a></li>
              <li><a class="dropdown-item" href="{{ '/submission.html' | relative_url }}">Instructions</a></li>
              <li><a class="dropdown-item" href="{{ '/account.html' | relative_url }}">Create Account</a></li>
              <li><a class="dropdown-item" href="{{ '/datadirbp.html' | relative_url }}">Submission Best Practices</a></li>
              <li><a class="dropdown-item" href="https://submit.brainimagelibrary.org/">Data Submission Portal</a></li>
              <li><a class="dropdown-item" href="{{ '/newmetadatamodel.html' | relative_url }}">Metadata Model</a></li>
              <li><a class="dropdown-item" href="{{ '/training.html' | relative_url }}">Training</a></li>
            </ul>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button"
               data-bs-toggle="dropdown" aria-expanded="false">Data Access</a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="https://api.brainimagelibrary.org/web">Search Brain Inventory</a></li>
              <li><a class="dropdown-item" href="{{ '/download.html' | relative_url }}">Downloading Data</a></li>
              <li><a class="dropdown-item" href="{{ '/identifiers.html' | relative_url }}">BIL Identifiers</a></li>
              <li><a class="dropdown-item" href="{{ '/computevisual.html' | relative_url }}">Computing and Visualization</a></li>
              <li><a class="dropdown-item" href="{{ '/visual.html' | relative_url }}">Web Visualization</a></li>
              <li><a class="dropdown-item" href="{{ '/analysis_ecosystem.html' | relative_url }}">Analysis Ecosystem</a></li>
              <li><a class="dropdown-item" href="{{ '/restrictedaccess.html' | relative_url }}">Restricted Data</a></li>
              <li><a class="dropdown-item" href="{{ '/metadataapi.html' | relative_url }}">Metadata API</a></li>
              <li><a class="dropdown-item" href="{{ '/citation.html' | relative_url }}">Citing Data</a></li>
            </ul>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="{{ '/contact.html' | relative_url }}">Contact</a>
          </li>
        </ul>
      </div>
    </nav>
  </div>
</header>
```

- [ ] **Step 2: Add topbar styles to `assets/css/site.css`**

Append:
```css
/* Topbar */
.topbar { background: var(--bil-primary-deep); }
.topbar-in {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: var(--sp-5);
  padding: var(--sp-3) var(--sp-6);
}
.logo {
  display: flex; align-items: center; gap: var(--sp-2);
  color: #fff; font-family: var(--font-heading);
  font-weight: 800; font-size: var(--fs-400); letter-spacing: -.01em;
}
.logo:hover { color: #fff; text-decoration: none; }
.logo img { display: block; height: 30px; width: auto; }

.topbar-nav { padding: 0; margin-left: auto; }
.topbar-nav .nav-link,
.topbar-nav .navbar-toggler {
  color: #cfe0ef; font-size: var(--fs-200); font-weight: 600;
}
.topbar-nav .nav-link:hover { color: #fff; }
.topbar-nav .dropdown-menu {
  border: 1px solid var(--bil-line);
  box-shadow: var(--shadow-card);
  border-radius: var(--radius-md);
  padding: var(--sp-2);
}
.topbar-nav .dropdown-item {
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--fs-200);
}
.topbar-nav .dropdown-item:hover {
  background: var(--bil-surface-2);
  color: var(--bil-primary);
}
```

- [ ] **Step 3: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `feat(nav): topbar include mirroring current menu.html links`

---

## Task 6: `_includes/footer.html` and `_includes/announcements.html`

**Files:**
- Modify: `_includes/footer.html`
- Modify: `_includes/announcements.html`
- Reference: existing `footer.html`, `menu.html` (announcement banner text), `index.html` (RRID line)

**Interfaces:**
- Consumes: nothing
- Produces: A footer fragment rendered on every page. Announcements include is empty by default and only rendered on pages that opt in via `home_announcement: true` front matter.

- [ ] **Step 1: Populate `_includes/announcements.html`**

Leave the file empty. When there is an announcement to make, its markup goes here.

- [ ] **Step 2: Populate `_includes/footer.html`**

```html
{% if page.home_announcement %}
  {% include announcements.html %}
{% endif %}

<footer class="site-footer">
  <div class="site-footer-in">
    <p class="site-footer-lead">
      The Brain Image Library is a BRAIN Initiative data archive that helps
      neuroscientists preserve, analyze, and share their microscopy data.
    </p>
    <p class="site-footer-support">
      Supported by the National Institutes of Mental Health of the National
      Institutes of Health under award number R24-MH-114793. The content is
      solely the responsibility of the authors and does not necessarily
      represent the official views of the National Institutes of Health.
    </p>
    <p class="site-footer-rrid">Brain Image Library · RRID:SCR_017272</p>
    <div class="announcement">
      This repository is under review for potential modification in
      compliance with Administration directives.
    </div>
  </div>
</footer>
```

- [ ] **Step 3: Add footer styles to `assets/css/site.css`**

Append:
```css
/* Footer */
.site-footer {
  background: var(--bil-primary-deep);
  color: #cfe0ef;
  padding: var(--sp-6) 0;
  margin-top: var(--sp-8);
}
.site-footer-in {
  max-width: 1080px; margin: 0 auto; padding: 0 var(--sp-6);
  display: flex; flex-direction: column; gap: var(--sp-3);
}
.site-footer p { margin: 0; font-size: var(--fs-200); line-height: 1.6; }
.site-footer-rrid { font-weight: 600; color: #fff; }

.announcement {
  margin-top: var(--sp-3);
  background: #fff8e1;
  color: #614a12;
  border: 1px solid #e6d38c;
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--fs-200);
}
```

- [ ] **Step 4: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds.

- [ ] **Step 5: Checkpoint**

Suggested commit message: `feat(footer): footer include with grant text, RRID, and announcement banner`

---

## Task 7: Smoke-test the layout on `contact.html`

**Files:**
- Modify: `contact.html`

**Interfaces:**
- Consumes: `_layouts/default.html`, `_includes/head.html`, `_includes/nav.html`, `_includes/footer.html`.
- Produces: `contact.html` becomes the first page using the new layout. Proves nav, footer, tokens all wire together before we convert the other 34.

- [ ] **Step 1: Read the current `contact.html` body**

Identify the content between the closing of the `topmenu` block/jQuery load and the opening of the `bottomfooter` block. That's the page body to preserve.

- [ ] **Step 2: Rewrite `contact.html`**

Replace the entire file contents with front matter + body only:

```html
---
layout: default
title: Contact
description: How to contact the Brain Image Library team.
---

<div class="container my-5">
  <header class="mb-4">
    <div class="eyebrow">Contact</div>
    <h1 class="mb-2">Contact BIL</h1>
    <p class="text-secondary">Reach out about data, accounts, or the archive.</p>
  </header>

  <!-- Preserve the page body from the original contact.html here. -->
  <!-- Apply mechanical BS4→BS5 rewrites: text-left → text-start, ml-* → ms-*, etc. -->
  <!-- Keep every link href, every email address, every phrasing. -->
</div>
```

Then paste the *body content only* (contact info, addresses, emails) from the current `contact.html` into the `<div class="container my-5">` block, applying mechanical BS4→BS5 class rewrites as you go.

- [ ] **Step 3: Verify build + render**

```bash
bundle exec jekyll serve --livereload
```
Open `http://localhost:4000/contact.html`. Expected:
- Topbar visible at top with BIL logo and nav dropdowns
- Contact content in the middle
- Footer at bottom with grant text, RRID, announcement banner
- No console errors in browser devtools

Stop the server.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `feat: convert contact.html to Jekyll layout (smoke test)`

---

## Task 8: Full component CSS

**Files:**
- Modify: `assets/css/site.css` (append)

**Interfaces:**
- Consumes: tokens defined in Task 2.
- Produces: All the reusable component classes referenced by later tasks: `.hero`, `.stat-grid`, `.stat`, `.bar-list`, `.bar-row`, `.bar-track`, `.bar-fill`, `.content-card`, `.section-eyebrow`, `.section-title`, `.section-sub`, `.feature-grid`, `.feature-card`.

- [ ] **Step 1: Append component styles**

```css
/* Hero */
.hero {
  padding: var(--sp-7) 0 var(--sp-6);
}
.hero .container-hero {
  max-width: 1080px; margin: 0 auto; padding: 0 var(--sp-6);
  display: grid; grid-template-columns: 1.05fr .95fr;
  gap: var(--sp-6); align-items: center;
}
@media (max-width: 900px) {
  .hero .container-hero { grid-template-columns: 1fr; }
}
.hero-title {
  font-size: var(--fs-800);
  line-height: 1.06;
  margin: var(--sp-3) 0 0;
}
.hero-lead {
  font-size: var(--fs-400);
  color: var(--bil-ink-soft);
  line-height: 1.55;
  margin: var(--sp-4) 0 0;
  max-width: 480px;
}
.hero-cta { margin-top: var(--sp-5); display: flex; gap: var(--sp-3); flex-wrap: wrap; }
.hero-search { margin-top: var(--sp-5); }

/* Stat grid */
.stat-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: var(--bil-line);
  border: 1px solid var(--bil-line);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-hero);
}
.stat {
  background: var(--bil-surface);
  padding: var(--sp-5) var(--sp-4);
}
.stat-v {
  font-size: var(--fs-700);
  font-weight: 800;
  letter-spacing: -.02em;
  line-height: 1;
  color: var(--bil-ink);
  font-variant-numeric: tabular-nums;
}
.stat-v small {
  font-size: var(--fs-400);
  font-weight: 700;
  color: var(--bil-primary);
  margin-left: 1px;
}
.stat-k {
  font-size: var(--fs-100);
  color: var(--bil-ink-soft);
  margin-top: var(--sp-2);
  font-weight: 500;
}

/* Bar list (species, modalities) */
.bar-list { display: flex; flex-direction: column; gap: var(--sp-2); }
.bar-row {
  display: grid;
  grid-template-columns: 200px 1fr auto;
  align-items: center;
  gap: var(--sp-3);
}
@media (max-width: 600px) {
  .bar-row { grid-template-columns: 1fr; gap: var(--sp-1); }
}
.bar-name { font-size: var(--fs-100); font-weight: 600; text-align: right; }
.bar-track {
  height: 16px;
  background: var(--bil-surface-2);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  min-width: 4px;
  background: linear-gradient(90deg, var(--bil-primary), #3a93cf);
}
.bar-count {
  font-size: var(--fs-100);
  color: var(--bil-ink-soft);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  min-width: 52px;
  text-align: right;
}

/* Content card (wraps long-form pages) */
.content-card {
  background: var(--bil-surface);
  border: 1px solid var(--bil-line);
  border-radius: var(--radius-xl);
  padding: var(--sp-6) var(--sp-6);
  box-shadow: var(--shadow-card);
  max-width: 900px;
  margin: 0 auto;
}
.content-card h2 { font-size: var(--fs-500); margin-top: var(--sp-5); }
.content-card h2:first-child { margin-top: 0; }

/* Section headings (shared across cards) */
.section-eyebrow { font-size: var(--fs-100); font-weight: 700; letter-spacing: .11em;
  text-transform: uppercase; color: var(--bil-primary); }
.section-title   { font-size: var(--fs-500); font-weight: 800; letter-spacing: -.02em;
  margin: 0; }
.section-sub     { font-size: var(--fs-200); color: var(--bil-ink-soft);
  margin: var(--sp-2) 0 0; line-height: 1.5; }

/* Feature grid (replaces homepage carousel) */
.feature-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--sp-4);
}
@media (max-width: 780px) { .feature-grid { grid-template-columns: 1fr; } }
.feature-card {
  background: var(--bil-surface);
  border: 1px solid var(--bil-line);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.feature-card img { display: block; width: 100%; height: auto; }
.feature-card-body { padding: var(--sp-4); }
.feature-card-caption {
  font-size: var(--fs-200); color: var(--bil-ink-soft); margin: 0;
}

/* Buttons — BS5 primary styling with our palette */
.btn-primary,
.btn-primary:focus {
  background-color: var(--bil-primary);
  border-color: var(--bil-primary);
}
.btn-primary:hover {
  background-color: var(--bil-primary-hov);
  border-color: var(--bil-primary-hov);
}

/* Unavailable state for stats block */
.bil-stats--unavailable .bar-list,
.bil-stats--unavailable .stat-grid { display: none; }
.bil-stats--unavailable .bil-stats-unavailable-msg { display: block; }
.bil-stats-unavailable-msg {
  display: none;
  padding: var(--sp-4);
  color: var(--bil-ink-soft);
  font-size: var(--fs-200);
}
```

- [ ] **Step 2: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat(css): hero, stat-grid, bar-list, content-card, feature-grid components`

---

## Task 9: `scripts/build_stats.py` — tests first, then implementation

**Files:**
- Create: `tests/test_build_stats.py`
- Create: `scripts/build_stats.py`

**Interfaces:**
- Consumes: `https://api.brainimagelibrary.org/stats?type=all` (public HTTP endpoint).
- Produces: `data/stats.json` with the schema from spec §4.3. Exit codes: 0 on success, 1 on API/network failure, 2 on schema violation from the endpoint. The GitHub Action (Task 14) invokes this script.

- [ ] **Step 1: Set up Python test infrastructure**

Create `tests/__init__.py` (empty) and `scripts/__init__.py` (empty). Add `pytest` and `requests` to development dependencies. If the repo has no pyproject/requirements files yet, add a minimal `requirements-dev.txt`:

```
pytest>=8.0
requests>=2.31
beautifulsoup4>=4.12
```

Then:
```bash
pip install -r requirements-dev.txt
```

- [ ] **Step 2: Write the failing test — species merge**

Create `tests/test_build_stats.py`:

```python
from scripts.build_stats import merge_species, filter_modalities, build_output


def test_merge_species_combines_synonyms():
    raw = [
        {"name": "human", "count": 100},
        {"name": "homo sapiens", "count": 50},
        {"name": "mouse", "count": 10000},
        {"name": "rat", "count": 200},
    ]
    merged = merge_species(raw)
    by_name = {row["name"]: row["count"] for row in merged}
    assert by_name["Human"] == 150
    assert by_name["Mouse"] == 10000
    assert by_name["Rat"] == 200
    assert "human" not in by_name and "homo sapiens" not in by_name


def test_merge_species_passthrough_unknown():
    raw = [{"name": "wombat", "count": 5}]
    merged = merge_species(raw)
    assert merged == [{"name": "Wombat", "count": 5}]


def test_merge_species_sorts_descending():
    raw = [
        {"name": "rat", "count": 10},
        {"name": "mouse", "count": 100},
        {"name": "human", "count": 50},
    ]
    merged = merge_species(raw)
    counts = [row["count"] for row in merged]
    assert counts == sorted(counts, reverse=True)


def test_filter_modalities_drops_na_and_zero():
    raw = [
        {"name": "cell morphology", "count": 5282},
        {"name": "#N/A", "count": 5},
        {"name": "morphology", "count": 0},
    ]
    filtered = filter_modalities(raw)
    names = [row["name"] for row in filtered]
    assert "#N/A" not in names
    assert "morphology" not in [n.lower() for n in names]
    assert "Cell morphology" in names


def test_build_output_shape():
    endpoint = {
        "dataset_count": 14225,
        "species": [{"name": "mouse", "count": 10000}, {"name": "human", "count": 100}],
        "modalities": [{"name": "cell morphology", "count": 5000}],
        "consortiums": [{"label": "BICCN", "value": "BICCN", "count": 10000}],
    }
    out = build_output(endpoint, generated_at="2026-08-21T06:00:00Z")
    assert out["generated_at"] == "2026-08-21T06:00:00Z"
    assert out["source"] == "https://api.brainimagelibrary.org/stats?type=all"
    assert out["headline"]["datasets"] == 14225
    assert out["headline"]["consortia"] == 1
    assert out["headline"]["species"] == len(out["species"])
    assert out["headline"]["modalities"] == len(out["modalities"])
    assert out["species"][0]["name"] == "Mouse"
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
pytest tests/test_build_stats.py -v
```
Expected: `ImportError` — `scripts.build_stats` doesn't exist yet.

- [ ] **Step 4: Implement `scripts/build_stats.py`**

```python
"""Fetch BIL /stats?type=all, normalize, write data/stats.json.

Run locally: python3 scripts/build_stats.py
Called by:   .github/workflows/stats.yml (daily)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.brainimagelibrary.org/stats?type=all"
TIMEOUT = 15
OUTPUT_PATH = Path("data/stats.json")

# Canonical display name -> list of lowercase raw endpoint names to fold in.
SPECIES_MERGE: dict[str, list[str]] = {
    "Mouse":                 ["mouse"],
    "Human":                 ["human", "homo sapiens"],
    "Rhesus macaque":        ["rhesus macaque", "macaca mulatta"],
    "Pig-tailed macaque":    ["pig-tailed macaque", "macaca nemestrina"],
    "Common marmoset":       ["common marmoset", "marmoset"],
    "Crab-eating macaque":   ["crab-eating macaque"],
    "Squirrel monkey":       ["saimiri sciureus", "squirrel monkey"],
    "Macaque (unspecified)": ["macaque"],
    "Rat":                   ["rat"],
    "Fruit fly":             ["fruit fly"],
    "Clonal raider ant":     ["clonal raider ant", "ooceraea biroi"],
    "Zebrafish":             ["zebrafish"],
    "Sea squirt":            ["ciona robusta"],
    "Spider":                ["spider", "feather-legged spider"],
}


def _lookup_canonical(raw_name: str) -> str | None:
    """Return the canonical display name if `raw_name` matches any merge entry."""
    raw_lower = raw_name.strip().lower()
    for canonical, aliases in SPECIES_MERGE.items():
        if raw_lower in aliases:
            return canonical
    return None


def merge_species(raw: list[dict]) -> list[dict]:
    """Fold synonyms per SPECIES_MERGE; unknown names pass through title-cased.

    Returns rows sorted by count descending.
    """
    totals: dict[str, int] = {}
    for row in raw:
        name = row["name"]
        count = int(row["count"])
        canonical = _lookup_canonical(name)
        if canonical is None:
            # Unknown — pass through with title-case, log to stdout.
            display = name.strip().title()
            print(f"NOTE: species '{name}' not in SPECIES_MERGE; passing through as '{display}'", file=sys.stderr)
        else:
            display = canonical
        totals[display] = totals.get(display, 0) + count

    merged = [{"name": name, "count": count} for name, count in totals.items()]
    merged.sort(key=lambda r: r["count"], reverse=True)
    return merged


def filter_modalities(raw: list[dict]) -> list[dict]:
    """Drop `#N/A` and zero-count entries; title-case names; sort descending."""
    result = []
    for row in raw:
        name = row["name"].strip()
        count = int(row["count"])
        if name == "#N/A" or count == 0:
            continue
        result.append({"name": name[:1].upper() + name[1:], "count": count})
    result.sort(key=lambda r: r["count"], reverse=True)
    return result


def build_output(endpoint: dict, *, generated_at: str) -> dict:
    """Compose the final data/stats.json document."""
    species = merge_species(endpoint["species"])
    modalities = filter_modalities(endpoint["modalities"])
    consortia = endpoint["consortiums"]  # spelling: endpoint uses "consortiums"
    return {
        "generated_at": generated_at,
        "source": API_URL,
        "headline": {
            "datasets":   int(endpoint["dataset_count"]),
            "consortia":  len(consortia),
            "species":    len(species),
            "modalities": len(modalities),
        },
        "species":    species,
        "modalities": modalities,
        "consortia":  consortia,
    }


def _validate_endpoint_shape(payload: dict) -> None:
    """Raise if the endpoint payload is missing required keys."""
    required = {"dataset_count", "species", "modalities", "consortiums"}
    missing = required - set(payload)
    if missing:
        raise SystemExit(2)


def main() -> int:
    try:
        r = requests.get(API_URL, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        return 1

    try:
        payload = r.json()
    except ValueError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    _validate_endpoint_shape(payload)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = build_output(payload, generated_at=generated_at)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, OUTPUT_PATH)
    print(f"OK: wrote {OUTPUT_PATH} (datasets={out['headline']['datasets']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_build_stats.py -v
```
Expected: all five tests pass.

- [ ] **Step 6: Checkpoint**

Suggested commit message: `feat(stats): build_stats.py with species merge and modality filter`

---

## Task 10: Seed the initial `data/stats.json`

**Files:**
- Create: `data/stats.json` (by running the script)

**Interfaces:**
- Consumes: live API endpoint.
- Produces: initial committed `data/stats.json` so the site works immediately on merge (before the daily workflow's first run).

- [ ] **Step 1: Run the script locally**

```bash
python3 scripts/build_stats.py
```
Expected: exits 0, prints "OK: wrote data/stats.json (datasets=NNNNN)". Any species merge warnings go to stderr.

- [ ] **Step 2: Verify the output**

```bash
cat data/stats.json | python3 -m json.tool | head -40
```
Expected: valid JSON matching the schema in spec §4.3.

- [ ] **Step 3: Sanity-check the merge decisions**

Review the stderr from Step 1 — any species names that hit the "pass through" branch are candidates for adding to `SPECIES_MERGE`. Flag any surprises to the user before finalizing.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `data: seed initial stats.json`

---

## Task 11: `_includes/stats-block.html` and `assets/js/stats.js`

**Files:**
- Modify: `_includes/stats-block.html` (create real content — currently empty from Task 3)
- Create: `assets/js/stats.js`

**Interfaces:**
- Consumes: `data/stats.json` (via fetch), CSS classes from Task 8.
- Produces: An include renderable on any page. When present in a page, the JS populates it from JSON on `DOMContentLoaded`.

- [ ] **Step 1: Populate `_includes/stats-block.html`**

```html
<section id="bil-stats" class="bil-stats" aria-live="polite">
  <div class="stat-grid" id="bil-stat-grid">
    <div class="stat"><div class="stat-v" data-stat="datasets">—</div><div class="stat-k">Datasets</div></div>
    <div class="stat"><div class="stat-v" data-stat="species">—</div><div class="stat-k">Species imaged</div></div>
    <div class="stat"><div class="stat-v" data-stat="modalities">—</div><div class="stat-k">Modalities</div></div>
    <div class="stat"><div class="stat-v" data-stat="consortia">—</div><div class="stat-k">Consortia</div></div>
  </div>

  <div class="row g-4 mt-4">
    <div class="col-lg-6">
      <div class="content-card">
        <div class="section-eyebrow">Distribution</div>
        <h2 class="section-title">Datasets by species</h2>
        <p class="section-sub">Common names, sorted by dataset count. Synonyms are merged in the archive index.</p>
        <div class="bar-list mt-3" id="bil-species-bars"></div>
      </div>
    </div>
    <div class="col-lg-6">
      <div class="content-card">
        <div class="section-eyebrow">Distribution</div>
        <h2 class="section-title">Datasets by modality</h2>
        <p class="section-sub">Imaging and analysis modalities represented across the archive.</p>
        <div class="bar-list mt-3" id="bil-modality-bars"></div>
      </div>
    </div>
  </div>

  <p class="bil-stats-unavailable-msg">
    Stats are temporarily unavailable — visit the
    <a href="https://api.brainimagelibrary.org/web">Search Brain Inventory</a> to explore the archive directly.
  </p>
</section>
```

- [ ] **Step 2: Create `assets/js/stats.js`**

```javascript
// Load /data/stats.json and populate the #bil-stats section, if present.
// Fetched same-origin (no CORS needed). Cache disabled — the JSON is
// regenerated daily and we want the browser to pick up updates.
(function () {
  "use strict";

  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("en-US") : "—";
  }

  function fillHeadline(headline) {
    document.querySelectorAll("#bil-stat-grid [data-stat]").forEach(function (el) {
      var key = el.getAttribute("data-stat");
      var value = headline[key];
      el.textContent = fmt(value);
    });
  }

  function renderBars(containerId, rows) {
    var container = document.getElementById(containerId);
    if (!container || !rows || !rows.length) return;
    var max = rows.reduce(function (m, r) { return r.count > m ? r.count : m; }, 0);
    if (max === 0) return;
    var html = rows.map(function (r) {
      var pct = (r.count / max) * 100;
      return (
        '<div class="bar-row">' +
          '<span class="bar-name">' + r.name + '</span>' +
          '<div class="bar-track"><div class="bar-fill" style="width:' + pct.toFixed(1) + '%"></div></div>' +
          '<span class="bar-count">' + fmt(r.count) + '</span>' +
        '</div>'
      );
    }).join("");
    container.innerHTML = html;
  }

  async function loadStats() {
    var host = document.getElementById("bil-stats");
    if (!host) return;
    try {
      var resp = await fetch("/data/stats.json", { cache: "no-store" });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      var data = await resp.json();
      fillHeadline(data.headline);
      renderBars("bil-species-bars", data.species);
      renderBars("bil-modality-bars", data.modalities);
    } catch (e) {
      console.warn("BIL stats load failed:", e);
      host.classList.add("bil-stats--unavailable");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStats);
  } else {
    loadStats();
  }
})();
```

- [ ] **Step 3: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds. `_site/assets/js/stats.js` is present.

- [ ] **Step 4: Verify JS syntax**

```bash
node --check assets/js/stats.js
```
Expected: no output, exit 0.

- [ ] **Step 5: Checkpoint**

Suggested commit message: `feat(stats): stats-block include and stats.js renderer`

---

## Task 12: New `index.html`

**Files:**
- Modify: `index.html` (full rewrite)

**Interfaces:**
- Consumes: `_layouts/default.html`, `_includes/stats-block.html`, CSS from Tasks 2/5/6/8.
- Produces: The new landing page.

- [ ] **Step 1: Rewrite `index.html`**

```html
---
layout: default
title: Home
description: A public archive of high-resolution brain microscopy data — free for researchers everywhere.
home_announcement: false
---

<section class="hero">
  <div class="container-hero">
    <div>
      <div class="eyebrow">The open archive for brain microscopy</div>
      <h1 class="hero-title">Find, explore, and download brain imaging data.</h1>
      <p class="hero-lead">
        The Brain Image Library is a BRAIN Initiative data archive of
        high-resolution microscopy — petabytes of open data across species,
        techniques, and scales, free for researchers everywhere.
      </p>

      <div class="hero-search">
        <iframe src="https://api.brainimagelibrary.org/web/search.html"
                width="100%" height="140" frameborder="0" scrolling="no"
                title="Search the Brain Image Library"></iframe>
      </div>

      <div class="hero-cta">
        <a class="btn btn-outline-secondary" href="{{ '/submission.html' | relative_url }}">
          Submit your data
          <i class="bi bi-arrow-right ms-1"></i>
        </a>
      </div>
    </div>

    <div>
      {% include stats-block.html %}
    </div>
  </div>
</section>

<section class="container my-5">
  <header class="mb-4">
    <div class="section-eyebrow">Featured</div>
    <h2 class="section-title">From the archive</h2>
  </header>

  <div class="feature-grid">
    <div class="feature-card">
      <img src="{{ '/assets/brain1.jpg' | relative_url }}" alt="Cell counting, imaging, STPT">
      <div class="feature-card-body">
        <p class="feature-card-caption">Cell counting, Imaging, STPT</p>
      </div>
    </div>
    <div class="feature-card">
      <img src="{{ '/assets/brain3.jpg' | relative_url }}" alt="Connectivity study">
      <div class="feature-card-body">
        <p class="feature-card-caption">Connectivity, TRIO, Triple Injection, Monosynaptic-Transsynaptic</p>
      </div>
    </div>
    <div class="feature-card">
      <img src="{{ '/assets/brain5.png' | relative_url }}" alt="Neuron morphologies overlaid on fMOST dataset">
      <div class="feature-card-body">
        <p class="feature-card-caption">Neuron morphologies overlaid on fMOST dataset</p>
      </div>
    </div>
  </div>
</section>
```

Note: The current `index.html` carousel has more images than shown above. Retire the ones the user hasn't uncommented (matches the current "comment out retired" pattern). If more than 3 should stay, add more `.feature-card` blocks — the grid handles overflow via `flex-wrap`.

- [ ] **Step 2: Verify build + render**

```bash
bundle exec jekyll serve --livereload
```
Open `http://localhost:4000/`. Expected:
- Hero renders with copy, iframe search, secondary CTA
- Stat grid shows real numbers (from the seeded `data/stats.json`)
- Species and modality bar charts populate below
- Featured card grid renders
- No console errors

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat(index): new landing page with hero, stats, feature grid`

---

## Task 13: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/stats.yml`

**Interfaces:**
- Consumes: `scripts/build_stats.py`, `requirements-dev.txt`.
- Produces: A daily GH Actions job that regenerates `data/stats.json` and commits it back to the repo. First run happens either at the next cron trigger or via manual `workflow_dispatch`.

- [ ] **Step 1: Create `.github/workflows/stats.yml`**

```yaml
name: Refresh stats.json

on:
  schedule:
    - cron: "0 6 * * *"     # 06:00 UTC daily
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install deps
        run: pip install requests

      - name: Build stats
        run: python3 scripts/build_stats.py

      - name: Commit if changed
        run: |
          if ! git diff --quiet -- data/stats.json; then
            git config user.name  "stats-bot"
            git config user.email "stats-bot@users.noreply.github.com"
            git add data/stats.json
            git commit -m "chore(stats): daily refresh"
            git push
          else
            echo "No changes to stats.json"
          fi
```

- [ ] **Step 2: Verify build (workflow is not run locally, just verify file parses)**

```bash
bundle exec jekyll build --strict_front_matter
```
Expected: build succeeds.

- [ ] **Step 3: Note for user**

The workflow won't run until the branch is pushed. After merging, the user should manually trigger the workflow once (Actions → "Refresh stats.json" → Run workflow) to confirm it works end-to-end.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `ci: daily workflow to refresh data/stats.json`

---

## Task 14: `scripts/bs4_to_bs5.py` rewrite tool — tests first

**Files:**
- Create: `tests/test_bs4_to_bs5.py`
- Create: `scripts/bs4_to_bs5.py`

**Interfaces:**
- Consumes: HTML file contents.
- Produces: A callable `rewrite_html(html: str) -> str` function that applies the BS4→BS5 attribute and class rewrites. Used in Task 15 to batch-rewrite pages.

- [ ] **Step 1: Write failing tests**

Create `tests/test_bs4_to_bs5.py`:

```python
from scripts.bs4_to_bs5 import rewrite_html


def test_rewrites_data_toggle():
    src = '<a href="#" data-toggle="dropdown">x</a>'
    assert 'data-bs-toggle="dropdown"' in rewrite_html(src)
    assert 'data-toggle=' not in rewrite_html(src)


def test_rewrites_data_target():
    src = '<button data-target="#foo">x</button>'
    assert 'data-bs-target="#foo"' in rewrite_html(src)


def test_rewrites_slide_attrs():
    src = '<a data-slide="prev">x</a><li data-slide-to="0">y</li>'
    out = rewrite_html(src)
    assert 'data-bs-slide="prev"' in out
    assert 'data-bs-slide-to="0"' in out


def test_rewrites_text_left_class():
    src = '<div class="text-left mb-3">x</div>'
    out = rewrite_html(src)
    assert 'class="text-start mb-3"' in out


def test_rewrites_margin_classes():
    src = '<div class="ml-1 mr-3 pl-2 pr-4">x</div>'
    out = rewrite_html(src)
    assert 'ms-1' in out and 'me-3' in out and 'ps-2' in out and 'pe-4' in out
    assert 'ml-1' not in out and 'pr-4' not in out


def test_rewrites_form_row_and_form_group():
    src = '<div class="form-row"><div class="form-group">x</div></div>'
    out = rewrite_html(src)
    assert 'row g-2' in out
    assert 'mb-3' in out
    assert 'form-group' not in out


def test_rewrites_sr_only():
    src = '<span class="sr-only">screen readers</span>'
    out = rewrite_html(src)
    assert 'visually-hidden' in out
    assert 'sr-only' not in out


def test_rewrites_badge():
    src = '<span class="badge badge-info">3</span>'
    out = rewrite_html(src)
    assert 'bg-info' in out
    assert 'text-white' in out
    assert 'badge-info' not in out


def test_rewrites_font_awesome_bars():
    src = '<i class="fa fa-bars"></i>'
    out = rewrite_html(src)
    assert 'bi bi-list' in out


def test_does_not_rewrite_inside_pre_or_code():
    # Critical: metadataapi.html has literal 'data-toggle' strings in code samples.
    src = '<pre><code>data-toggle="dropdown"</code></pre>'
    out = rewrite_html(src)
    assert 'data-toggle="dropdown"' in out  # preserved in code
    assert 'data-bs-toggle' not in out


def test_replaces_jumbotron_with_content_card():
    src = '<div class="jumbotron pagejumbotron">body</div>'
    out = rewrite_html(src)
    assert 'content-card' in out
    assert 'jumbotron' not in out
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_bs4_to_bs5.py -v
```
Expected: `ImportError` — script doesn't exist yet.

- [ ] **Step 3: Implement `scripts/bs4_to_bs5.py`**

```python
"""Rewrite Bootstrap 4 attributes and classes to Bootstrap 5 equivalents.

Usage:
    python3 scripts/bs4_to_bs5.py path/to/file.html            # in place
    python3 scripts/bs4_to_bs5.py path/to/*.html
    echo '<div class="ml-1">' | python3 scripts/bs4_to_bs5.py  # stdin

The rewriter walks attributes only (never text nodes or <pre>/<code> contents),
so literal strings like `data-toggle` in example code are preserved.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

DATA_ATTR_MAP = {
    "data-toggle":   "data-bs-toggle",
    "data-target":   "data-bs-target",
    "data-dismiss":  "data-bs-dismiss",
    "data-parent":   "data-bs-parent",
    "data-slide":    "data-bs-slide",
    "data-slide-to": "data-bs-slide-to",
}

# Class token rewrites (whole token, not substring).
CLASS_TOKEN_MAP = {
    "text-left":       "text-start",
    "text-right":      "text-end",
    "float-left":      "float-start",
    "float-right":     "float-end",
    "no-gutters":      "g-0",
    "sr-only":         "visually-hidden",
    "font-italic":     "fst-italic",
    "text-monospace":  "font-monospace",
    "embed-responsive":"ratio",
    "form-row":        "row g-2",     # multi-token replacement
    "custom-select":   "form-select",
    "close":           "btn-close",
    "form-group":      "mb-3",
    "jumbotron":       "content-card",
    "pagejumbotron":   "",            # our new content-card owns the padding
    "mainjumbotron":   "hero",
    "tablejumbotron":  "",
}

# Regex rewrites (start/end margin/padding utilities).
CLASS_REGEX_MAP = [
    (re.compile(r"^ml-(\d+|auto)$"), r"ms-\1"),
    (re.compile(r"^mr-(\d+|auto)$"), r"me-\1"),
    (re.compile(r"^pl-(\d+|auto)$"), r"ps-\1"),
    (re.compile(r"^pr-(\d+|auto)$"), r"pe-\1"),
    (re.compile(r"^font-weight-(\w+)$"), r"fw-\1"),
]

# Badge color rewrites: badge-<color> -> bg-<color> text-white
BADGE_RE = re.compile(r"^badge-(primary|secondary|success|danger|warning|info|light|dark)$")

# Font Awesome icon rewrites (this site uses only fa-bars per audit).
FA_MAP = {
    "fa-bars":          "bi-list",
    "fa-search":        "bi-search",
    "fa-download":      "bi-download",
    "fa-external-link": "bi-box-arrow-up-right",
    "fa-envelope":      "bi-envelope",
    "fa-github":        "bi-github",
}


def _rewrite_class_list(tokens: list[str]) -> list[str]:
    out: list[str] = []
    saw_fa_prefix = False
    saw_bi_prefix = False
    for tok in tokens:
        # FA prefix classes ("fa", "fas", "fab", "far") drop, we translate the icon token to bi-*.
        if tok in ("fa", "fas", "fab", "far"):
            saw_fa_prefix = True
            continue
        # Badge coloring: replace with bg-<color> + text-white
        m = BADGE_RE.match(tok)
        if m:
            out.append(f"bg-{m.group(1)}")
            if m.group(1) not in ("light", "warning"):  # dark text on light/warning badges
                out.append("text-white")
            continue
        # FA icon token → BI icon token
        if tok in FA_MAP:
            saw_bi_prefix = True
            out.append(FA_MAP[tok])
            continue
        # Static map
        if tok in CLASS_TOKEN_MAP:
            repl = CLASS_TOKEN_MAP[tok]
            if repl:
                out.extend(repl.split())
            continue
        # Regex map
        replaced = False
        for pat, subs in CLASS_REGEX_MAP:
            if pat.match(tok):
                out.append(pat.sub(subs, tok))
                replaced = True
                break
        if replaced:
            continue
        # Otherwise pass through
        out.append(tok)

    if saw_fa_prefix and saw_bi_prefix:
        # Ensure "bi" prefix is present alongside the "bi-*" icon token.
        if "bi" not in out:
            out.insert(0, "bi")

    return out


def rewrite_html(html: str) -> str:
    """Apply all rewrites to a fragment or full document."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        # Skip contents of <pre> and <code> — do NOT rewrite text nodes.
        # We still rewrite the <pre>/<code> tag's own attributes, but its
        # descendants are left alone by walking find_all() and checking ancestry.
        if any(anc.name in ("pre", "code") for anc in tag.parents):
            continue
        # Data attributes
        for old, new in DATA_ATTR_MAP.items():
            if tag.has_attr(old):
                tag[new] = tag[old]
                del tag[old]
        # Classes
        if tag.has_attr("class"):
            tag["class"] = _rewrite_class_list(list(tag["class"]))
            if not tag["class"]:
                del tag["class"]
    return str(soup)


def _rewrite_file(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    rewritten = rewrite_html(original)
    if rewritten != original:
        path.write_text(rewritten, encoding="utf-8")
        print(f"rewrote {path}")
    else:
        print(f"unchanged {path}")


def main(argv: list[str]) -> int:
    if not argv:
        # stdin mode
        sys.stdout.write(rewrite_html(sys.stdin.read()))
        return 0
    for arg in argv:
        for path in Path().glob(arg) if "*" in arg else [Path(arg)]:
            _rewrite_file(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_bs4_to_bs5.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Checkpoint**

Suggested commit message: `feat(scripts): bs4_to_bs5.py rewriter with test coverage`

---

## Task 15: Convert about-cluster pages

**Files:**
- Modify: `about.html`, `people.html`, `partners.html`, `braindataarchives.html`

**Interfaces:**
- Consumes: `_layouts/default.html`, `scripts/bs4_to_bs5.py`.
- Produces: Each page as `layout: default` front matter + BS5-rewritten body.

**Conversion pattern (applies to every remaining page in this and subsequent conversion tasks):**

For each page:

1. Read the current file.
2. Identify the "body" — the content between:
   - After: `<script>$(function(){$("#topmenu").load("menu.html");});</script>`
   - Before: `<div id="bottomfooter"></div>` (or equivalent)
3. Run the body through `scripts/bs4_to_bs5.py` to apply mechanical class rewrites.
4. Replace `.jumbotron.pagejumbotron` wrapper with `.container.my-5` + a `<header>` block + `.content-card` (for docs pages) or just `.container.my-5` (for slim pages).
5. Prepend Jekyll front matter (`---\nlayout: default\ntitle: <Title>\ndescription: <one-line>\n---`).
6. Delete everything else — the `<!DOCTYPE>`, `<html>`, `<head>`, `<body class="bg">`, the topmenu/bottomfooter loader divs and their scripts, the trailing `<script src="/js/...">` tags.
7. Verify: `bundle exec jekyll build` succeeds; page renders correctly in browser at `http://localhost:4000/<page>.html`.

- [ ] **Step 1: Convert `about.html`**

Front matter: `title: About BIL`, `description: About the Brain Image Library — mission, scope, and data.`

Wrap body in `<div class="container my-5"><div class="content-card">…</div></div>`. Add a `<header>` block with an eyebrow "ABOUT" and h1 matching the current page title. Run the body through `bs4_to_bs5.py`.

Verify: `http://localhost:4000/about.html` renders with nav, content, footer, and no console errors.

- [ ] **Step 2: Convert `people.html`**

Front matter: `title: BIL Staff`, `description: The team behind the Brain Image Library.`

Same pattern — `content-card` wrapper, add header. The current page uses BS4 grid — the rewriter handles it; verify the grid still lays out correctly.

- [ ] **Step 3: Convert `partners.html`**

Front matter: `title: Partners`, `description: BIL's institutional and consortium partners.`

Same pattern.

- [ ] **Step 4: Convert `braindataarchives.html`**

Front matter: `title: BRAIN Initiative Data Archives`, `description: Related archives across the BRAIN Initiative.`

Same pattern.

- [ ] **Step 5: Verify all four pages render**

```bash
bundle exec jekyll serve --livereload
```
Visit each URL, spot-check that the layout works.

- [ ] **Step 6: Checkpoint**

Suggested commit message: `feat: convert about cluster (about, people, partners, braindataarchives)`

---

## Task 16: Convert data-submission cluster

**Files:**
- Modify: `datarequirements.html`, `submission.html`, `account.html`, `accountnew.html`, `datadirbp.html`, `newmetadatamodel.html`, `training.html`

**Interfaces:**
- Consumes: `_layouts/default.html`, `scripts/bs4_to_bs5.py`.
- Produces: Seven converted pages.

- [ ] **Step 1: Convert each page using the pattern from Task 15**

For each of the seven pages: apply Task 15's conversion pattern.

| File | Title | Description |
|---|---|---|
| `datarequirements.html` | Data Depositor FAQ | Frequently asked questions for BIL data submitters. |
| `submission.html` | Submission Instructions | How to submit data to the Brain Image Library. |
| `account.html` | Create Account | Register for a BIL data-submission account. |
| `accountnew.html` | New Account | (Convert as-is; content review to prune duplicates is a follow-up.) |
| `datadirbp.html` | Submission Best Practices | Best practices for structuring submitted data. |
| `newmetadatamodel.html` | Metadata Model | The BIL metadata model. |
| `training.html` | Training | Training resources for data depositors. |

**Special attention for `submission.html`:** heavy form markup. Verify after conversion that form controls render correctly under BS5 (`.form-select`, `.form-control`, `.mb-3` spacing). The rewriter handles `.form-group` → `.mb-3` and `.custom-select` → `.form-select`, but verify visually.

**Special attention for `newmetadatamodel.html`:** 161 KB — large doc page. After rewrite, spot-check that long tables, code blocks, and heading hierarchy still work.

- [ ] **Step 2: Verify all seven pages render**

Spot-check each URL at `http://localhost:4000/<page>.html`.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat: convert data-submission cluster (7 pages)`

---

## Task 17: Convert data-access cluster

**Files:**
- Modify: `download.html`, `identifiers.html`, `computevisual.html`, `visual.html`, `analysis_ecosystem.html`, `restrictedaccess.html`, `metadataapi.html`, `citation.html`

**Interfaces:** Same as Task 16.

- [ ] **Step 1: Convert each page using the pattern from Task 15**

| File | Title | Description |
|---|---|---|
| `download.html` | Downloading Data | How to download data from BIL. |
| `identifiers.html` | BIL Identifiers | The BIL identifier scheme. |
| `computevisual.html` | Computing and Visualization | Compute resources for BIL data. |
| `visual.html` | Web Visualization | Browser-based visualization of BIL data. |
| `analysis_ecosystem.html` | Analysis Ecosystem | BIL's compute and analysis environment. |
| `restrictedaccess.html` | Restricted Data | Restricted-access datasets and how to request them. |
| `metadataapi.html` | Metadata API | The BIL metadata API. |
| `citation.html` | Citing Data | How to cite BIL datasets. |

**Special attention for `metadataapi.html`:** contains many `<pre><code>` blocks with literal strings like `data-toggle="dropdown"` used as API example URLs. The `bs4_to_bs5.py` rewriter is designed to skip contents of `<pre>` and `<code>` — verify with a diff check after running that no code sample was corrupted.

**Special attention for `analysis_ecosystem.html`:** 161 KB doc page. Spot-check after rewrite.

- [ ] **Step 2: Verify all eight pages render**

Spot-check each URL. Pay extra attention to `metadataapi.html` code blocks.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat: convert data-access cluster (8 pages)`

---

## Task 18: Convert remaining top-level pages

**Files:**
- Modify: `access.html`, `accessallocation.html`, `avout.html`, `compute.html`, `globus.html`, `hackathon.html`, `hackathonFAQ.html`, `neuroscience2023.html`, `ng_help.html`, `password.html`, `publications.html`, `spatialworkshop2025.html`, `XSEDEportal.html`

**Interfaces:** Same as Task 15.

- [ ] **Step 1: Convert each page using the pattern from Task 15**

| File | Title | Description |
|---|---|---|
| `access.html` | Access | Data access overview. |
| `accessallocation.html` | ACCESS Allocation | ACCESS compute allocation details. |
| `avout.html` | (preserve current title) | (preserve current description) |
| `compute.html` | Compute | Compute environment. |
| `globus.html` | Globus | Using Globus with BIL. |
| `hackathon.html` | Hackathon | (Retired event — preserve content.) |
| `hackathonFAQ.html` | Hackathon FAQ | (Retired event.) |
| `neuroscience2023.html` | Neuroscience 2023 | (Retired event.) |
| `ng_help.html` | Neuroglancer Help | Using Neuroglancer with BIL data. |
| `password.html` | Password | Account password help. |
| `publications.html` | Publications | Publications using BIL data. |
| `spatialworkshop2025.html` | Spatial Workshop 2025 | (Past event.) |
| `XSEDEportal.html` | XSEDE Portal | (Retired — XSEDE became ACCESS.) |

Retired event pages get the same layout but no content changes.

- [ ] **Step 2: Verify all thirteen pages render**

Spot-check each URL.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat: convert remaining top-level pages (13 pages)`

---

## Task 19: Convert nested `software/x2go.html`

**Files:**
- Modify: `software/x2go.html`

**Interfaces:** Same as Task 15.

- [ ] **Step 1: Convert using the pattern from Task 15**

Front matter: `title: X2Go`, `description: Using X2Go to connect to BIL.`

- [ ] **Step 2: Verify rendering**

Visit `http://localhost:4000/software/x2go.html`. Confirm nav/footer render, all internal links (relative paths from `software/` back to the root) work.

- [ ] **Step 3: Checkpoint**

Suggested commit message: `feat: convert software/x2go.html`

---

## Task 20: Delete legacy assets

**Files:**
- Delete: `menu.html`
- Delete: `footer.html`
- Delete: `datasets.html`
- Delete: `my.css`
- Delete: `css/bootstrap.css`
- Delete: `js/bootstrap.min.js`
- Delete: `js/popper.min.js`
- Delete: `js/jquery.min.js`

**Interfaces:**
- Consumes: nothing after this deletion (all pages now use Jekyll includes).
- Produces: A leaner repo.

- [ ] **Step 1: Confirm nothing references the files to be deleted**

```bash
grep -rEn 'menu\.html|footer\.html|datasets\.html|my\.css|/js/jquery\.min\.js|/js/bootstrap\.min\.js|/js/popper\.min\.js|/css/bootstrap\.css' . \
  --include="*.html" --include="*.css" --include="*.js" --include="*.yml" \
  --exclude-dir=_site --exclude-dir=node_modules --exclude-dir=vendor \
  --exclude-dir=.git --exclude-dir=docs \
  || true
```
Expected: no output. If there's output, that page still references a legacy path — fix it before proceeding.

- [ ] **Step 2: Delete the files**

```bash
rm menu.html footer.html datasets.html my.css
rm css/bootstrap.css
rm js/bootstrap.min.js js/popper.min.js js/jquery.min.js
# Prune the /css and /js directories if empty
rmdir css js 2>/dev/null || true
```

- [ ] **Step 3: Verify build still succeeds and site still renders**

```bash
bundle exec jekyll build --strict_front_matter
bundle exec jekyll serve
```
Visit `http://localhost:4000/` and a handful of other pages. Expected: everything renders as before.

- [ ] **Step 4: Checkpoint**

Suggested commit message: `chore: remove BS4/jQuery/FA assets and legacy chrome files`

---

## Task 21: Verification scripts

**Files:**
- Create: `scripts/check_links.py`
- Create: `scripts/validate_stats_schema.py`
- Create: `scripts/verify.sh`
- Create: `tests/test_check_links.py`
- Create: `tests/test_validate_stats_schema.py`

**Interfaces:**
- Consumes: built `_site/`, `data/stats.json`, `assets/js/stats.js`.
- Produces: A `verify.sh` that runs before push to catch regressions.

- [ ] **Step 1: Write failing tests for `check_links.py`**

Create `tests/test_check_links.py`:

```python
from pathlib import Path
import tempfile
from scripts.check_links import find_broken_links


def _write(root: Path, rel: str, body: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_reports_missing_internal_link():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="/missing.html">go</a>')
        broken = find_broken_links(root)
        assert any("missing.html" in b.target for b in broken)


def test_ignores_external_links():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="https://example.com/x">x</a>')
        assert find_broken_links(root) == []


def test_finds_existing_internal_link():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="/b.html">b</a>')
        _write(root, "b.html", 'ok')
        assert find_broken_links(root) == []


def test_handles_anchor_only_links():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="#section">jump</a>')
        assert find_broken_links(root) == []
```

- [ ] **Step 2: Implement `scripts/check_links.py`**

```python
"""Find broken internal <a href> links in a built Jekyll _site/ directory.

Only checks internal links (starting with `/`, or a bare filename).
External `http(s)://`, `mailto:`, `tel:`, and pure `#anchor` links are ignored.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class BrokenLink:
    source: str
    target: str


def _is_internal(href: str) -> bool:
    if not href:
        return False
    if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
        return False
    if href.startswith("#"):
        return False
    return True


def _normalize(root: Path, source: Path, href: str) -> Path:
    parsed = urlparse(href)
    path = parsed.path
    if not path:
        return source  # anchor-only
    if path.startswith("/"):
        return (root / path.lstrip("/")).resolve()
    return (source.parent / path).resolve()


def find_broken_links(root: Path) -> list[BrokenLink]:
    broken: list[BrokenLink] = []
    root = root.resolve()
    for html_file in root.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not _is_internal(href):
                continue
            target = _normalize(root, html_file, href)
            # Accept both /foo.html and /foo/ (directory index)
            if target.is_file():
                continue
            if target.is_dir() and (target / "index.html").is_file():
                continue
            broken.append(BrokenLink(source=str(html_file.relative_to(root)),
                                     target=href))
    return broken


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    if not root.exists():
        print(f"ERROR: {root} does not exist. Run `bundle exec jekyll build` first.")
        return 2
    broken = find_broken_links(root)
    if broken:
        for b in broken:
            print(f"BROKEN {b.source} → {b.target}")
        return 1
    print(f"OK: no broken internal links in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run link tests to confirm they pass**

```bash
pytest tests/test_check_links.py -v
```
Expected: all pass.

- [ ] **Step 4: Write failing tests for `validate_stats_schema.py`**

Create `tests/test_validate_stats_schema.py`:

```python
import json
import tempfile
from pathlib import Path
from scripts.validate_stats_schema import validate


VALID = {
    "generated_at": "2026-08-21T06:00:00Z",
    "source": "https://api.brainimagelibrary.org/stats?type=all",
    "headline": {"datasets": 14225, "consortia": 4, "species": 14, "modalities": 14},
    "species": [{"name": "Mouse", "count": 100}],
    "modalities": [{"name": "Cell morphology", "count": 100}],
    "consortia": [{"label": "BICCN", "value": "BICCN", "count": 100}],
}


def test_accepts_valid_document():
    assert validate(VALID) == []


def test_rejects_missing_headline():
    bad = dict(VALID); del bad["headline"]
    errs = validate(bad)
    assert any("headline" in e for e in errs)


def test_rejects_wrong_type_in_species():
    bad = dict(VALID); bad["species"] = [{"name": "Mouse", "count": "one hundred"}]
    errs = validate(bad)
    assert any("count" in e for e in errs)


def test_rejects_empty_species_when_headline_says_present():
    bad = dict(VALID); bad["species"] = []; bad["headline"] = dict(VALID["headline"], species=5)
    errs = validate(bad)
    assert any("species" in e for e in errs)
```

- [ ] **Step 5: Implement `scripts/validate_stats_schema.py`**

```python
"""Validate data/stats.json against the design schema."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(doc: dict) -> list[str]:
    errs: list[str] = []
    for k in ("generated_at", "source", "headline", "species", "modalities", "consortia"):
        if k not in doc:
            errs.append(f"missing top-level key: {k}")
    if "headline" in doc:
        for k in ("datasets", "consortia", "species", "modalities"):
            if k not in doc["headline"]:
                errs.append(f"missing headline.{k}")
            elif not isinstance(doc["headline"][k], int):
                errs.append(f"headline.{k} must be int")
    for coll in ("species", "modalities"):
        rows = doc.get(coll, [])
        for i, row in enumerate(rows):
            if not isinstance(row.get("name"), str):
                errs.append(f"{coll}[{i}].name must be str")
            if not isinstance(row.get("count"), int):
                errs.append(f"{coll}[{i}].count must be int")
        headline_count = doc.get("headline", {}).get(coll)
        if isinstance(headline_count, int) and headline_count != len(rows):
            errs.append(f"headline.{coll}={headline_count} does not match len({coll})={len(rows)}")
    return errs


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/stats.json")
    doc = json.loads(path.read_text(encoding="utf-8"))
    errs = validate(doc)
    if errs:
        for e in errs:
            print(f"SCHEMA ERROR: {e}")
        return 1
    print(f"OK: {path} conforms to schema")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run schema tests to confirm they pass**

```bash
pytest tests/test_validate_stats_schema.py -v
```
Expected: all pass.

- [ ] **Step 7: Create `scripts/verify.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "1. Jekyll build..."
bundle exec jekyll build --strict_front_matter

echo "2. No BS4 data-* attributes in built site..."
if grep -rEn 'data-(toggle|target|dismiss|slide)=' _site/ >/dev/null 2>&1; then
  echo "FAIL: BS4 data-* attribute found in _site/"
  grep -rEn 'data-(toggle|target|dismiss|slide)=' _site/
  exit 1
fi

echo "3. No jQuery references..."
if grep -rEn 'jquery' _site/ --include='*.html' --include='*.js' >/dev/null 2>&1; then
  echo "FAIL: jquery reference found"
  grep -rEn 'jquery' _site/ --include='*.html' --include='*.js'
  exit 1
fi

echo "4. No BS4/FA asset paths..."
if grep -rEn '/js/bootstrap\.min\.js|/js/popper\.min\.js|/js/jquery\.min\.js|/css/bootstrap\.css|font-awesome' _site/ --include='*.html' >/dev/null 2>&1; then
  echo "FAIL: legacy asset path found"
  exit 1
fi

echo "5. No broken internal links..."
python3 scripts/check_links.py _site/

echo "6. Stats JSON schema..."
python3 scripts/validate_stats_schema.py data/stats.json

echo "7. Stats JS syntax..."
node --check assets/js/stats.js

echo ""
echo "All automated checks passed."
echo ""
echo "Now perform the manual visual pass:"
echo "  bundle exec jekyll serve"
echo "  Then check: /, /contact.html, /submission.html, /newmetadatamodel.html,"
echo "  /accessallocation.html, /metadataapi.html, /hackathon.html, /software/x2go.html"
echo "  Also verify at mobile viewport (375px)."
```

- [ ] **Step 8: Make it executable and run it**

```bash
chmod +x scripts/verify.sh
./scripts/verify.sh
```
Expected: all seven checks pass.

- [ ] **Step 9: Checkpoint**

Suggested commit message: `feat(scripts): verification helpers (check_links, validate_stats_schema, verify.sh)`

---

## Task 22: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: nothing.
- Produces: Updated guidance for future Claude Code sessions to work in the modernized codebase.

- [ ] **Step 1: Rewrite `CLAUDE.md`**

Preserve the required header. Reflect:
- Jekyll is the site framework; pages are front-matter + body only
- Shared chrome lives in `_layouts/default.html` and `_includes/*`
- Local preview: `bundle exec jekyll serve --livereload`
- The design system: `assets/css/site.css` with `:root` tokens
- Stats pipeline: `scripts/build_stats.py` + `.github/workflows/stats.yml` + `data/stats.json`
- Verification: `./scripts/verify.sh` before pushing

Draft body:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Static site for the Brain Image Library, served at `www.brainimagelibrary.org` (see `CNAME`) via GitHub Pages using Jekyll.

## Serving locally

GitHub Pages runs Jekyll — local preview must too, or the `_layouts/default.html` chrome (nav, footer) won't render.

```bash
gem install bundler jekyll
bundle install
bundle exec jekyll serve --livereload
# → http://localhost:4000
```

`python3 -m http.server` will *not* work anymore because pages depend on Jekyll to expand `layout: default` and `{% include %}` directives.

## Structure

- `_layouts/default.html` — wraps every page's `{{ content }}` with head, nav, and footer.
- `_includes/head.html` — `<head>` fragment: BS5 CSS, Bootstrap Icons, Inter, `site.css`, Google Analytics. Applied to every page.
- `_includes/nav.html` — top navbar. Edit here to change navigation for the whole site.
- `_includes/footer.html` — footer + announcement banner. Edit here to change the footer for the whole site.
- `_includes/announcements.html` — empty by default; populate + set `home_announcement: true` in the page's front matter to display.
- `_includes/stats-block.html` — landing page's stats block (skeleton; `assets/js/stats.js` fills it in).
- `assets/css/site.css` — the entire custom design system. Design tokens (colors, type, spacing) live in `:root`. Component classes below.
- `assets/js/stats.js` — reads `data/stats.json` and renders the landing page's headline numbers and bar charts. Same-origin fetch.
- `data/stats.json` — generated daily by `.github/workflows/stats.yml`. Do not hand-edit; the workflow overwrites it.
- `scripts/build_stats.py` — the generator. Also runnable locally to refresh `data/stats.json`.
- `scripts/bs4_to_bs5.py` — the one-shot BS4→BS5 rewriter used during the modernization. Kept in the tree in case a future page needs the same treatment.
- `scripts/verify.sh` — pre-push check. Runs the build, greps for stragglers, checks link validity, validates stats schema.

Each `*.html` page has Jekyll front matter (`---\nlayout: default\ntitle: ...\n---`) followed by the page body. Never re-introduce a full `<html>`/`<head>`/nav-loader per page — that pattern is gone.

## Framework and dependencies

- Bootstrap 5.3.3 (pinned) — from jsDelivr, loaded in `_includes/head.html` and `_layouts/default.html`.
- Bootstrap Icons 1.11.3 — from jsDelivr.
- Inter (Google Fonts) for headings; system-ui for body.
- No jQuery. No Font Awesome. No standalone Popper (BS5 bundles it).

When editing HTML, use BS5 attribute and utility names: `data-bs-toggle`, `data-bs-target`, `.text-start` (not `.text-left`), `.ms-*`/`.me-*` (not `.ml-*`/`.mr-*`), `.form-select` (not `.custom-select`), `.visually-hidden` (not `.sr-only`), `.mb-3` (not `.form-group`). If in doubt, run:

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
- The species merge table lives in `scripts/build_stats.py` — `SPECIES_MERGE`. Add or edit entries there.

## External services

Two subdomains host related tooling — those are separate deployments, not in this repo:

- `api.brainimagelibrary.org` — data + metadata API. `web/search.html` is iframed in the homepage hero.
- `submit.brainimagelibrary.org` — data submission portal, linked from the nav.

## Before pushing

```bash
./scripts/verify.sh
```
```

- [ ] **Step 2: Verify build**

```bash
bundle exec jekyll build --strict_front_matter
```

- [ ] **Step 3: Checkpoint**

Suggested commit message: `docs(claude): update CLAUDE.md for Jekyll + BS5 workflow`

---

## Task 23: Full verification pass

**Files:** none

**Interfaces:**
- Consumes: everything.
- Produces: Confidence.

- [ ] **Step 1: Run the verification script**

```bash
./scripts/verify.sh
```
Expected: all seven checks pass.

- [ ] **Step 2: Run all Python tests**

```bash
pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 3: Manual visual pass**

Start the server:
```bash
bundle exec jekyll serve --livereload
```

Visit and verify each of these renders correctly (nav visible, content visible, footer visible, no console errors, no failed network requests):

- [ ] `/` — hero, search iframe loads, stats populate with real numbers, species/modality bars render, feature grid displays.
- [ ] `/contact.html` — short page.
- [ ] `/submission.html` — form-heavy page.
- [ ] `/newmetadatamodel.html` — very long doc page.
- [ ] `/accessallocation.html` — table-heavy page.
- [ ] `/metadataapi.html` — code samples intact (spot-check `<pre>` blocks).
- [ ] `/hackathon.html` — retired event page still readable.
- [ ] `/software/x2go.html` — nested-directory page works.

- [ ] **Step 4: Mobile viewport check**

Chrome devtools → device toolbar → 375px width. On the homepage:

- [ ] Topbar collapses to hamburger; hamburger opens the dropdowns.
- [ ] Hero stacks (single column).
- [ ] Stat grid stacks or renders as a 2×2.
- [ ] Species/modality bars remain readable.
- [ ] Feature grid stacks to single column.

- [ ] **Step 5: Notify user**

The plan is complete. Provide the user with:
- A summary of what changed
- A list of files modified/created/deleted
- The location of the design spec and this plan
- Instructions to run `./scripts/verify.sh` themselves before pushing
- A reminder that the GH Actions workflow will only start running on the daily cron *after* the user pushes and merges the PR — before that, `data/stats.json` is the seeded snapshot from Task 10

- [ ] **Step 6: Final checkpoint**

Suggested commit message: `chore: final verification pass`

---

## Post-implementation notes for the user

Once you've reviewed and pushed:

1. **Manually trigger the workflow once** to confirm the pipeline works end-to-end: GitHub → Actions → "Refresh stats.json" → Run workflow → select `master`.
2. **Verify the deployment**: after ~2 minutes, load `https://www.brainimagelibrary.org` (Cmd-Shift-R to bypass cache). Check devtools console for errors and devtools network for `stats.json` returning 200.
3. **Rollback plan**: if anything is wrong, `git revert <sha>` re-deploys the previous state via GH Pages within a few minutes.

Longer-term follow-ups (out of scope for this PR — captured in the design spec §10):
- Add CORS to the API's nginx config, then swap `stats.js` to fetch live from `/stats?type=all` and retire the GH Action.
- Content-review pass with the BIL team to prune orphaned/retired pages.
- Consider replacing the deleted `datasets.html` with a live-search page against `/query/dataset`.
