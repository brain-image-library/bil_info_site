#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

echo "1. Jekyll build..."
if command -v bundle >/dev/null 2>&1 && [ -f Gemfile.lock ]; then
  bundle exec jekyll build --strict_front_matter
  SITE_DIR="_site"
else
  echo "  (bundler/Jekyll unavailable — skipping build; static checks only)"
  SITE_DIR=""
fi

TARGETS=()
if [ -n "$SITE_DIR" ]; then TARGETS+=("$SITE_DIR"); fi
# Always check source pages, whether or not Jekyll built.
TARGETS+=($(ls *.html 2>/dev/null || true) $(ls software/*.html 2>/dev/null || true))

echo "2. No BS4 data-* attributes in source pages..."
if grep -EnR 'data-(toggle|target|dismiss|slide|slide-to)=' "${TARGETS[@]}" 2>/dev/null | grep -v data-bs- >/dev/null; then
  echo "FAIL: BS4 data-* attribute found"
  grep -EnR 'data-(toggle|target|dismiss|slide|slide-to)=' "${TARGETS[@]}" 2>/dev/null | grep -v data-bs-
  exit 1
fi

echo "3. No jQuery references..."
if grep -EnR 'jquery' "${TARGETS[@]}" 2>/dev/null | grep -v _site >/dev/null; then
  echo "FAIL: jquery reference found"
  grep -EnR 'jquery' "${TARGETS[@]}" 2>/dev/null | grep -v _site
  exit 1
fi

echo "4. No BS4/FA asset paths..."
if grep -EnR '/js/bootstrap\.min\.js|/js/popper\.min\.js|/js/jquery\.min\.js|/css/bootstrap\.css|font-awesome' "${TARGETS[@]}" 2>/dev/null >/dev/null; then
  echo "FAIL: legacy asset path found"
  grep -EnR '/js/bootstrap\.min\.js|/js/popper\.min\.js|/js/jquery\.min\.js|/css/bootstrap\.css|font-awesome' "${TARGETS[@]}" 2>/dev/null
  exit 1
fi

if [ -n "$SITE_DIR" ]; then
  echo "5. No broken internal links..."
  python3 scripts/check_links.py "$SITE_DIR"
else
  echo "5. (link check skipped — no built _site/)"
fi

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
