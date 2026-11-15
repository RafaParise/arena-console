#!/usr/bin/env bash
set -e

BASE_URL="${1:-http://127.0.0.1:8080}"

echo "=== 1. Sincronizar armazenamento (/api/storage/sync) ==="
curl -s -X POST "${BASE_URL}/api/storage/sync" \
  -H "Content-Type: application/json" \
  -d '{"paths": ["/storage/emulated/0"]}' | jq .

echo "=== 2. Listar raízes e contadores (/api/storage) ==="
curl -s "${BASE_URL}/api/storage" | jq .

echo "=== 3. Listar ROMs de SNES com metadados gamelist.xml (/api/roms?system=snes) ==="
curl -s "${BASE_URL}/api/roms?system=snes" | jq '.[0] | {id, title, description, artwork_url, is_favorite}'

echo "=== 4. Testar cabeçalhos HTTP de capa (/api/artwork) ==="
ART_URL=$(curl -s "${BASE_URL}/api/roms" | jq -r '[.[] | select(.artwork_url != null)][0].artwork_url // empty')
if [ -n "$ART_URL" ]; then
  curl -I "${BASE_URL}${ART_URL}"
else
  echo "Nenhuma capa encontrada ainda nas pastas de ROMs."
fi

echo "=== 5. Alternar favorito e consultar /api/roms?system=favorites ==="
ROM_ID=$(curl -s "${BASE_URL}/api/roms" | jq -r '.[0].id // empty')
if [ -n "$ROM_ID" ]; then
  curl -s -X POST "${BASE_URL}/api/favorites/toggle" \
    -H "Content-Type: application/json" \
    -d "{\"id\": \"${ROM_ID}\"}" | jq .
  curl -s "${BASE_URL}/api/roms?system=favorites" | jq '.[].title'
fi