#!/usr/bin/env bash
set -euo pipefail

# prepare_repo.sh
# Collects the minimal set of files for publishing the mediaplayer app
# into a clean folder ready to be git-initialized and pushed to a remote.
#
# Usage:
#   ./prepare_repo.sh [output_dir] [remote_git_url]
# Examples:
#   ./prepare_repo.sh mediaplayerv4
#   ./prepare_repo.sh mediaplayerv4 git@github.com:you/mediaplayerv4.git

OUTDIR=${1:-mediaplayerv4}
REMOTE=${2:-}

echo "Preparing minimal repo in: $OUTDIR"

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

# Files and directories to include (relative to repository root)
FILES=(
  app.py
  OV.py
  MySql.py
  wsgi.py
  requirements.txt
  sync_media.py
  prepare_repo.sh
  config.sample.py
  README.md
  .gitignore
)

DIRS=(
  templates
  static
)

# Copy files
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    mkdir -p "$OUTDIR/$(dirname "$f")"
    cp "$f" "$OUTDIR/$f"
    echo "  added $f"
  else
    echo "  skipped (missing) $f"
  fi
done

# Copy directories
for d in "${DIRS[@]}"; do
  if [ -d "$d" ]; then
    cp -r "$d" "$OUTDIR/"
    echo "  added dir $d"
  else
    echo "  skipped dir (missing) $d"
  fi
done

# Remove any local config from output if accidentally copied
rm -f "$OUTDIR/config.py"

pushd "$OUTDIR" >/dev/null
if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "Initial import of mediaplayer minimal files"
  echo "Initialized git repository and created first commit in $OUTDIR"
else
  echo "Git repo already present in $OUTDIR"
fi

if [ -n "$REMOTE" ]; then
  git remote add origin "$REMOTE" || true
  git branch -M main || true
  echo "Pushing to remote: $REMOTE"
  git push -u origin main
fi

popd >/dev/null

echo "Done. Review the $OUTDIR folder before pushing to GitHub (config.py is intentionally excluded)."
