"""
instagram_insights.py — Coleta de métricas via Graph API para @cadeiaparamaustratossp
Coleta métricas em 3 momentos: 24h, 48h e 7 dias após publicação.

Uso:
    # Coletar métricas de um post específico:
    python tools/meta_api/instagram_insights.py --post-id 17846368219941196 --medicao 24h

    # Coletar métricas pendentes de todos os posts:
    python tools/meta_api/instagram_insights.py --coletar-pendentes

    # Via código:
    from tools.meta_api.instagram_insights import InstagramInsights
    insights = InstagramInsights()
    metricas = insights.coletar_post(instagram_post_id, medicao="24h")
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

GRAPH_URL = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Métricas disponíveis na Graph API para posts de mídia
METRICAS_POST = [
    "impressions",
    "reach",
    "likes",
    "comments",
    "shares",
    "saved",
    "profile_visits",
    "follows",
    "total_interactions",
]


class InstagramInsights:

    def __init__(self):
        if not ACCESS_TOKEN or not ACCOUNT_ID:
            raise EnvironmentError(
                "INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID devem estar no .env"
            )
        self.token = ACCESS_TOKEN
        self.account_id = ACCOUNT_ID

    # ── Métricas de um post ───────────────────

    def coletar_post(self, instagram_post_id: str, medicao: str) -> dict:
        """
        Coleta métricas de um post específico.

        Args:
            instagram_post_id: ID do post no Instagram (campo instagram_post_id no DB).
            medicao: '24h', '48h' ou '7d' — apenas para registrar no banco.

        Returns:
            dict com todas as métricas coletadas.
        """
        url = f"{GRAPH_URL}/{instagram_post_id}/insights"
        params = {
            "metric": ",".join(METRICAS_POST),
            "access_token": self.token,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            self._checar_resposta(resp)
            data = resp.json()
        except Exception as e:
            logger.error(f"Erro ao coletar insights do post {instagram_post_id}: {e}")
            raise

        metricas = self._parsear_metricas(data)
        metricas["medicao"] = medicao
        metricas["instagram_post_id"] = instagram_post_id
        metricas["coletado_em"] = datetime.now().isoformat()

        logger.info(
            f"📊 Métricas [{medicao}] post {instagram_post_id}: "
            f"reach={metricas.get('reach', 0)}, "
            f"likes={metricas.get('likes', 0)}, "
            f"saves={metricas.get('saved', 0)}"
        )
        return metricas

    def salvar_metricas_no_db(self, published_post_id: int,
                               instagram_post_id: str, medicao: str):
        """
        Coleta métricas e salva diretamente no PostgreSQL.
        published_post_id: ID na tabela published_posts do banco.
        """
        from tools.db.db_manager import save_metrics, save_fallback

        metricas = self.coletar_post(instagram_post_id, medicao)

        reach = metricas.get("reach", 0)
        likes = metricas.get("likes", 0)
        comments = metricas.get("comments", 0)
        saves = metricas.get("saved", 0)
        engagement_rate = self._calcular_engagement(reach, likes, comments, saves)

        try:
            save_metrics(
                published_post_id=published_post_id,
                medicao=medicao,
                impressions=metricas.get("impressions", 0),
                reach=reach,
                likes=likes,
                comments=comments,
                shares=metricas.get("shares", 0),
                saves=saves,
                engagement_rate=engagement_rate,
                profile_visits=metricas.get("profile_visits", 0),
                follows_from_post=metricas.get("follows", 0),
            )
            logger.info(f"✅ Métricas [{medicao}] salvas no banco para post DB id={published_post_id}")
        except Exception as e:
            logger.error(f"Erro ao salvar no DB: {e}. Salvando fallback JSON...")
            save_fallback(
                {"published_post_id": published_post_id, "medicao": medicao, **metricas},
                prefix="metrics_fallback",
            )

    # ── Coletar todos os pendentes ────────────

    def coletar_pendentes(self):
        """
        Verifica quais posts precisam de coleta (24h, 48h ou 7d) e coleta automaticamente.
        Consulta published_posts no PostgreSQL e verifica quais medições ainda não foram feitas.
        """
        from tools.db.db_manager import list_published_posts, get_metrics

        posts = list_published_posts(limit=50)
        agora = datetime.now()
        coletados = 0

        for post in posts:
            if not post.get("instagram_post_id"):
                continue

            data_pub = post["data_publicacao"]
            if isinstance(data_pub, str):
                data_pub = datetime.fromisoformat(data_pub)

            horas_desde_pub = (agora - data_pub).total_seconds() / 3600
            metricas_existentes = {m["medicao"] for m in get_metrics(post["id"])}

            medicoes_necessarias = []
            if horas_desde_pub >= 24 and "24h" not in metricas_existentes:
                medicoes_necessarias.append("24h")
            if horas_desde_pub >= 48 and "48h" not in metricas_existentes:
                medicoes_necessarias.append("48h")
            if horas_desde_pub >= 168 and "7d" not in metricas_existentes:  # 7 * 24
                medicoes_necessarias.append("7d")

            for medicao in medicoes_necessarias:
                logger.info(f"Coletando [{medicao}] para post DB id={post['id']}...")
                try:
                    self.salvar_metricas_no_db(
                        published_post_id=post["id"],
                        instagram_post_id=post["instagram_post_id"],
                        medicao=medicao,
                    )
                    coletados += 1
                except Exception as e:
                    logger.error(f"Falha ao coletar [{medicao}] post {post['id']}: {e}")

        logger.info(f"✅ Coleta de pendentes concluída. {coletados} medições salvas.")
        return coletados

    # ── Insights da conta (perfil) ────────────

    def insights_perfil(self, periodo: str = "day") -> dict:
        """
        Retorna métricas gerais do perfil (alcance, impressões, novos seguidores).
        periodo: 'day', 'week' ou 'month'
        """
        url = f"{GRAPH_URL}/{self.account_id}/insights"
        params = {
            "metric": "reach,impressions,follower_count,profile_views",
            "period": periodo,
            "access_token": self.token,
        }
        resp = requests.get(url, params=params, timeout=30)
        self._checar_resposta(resp)
        return self._parsear_metricas(resp.json())

    def resumo_performance(self, limite_posts: int = 10) -> str:
        """
        Gera um resumo textual de performance dos últimos posts — útil para o agente.
        """
        from tools.db.db_manager import list_published_posts, get_metrics

        posts = list_published_posts(limit=limite_posts)
        if not posts:
            return "Nenhum post publicado encontrado no banco de dados."

        linhas = [f"## Resumo de Performance — Últimos {len(posts)} posts\n"]
        for post in posts:
            metricas = get_metrics(post["id"])
            m7d = next((m for m in metricas if m["medicao"] == "7d"), None)
            m_mais_recente = metricas[-1] if metricas else None
            m = m7d or m_mais_recente

            if m:
                linhas.append(
                    f"**{post['tema'][:50]}** ({post['tipo']}) — "
                    f"publicado {post['data_publicacao']}\n"
                    f"  reach={m['reach']} | likes={m['likes']} | "
                    f"saves={m['saves']} | engagement={m['engagement_rate']}% "
                    f"[{m['medicao']}]\n"
                )
            else:
                linhas.append(
                    f"**{post['tema'][:50]}** ({post['tipo']}) — métricas ainda não coletadas\n"
                )

        return "\n".join(linhas)

    # ── Privados ──────────────────────────────

    @staticmethod
    def _parsear_metricas(data: dict) -> dict:
        resultado = {}
        for item in data.get("data", []):
            nome = item.get("name")
            values = item.get("values", [])
            if values:
                resultado[nome] = values[-1].get("value", 0)
            else:
                resultado[nome] = item.get("value", 0)
        return resultado

    @staticmethod
    def _calcular_engagement(reach: int, likes: int,
                              comments: int, saves: int) -> float:
        if reach == 0:
            return 0.0
        return round(((likes + comments + saves) / reach) * 100, 2)

    @staticmethod
    def _checar_resposta(resp: requests.Response):
        if resp.status_code == 429:
            raise RuntimeError("Rate limit da API Meta atingido.")
        if resp.status_code >= 400:
            try:
                erro = resp.json().get("error", {})
                code = erro.get("code", resp.status_code)
                msg = erro.get("message", resp.text)
                if code == 190:
                    raise RuntimeError(
                        "Token expirado. Renove o INSTAGRAM_ACCESS_TOKEN no .env"
                    )
                raise RuntimeError(f"Erro {code}: {msg}")
            except (ValueError, KeyError):
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta métricas do Instagram via Graph API")
    parser.add_argument("--post-id", help="Instagram Post ID para coletar métricas")
    parser.add_argument("--medicao", choices=["24h", "48h", "7d"], default="24h")
    parser.add_argument("--coletar-pendentes", action="store_true",
                        help="Coleta todas as medições pendentes do banco")
    parser.add_argument("--resumo", action="store_true",
                        help="Exibe resumo de performance dos últimos posts")
    args = parser.parse_args()

    insights = InstagramInsights()

    if args.post_id:
        metricas = insights.coletar_post(args.post_id, args.medicao)
        print(f"\n📊 Métricas [{args.medicao}] do post {args.post_id}:")
        for k, v in metricas.items():
            print(f"   {k}: {v}")

    elif args.coletar_pendentes:
        total = insights.coletar_pendentes()
        print(f"\n✅ {total} medições coletadas e salvas.")

    elif args.resumo:
        print(insights.resumo_performance())

    else:
        parser.print_help()
