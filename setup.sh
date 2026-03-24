#!/bin/bash
# setup.sh — Configuração do ambiente no Ubuntu 24.04 LTS
# Projeto: @cadeiaparamaustratossp
# Uso: bash setup.sh

set -e  # Para em qualquer erro

echo "================================================"
echo " Setup: @cadeiaparamaustratossp"
echo " Ubuntu 24.04 LTS"
echo "================================================"

# ── 1. Atualizar sistema ──────────────────────────
echo ""
echo "[1/7] Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# ── 2. Instalar dependências do sistema ───────────
echo ""
echo "[2/7] Instalando dependências do sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    ffmpeg \
    curl \
    git \
    build-essential \
    libpq-dev

# ── 3. Criar ambiente virtual Python ─────────────
echo ""
echo "[3/7] Criando ambiente virtual Python..."
python3 -m venv .venv
source .venv/bin/activate

# ── 4. Instalar dependências Python ──────────────
echo ""
echo "[4/7] Instalando dependências Python..."
pip install --upgrade pip
pip install \
    psycopg2-binary \
    python-dotenv \
    requests \
    Pillow \
    duckduckgo-search

# ── 5. Configurar PostgreSQL ──────────────────────
echo ""
echo "[5/7] Configurando PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar usuário e banco (ignora erro se já existir)
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'Latvij@1918';" 2>/dev/null || echo "  Usuário postgres já existe, pulando..."
sudo -u postgres psql -c "CREATE DATABASE socialmedia OWNER postgres;" 2>/dev/null || echo "  Banco socialmedia já existe, pulando..."

# Aplicar schema
echo "  Aplicando schema do banco..."
sudo -u postgres psql -d socialmedia -f tools/db/schema.sql
echo "  Schema aplicado."

# ── 6. Configurar Nginx para servir imagens ───────
echo ""
echo "[6/7] Configurando Nginx..."

# Criar pasta de imagens públicas
mkdir -p /var/www/socialmedia/images
sudo chown -R $USER:$USER /var/www/socialmedia

# Criar config do Nginx
sudo tee /etc/nginx/sites-available/socialmedia > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    location /images/ {
        alias /var/www/socialmedia/images/;
        expires 1d;
        add_header Cache-Control "public";
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/socialmedia /etc/nginx/sites-enabled/socialmedia
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl enable nginx

echo "  Nginx configurado. Imagens servidas em: http://IP_DO_VPS/images/"

# ── 7. Criar pastas necessárias ───────────────────
echo ""
echo "[7/7] Criando estrutura de pastas..."
mkdir -p temp
mkdir -p brand_assets/logos

# ── Concluído ─────────────────────────────────────
echo ""
echo "================================================"
echo " Setup concluído!"
echo ""
echo " Próximos passos:"
echo "  1. Copie o .env para este diretório"
echo "     scp .env usuario@VPS:/caminho/socialmedia/.env"
echo ""
echo "  2. Ative o ambiente virtual sempre que usar:"
echo "     source .venv/bin/activate"
echo ""
echo "  3. Teste a conexão com a API:"
echo "     python tools/meta_api/instagram_publisher.py --testar"
echo ""
echo "  4. Para servir imagens publicamente, copie para:"
echo "     /var/www/socialmedia/images/"
echo "================================================"
