#!/bin/bash
# ATOS Daily Update — Run all agents + deploy to GitHub Pages
set -e

cd /home/ubuntu/test-website

echo "════════════════════════════════════════"
echo "  ATOS Daily Update — $(date)"
echo "════════════════════════════════════════"

# Run the ATOS engine
echo "[1/3] Running ATOS engine..."
python3 atos/engine.py

# Commit and push updated data
echo "[2/3] Committing data..."
git add data/
git diff --staged --quiet && echo "No changes to commit." || {
    git commit -m "ATOS: daily auto-update $(date -u +%Y-%m-%dT%H:%M)"
    echo "[3/3] Pushing to GitHub..."
    git push origin main
    echo "✅ Deployed to https://srrajeev.github.io/test-website/"
}

echo "════════════════════════════════════════"
echo "  ATOS Daily Update Complete"
echo "════════════════════════════════════════"
