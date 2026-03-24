"""
db_manager.py — CRUD PostgreSQL para @cadeiaparamaustratossp
Uso: from tools.db.db_manager import DBManager
"""

import os
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ──────────────────────────────────────────────
# content_ideas
# ──────────────────────────────────────────────

def create_idea(tema: str, formato: str, fonte: str = None,
                score_potencial: int = None, notas: str = None) -> int:
    """Insere uma nova ideia e retorna o id gerado."""
    sql = """
        INSERT INTO content_ideas (tema, formato, fonte, score_potencial, notas)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (tema, formato, fonte, score_potencial, notas))
            return cur.fetchone()[0]


def get_idea(idea_id: int) -> Optional[dict]:
    sql = "SELECT * FROM content_ideas WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (idea_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_ideas(status: str = None, formato: str = None, limit: int = 20) -> list[dict]:
    """Lista ideias com filtros opcionais."""
    conditions, params = [], []
    if status:
        conditions.append("status = %s")
        params.append(status)
    if formato:
        conditions.append("formato = %s")
        params.append(formato)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM content_ideas {where} ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def update_idea_status(idea_id: int, status: str, notas: str = None):
    """Atualiza status e, opcionalmente, as notas de uma ideia."""
    sql = "UPDATE content_ideas SET status = %s" + (", notas = %s" if notas else "") + " WHERE id = %s"
    params = [status, notas, idea_id] if notas else [status, idea_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


def update_idea_score(idea_id: int, score: int, notas: str = None):
    sql = "UPDATE content_ideas SET score_potencial = %s" + (", notas = %s" if notas else "") + " WHERE id = %s"
    params = [score, notas, idea_id] if notas else [score, idea_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


def ideas_by_tema(tema_keyword: str, days: int = 30) -> list[dict]:
    """Retorna ideias com tema similar nos últimos N dias (evitar repetição)."""
    sql = """
        SELECT * FROM content_ideas
        WHERE tema ILIKE %s
          AND created_at >= NOW() - INTERVAL '%s days'
        ORDER BY created_at DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (f"%{tema_keyword}%", days))
            return [dict(r) for r in cur.fetchall()]


# ──────────────────────────────────────────────
# published_posts
# ──────────────────────────────────────────────

def create_published_post(content_idea_id: int, tipo: str, legenda: str,
                           hashtags: list[str], tema: str,
                           score_potencial: int = None,
                           instagram_post_id: str = None) -> int:
    sql = """
        INSERT INTO published_posts
            (instagram_post_id, content_idea_id, tipo, legenda, hashtags,
             data_publicacao, horario, tema, score_potencial)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW()::TIME, %s, %s)
        RETURNING id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (instagram_post_id, content_idea_id, tipo,
                               legenda, hashtags, tema, score_potencial))
            post_id = cur.fetchone()[0]

    update_idea_status(content_idea_id, "publicado")
    return post_id


def get_published_post(post_id: int) -> Optional[dict]:
    sql = "SELECT * FROM published_posts WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (post_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_published_posts(limit: int = 10) -> list[dict]:
    sql = "SELECT * FROM published_posts ORDER BY data_publicacao DESC LIMIT %s"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return [dict(r) for r in cur.fetchall()]


def update_instagram_post_id(post_id: int, instagram_post_id: str):
    sql = "UPDATE published_posts SET instagram_post_id = %s WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (instagram_post_id, post_id))


# ──────────────────────────────────────────────
# post_metrics
# ──────────────────────────────────────────────

def save_metrics(published_post_id: int, medicao: str, impressions: int = 0,
                 reach: int = 0, likes: int = 0, comments: int = 0,
                 shares: int = 0, saves: int = 0, engagement_rate: float = 0.0,
                 profile_visits: int = 0, follows_from_post: int = 0):
    sql = """
        INSERT INTO post_metrics
            (published_post_id, medicao, impressions, reach, likes, comments,
             shares, saves, engagement_rate, profile_visits, follows_from_post)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (published_post_id, medicao) DO UPDATE SET
            impressions = EXCLUDED.impressions,
            reach = EXCLUDED.reach,
            likes = EXCLUDED.likes,
            comments = EXCLUDED.comments,
            shares = EXCLUDED.shares,
            saves = EXCLUDED.saves,
            engagement_rate = EXCLUDED.engagement_rate,
            profile_visits = EXCLUDED.profile_visits,
            follows_from_post = EXCLUDED.follows_from_post,
            collected_at = NOW()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (published_post_id, medicao, impressions, reach,
                               likes, comments, shares, saves, engagement_rate,
                               profile_visits, follows_from_post))


def get_metrics(published_post_id: int) -> list[dict]:
    sql = "SELECT * FROM post_metrics WHERE published_post_id = %s ORDER BY medicao"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (published_post_id,))
            return [dict(r) for r in cur.fetchall()]


def best_posting_hours(limit: int = 3) -> list[dict]:
    """Retorna os horários com maior engagement_rate médio."""
    sql = """
        SELECT
            EXTRACT(HOUR FROM pp.horario) AS hora,
            AVG(pm.engagement_rate) AS media_engagement,
            COUNT(*) AS total_posts
        FROM post_metrics pm
        JOIN published_posts pp ON pp.id = pm.published_post_id
        WHERE pm.medicao = '7d'
        GROUP BY hora
        ORDER BY media_engagement DESC
        LIMIT %s
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return [dict(r) for r in cur.fetchall()]


# ──────────────────────────────────────────────
# hashtags
# ──────────────────────────────────────────────

def upsert_hashtag(tag: str, categoria: str = None):
    """Insere hashtag ou incrementa contador se já existir."""
    sql = """
        INSERT INTO hashtags (tag, vezes_usada, categoria)
        VALUES (%s, 1, %s)
        ON CONFLICT (tag) DO UPDATE SET
            vezes_usada = hashtags.vezes_usada + 1,
            updated_at = NOW()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (tag, categoria))


def update_hashtag_engagement(tag: str, engagement_rate: float):
    """Atualiza a média de engagement de uma hashtag (média móvel simples)."""
    sql = """
        UPDATE hashtags
        SET media_engagement = (media_engagement * (vezes_usada - 1) + %s) / vezes_usada,
            updated_at = NOW()
        WHERE tag = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (engagement_rate, tag))


def top_hashtags(categoria: str = None, limit: int = 20) -> list[dict]:
    """Retorna as hashtags com melhor performance."""
    conditions, params = ["vezes_usada >= 3"], []
    if categoria:
        conditions.append("categoria = %s")
        params.append(categoria)

    sql = f"""
        SELECT tag, vezes_usada, media_engagement, categoria
        FROM hashtags
        WHERE {' AND '.join(conditions)}
        ORDER BY media_engagement DESC, vezes_usada DESC
        LIMIT %s
    """
    params.append(limit)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


# ──────────────────────────────────────────────
# Utilitário: fallback JSON quando DB indisponível
# ──────────────────────────────────────────────

FALLBACK_DIR = "temp"


def save_fallback(data: dict, prefix: str = "fallback"):
    """Salva dados em JSON quando o PostgreSQL está indisponível."""
    os.makedirs(FALLBACK_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(FALLBACK_DIR, f"{prefix}_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.warning(f"PostgreSQL indisponível — dados salvos em {path}")
    return path
