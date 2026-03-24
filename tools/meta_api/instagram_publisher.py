"""
instagram_publisher.py — Publicação no Instagram via Graph API
Suporta posts estáticos, carrosséis e Reels.

Uso:
    # Testar conexão:
    python tools/meta_api/instagram_publisher.py --testar

    # Publicar post estático:
    python tools/meta_api/instagram_publisher.py --imagem temp/post.jpg --legenda "Texto..."

    # Via código:
    from tools.meta_api.instagram_publisher import InstagramPublisher
    pub = InstagramPublisher()
    post_id = pub.publicar_estatico("temp/post.jpg", "Legenda aqui")
"""

import argparse
import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

GRAPH_URL = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Limites da API
MAX_HASHTAGS = 30
MAX_POSTS_DIA = 50
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 5  # segundos entre tentativas


# ──────────────────────────────────────────────
# Publisher
# ──────────────────────────────────────────────

class InstagramPublisher:

    def __init__(self):
        if not ACCESS_TOKEN or not ACCOUNT_ID:
            raise EnvironmentError(
                "INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID devem estar no .env"
            )
        self.token = ACCESS_TOKEN
        self.account_id = ACCOUNT_ID

    # ── Publicação: Post Estático ──────────────

    def publicar_estatico(self, caminho_imagem: str, legenda: str,
                           url_imagem: str = None) -> str:
        """
        Publica um post estático (imagem única).

        A Graph API exige que a imagem esteja em uma URL pública.
        Se você tiver apenas o caminho local, use um serviço de hospedagem
        temporária ou passe a url_imagem diretamente.

        Retorna o instagram_post_id publicado.
        """
        if not url_imagem:
            raise ValueError(
                "A Graph API exige uma URL pública da imagem. "
                "Hospede a imagem e passe via url_imagem=..."
            )

        self._validar_legenda(legenda)

        logger.info("Criando container de mídia...")
        container_id = self._criar_container_imagem(url_imagem, legenda)

        logger.info(f"Container criado: {container_id}. Aguardando processamento...")
        self._aguardar_container(container_id)

        logger.info("Publicando...")
        post_id = self._publicar_container(container_id)
        logger.info(f"✅ Post publicado! ID: {post_id}")
        return post_id

    # ── Publicação: Carrossel ──────────────────

    def publicar_carrossel(self, urls_imagens: list[str], legenda: str) -> str:
        """
        Publica um carrossel com múltiplas imagens.
        urls_imagens: lista de URLs públicas de cada slide (mín 2, máx 10).
        Retorna o instagram_post_id publicado.
        """
        if len(urls_imagens) < 2:
            raise ValueError("Carrossel precisa de pelo menos 2 imagens.")
        if len(urls_imagens) > 10:
            raise ValueError("Carrossel suporta no máximo 10 imagens.")

        self._validar_legenda(legenda)

        logger.info(f"Criando {len(urls_imagens)} containers de slide...")
        slide_ids = []
        for i, url in enumerate(urls_imagens, 1):
            slide_id = self._criar_container_imagem(url, legenda=None, is_carousel_item=True)
            slide_ids.append(slide_id)
            logger.info(f"  Slide {i}/{len(urls_imagens)}: {slide_id}")

        logger.info("Criando container do carrossel...")
        carousel_id = self._criar_container_carrossel(slide_ids, legenda)

        logger.info("Aguardando processamento do carrossel...")
        self._aguardar_container(carousel_id)

        logger.info("Publicando carrossel...")
        post_id = self._publicar_container(carousel_id)
        logger.info(f"✅ Carrossel publicado! ID: {post_id}")
        return post_id

    # ── Publicação: Reel ──────────────────────

    def publicar_reel(self, url_video: str, legenda: str,
                      thumb_url: str = None) -> str:
        """
        Publica um Reel.
        url_video: URL pública do vídeo MP4 (máx 100MB, recomendado < 60s).
        Retorna o instagram_post_id publicado.
        """
        self._validar_legenda(legenda)

        logger.info("Criando container de Reel...")
        params = {
            "media_type": "REELS",
            "video_url": url_video,
            "caption": legenda,
            "access_token": self.token,
        }
        if thumb_url:
            params["thumb_offset"] = 0

        resp = self._post(f"{GRAPH_URL}/{self.account_id}/media", params)
        container_id = resp["id"]

        logger.info(f"Container Reel criado: {container_id}. Aguardando processamento (pode demorar)...")
        self._aguardar_container(container_id, max_tentativas=20, intervalo=15)

        logger.info("Publicando Reel...")
        post_id = self._publicar_container(container_id)
        logger.info(f"✅ Reel publicado! ID: {post_id}")
        return post_id

    # ── Testar Conexão ────────────────────────

    def testar_conexao(self) -> dict:
        """Verifica se as credenciais estão funcionando e retorna info da conta."""
        url = f"{GRAPH_URL}/{self.account_id}"
        params = {
            "fields": "id,username,name,followers_count,media_count",
            "access_token": self.token,
        }
        data = self._get(url, params)
        logger.info(f"✅ Conexão OK — @{data.get('username')} | Seguidores: {data.get('followers_count')}")
        return data

    # ── Privados ──────────────────────────────

    def _criar_container_imagem(self, url_imagem: str, legenda: str = None,
                                 is_carousel_item: bool = False) -> str:
        params = {
            "image_url": url_imagem,
            "access_token": self.token,
        }
        if is_carousel_item:
            params["is_carousel_item"] = "true"
        elif legenda:
            params["caption"] = legenda

        resp = self._post(f"{GRAPH_URL}/{self.account_id}/media", params)
        return resp["id"]

    def _criar_container_carrossel(self, slide_ids: list[str], legenda: str) -> str:
        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(slide_ids),
            "caption": legenda,
            "access_token": self.token,
        }
        resp = self._post(f"{GRAPH_URL}/{self.account_id}/media", params)
        return resp["id"]

    def _aguardar_container(self, container_id: str,
                             max_tentativas: int = 10, intervalo: int = 5):
        """Aguarda o container ficar com status FINISHED."""
        url = f"{GRAPH_URL}/{container_id}"
        params = {"fields": "status_code,status", "access_token": self.token}

        for tentativa in range(1, max_tentativas + 1):
            data = self._get(url, params)
            status = data.get("status_code", "")
            logger.debug(f"  Status container ({tentativa}/{max_tentativas}): {status}")

            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Container com erro: {data.get('status')}")

            time.sleep(intervalo)

        raise TimeoutError(f"Container {container_id} não ficou FINISHED em {max_tentativas} tentativas.")

    def _publicar_container(self, container_id: str) -> str:
        params = {
            "creation_id": container_id,
            "access_token": self.token,
        }
        resp = self._post(f"{GRAPH_URL}/{self.account_id}/media_publish", params)
        return resp["id"]

    def _validar_legenda(self, legenda: str):
        hashtags = [p for p in legenda.split() if p.startswith("#")]
        if len(hashtags) > MAX_HASHTAGS:
            raise ValueError(f"Legenda tem {len(hashtags)} hashtags. Máximo permitido: {MAX_HASHTAGS}.")

    def _get(self, url: str, params: dict) -> dict:
        for tentativa in range(1, RETRY_ATTEMPTS + 1):
            try:
                resp = requests.get(url, params=params, timeout=30)
                self._checar_resposta(resp)
                return resp.json()
            except RateLimitError:
                wait = RETRY_BACKOFF * tentativa
                logger.warning(f"Rate limit atingido. Aguardando {wait}s...")
                time.sleep(wait)
            except Exception as e:
                if tentativa == RETRY_ATTEMPTS:
                    raise
                logger.warning(f"Tentativa {tentativa} falhou: {e}. Retentando...")
                time.sleep(RETRY_BACKOFF)

    def _post(self, url: str, params: dict) -> dict:
        for tentativa in range(1, RETRY_ATTEMPTS + 1):
            try:
                resp = requests.post(url, data=params, timeout=30)
                self._checar_resposta(resp)
                return resp.json()
            except RateLimitError:
                wait = RETRY_BACKOFF * tentativa
                logger.warning(f"Rate limit atingido. Aguardando {wait}s...")
                time.sleep(wait)
            except Exception as e:
                if tentativa == RETRY_ATTEMPTS:
                    raise
                logger.warning(f"Tentativa {tentativa} falhou: {e}. Retentando...")
                time.sleep(RETRY_BACKOFF)

    @staticmethod
    def _checar_resposta(resp: requests.Response):
        if resp.status_code == 429:
            raise RateLimitError("Rate limit da API Meta atingido.")
        if resp.status_code >= 400:
            try:
                erro = resp.json().get("error", {})
                msg = erro.get("message", resp.text)
                code = erro.get("code", resp.status_code)
                if code == 190:
                    raise TokenExpiradoError(
                        "Token expirado ou inválido. Renove o INSTAGRAM_ACCESS_TOKEN no .env"
                    )
                raise APIError(f"Erro {code}: {msg}")
            except (ValueError, KeyError):
                raise APIError(f"HTTP {resp.status_code}: {resp.text}")


# ── Exceções customizadas ──────────────────────

class RateLimitError(Exception):
    pass

class TokenExpiradoError(Exception):
    pass

class APIError(Exception):
    pass


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publica no Instagram via Graph API")
    parser.add_argument("--testar", action="store_true", help="Testa a conexão com a API")
    parser.add_argument("--imagem", help="URL pública da imagem para post estático")
    parser.add_argument("--legenda", help="Legenda do post")
    args = parser.parse_args()

    pub = InstagramPublisher()

    if args.testar:
        info = pub.testar_conexao()
        print(f"\nConta: @{info.get('username')}")
        print(f"   Seguidores: {info.get('followers_count')}")
        print(f"   Posts: {info.get('media_count')}")
        print(f"   ID: {info.get('id')}")

    elif args.imagem and args.legenda:
        post_id = pub.publicar_estatico(
            caminho_imagem=args.imagem,
            legenda=args.legenda,
            url_imagem=args.imagem,
        )
        print(f"\n✅ Publicado! Instagram Post ID: {post_id}")

    else:
        parser.print_help()
