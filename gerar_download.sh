#!/bin/bash
# Script para criar o pacote de download final
# Executar após todo o trabalho estar concluído

echo "=== GERANDO PACOTE DE DOWNLOAD FINAL ==="

# 1. Limpar pastas desnecessárias
echo "Removendo pastas pesadas..."
rm -rf retroarch/
rm -rf emuladores/
rm -rf dados/
rm -rf perfil/
rm -rf backup/

# 2. Limpar arquivos temporários
echo "Removendo arquivos temporários..."
find . -name "*.log" -type f -delete
find . -name "*.tmp" -type f -delete
find . -name "ARENA-troca.json" -type f -delete

# 3. Criar ZIP
echo "Criando arquivo ZIP..."
cd ..
zip -r ARENA-download.zip ARENA-ARENA-unificado/ \
    -x "*/jogos/*" \
    -x "*/.git/*" \
    -x "*/__pycache__/*" \
    -x "*/*.log" \
    -x "*/*.tmp"

echo "✅ Pacote criado: ARENA-download.zip"
echo "Tamanho:"
ls -lh ARENA-download.zip

# 4. Instruções para upload
echo ""
echo "=== PRÓXIMOS PASSOS ==="
echo "1. Upload no OneDrive/Google Drive: ARENA-download.zip"
echo "2. Obter link de compartilhamento"
echo "3. Criar GitHub Release e anexar o ZIP"
echo "4. Atualizar README.md com links de download"