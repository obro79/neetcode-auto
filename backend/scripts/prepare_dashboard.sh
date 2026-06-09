#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DASHBOARD_DIR="$ROOT/dashboard"
OUTPUT_DIR="$ROOT/backend/dashboard_dist"

cd "$DASHBOARD_DIR"
npm ci
npm run build

rm -rf "$OUTPUT_DIR"
cp -r dist "$OUTPUT_DIR"
echo "Dashboard built to $OUTPUT_DIR"
