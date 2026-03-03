#!/usr/bin/env bash
set -euo pipefail

# Prefer nvm if available
if command -v nvm >/dev/null 2>&1; then
  nvm install
  nvm use
  node -v
  exit 0
fi

echo "nvm not found. Install nvm or use Node 22.12+."
echo "Current node: $(node -v 2>/dev/null || echo 'none')"
exit 1