#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker run --rm -v "$(pwd):/workspace" -w /workspace alpine:3.21 sh scripts/bootstrap.sh
echo 'Next: docker compose up -d'
