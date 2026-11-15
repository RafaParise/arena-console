#!/usr/bin/env bash
set -e

TAG="${1:?Informe a tag da release (ex: 2026.11.14)}"
MSG="${2:-feat: migra servidor web para Rust (Axum) e integra execução nativa no APK Android}"

git rm -rf --cached arena-web/target bin dist apk-out 2>/dev/null || true
git status
git add .
git commit -m "$MSG"
git push origin main

git tag -a "$TAG" -m "Release ARENA $TAG"
git push origin "$TAG"

gh run list --workflow=release-arena.yml --limit 3
gh run watch