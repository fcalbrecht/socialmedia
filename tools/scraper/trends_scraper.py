"""
trends_scraper.py — Pesquisa de tendências para @cadeiaparamaustratossp
Busca notícias recentes e tendências sobre proteção animal em SP.

Uso:
    python tools/scraper/trends_scraper.py
    ou via código:
        from tools.scraper.trends_scraper import TrendsScraper
        scraper = TrendsScraper()
        results = scraper.run()
"""

import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime

from duckduckgo_search import DDGS
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao path para importar db_manager
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


# ──────────────────────────────────────────────
# Configuração de busca
# ──────────────────────────────────────────────

# Termos de busca por categoria
SEARCH_QUERIES = {
    "maus_tratos_sp": [
        "maus-tratos animais São Paulo",
        "crueldade animal SP preso",
        "resgate animal São Paulo",
        "abandono animal SP flagrante",
    ],
    "legislacao": [
        "Lei Sansão maus-tratos animais",
        "projeto lei proteção animal Brasil",
        "crime maus-tratos animal pena",
        "cadeia maus-tratos animal 2025",
    ],
    "casos_nacionais": [
        "maus-tratos animal Brasil notícia",
        "crueldade animal resgate Brasil",
        "animal maltratado denúncia Brasil",
    ],
    "datas_comemorativas": [
        "dia dos animais proteção animal",
        "semana animal direitos",
    ],
}

# Hashtags do nicho para monitorar
HASHTAGS_NICHO = [
    "#CadeiaParaMausTratos",
    "#DireitosAnimais",
    "#ProteçãoAnimal",
    "#LeiSansao",
    "#MausTratos",
    "#ResgateAnimal",
    "#AdoteNaoCompre",
    "#TodosContraAMaustratos",
    "#AnimalAbuse",
    "#DirectorsAnimais",
]

# Perfis de referência (para contexto editorial)
PERFIS_REFERENCIA = [
    "@del.brunolima",
    "@cadeiaparamaustratos",
    "@cadeiaparamaustratos_sumare",
]


# ──────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────

@dataclass
class NoticiaEncontrada:
    titulo: str
    resumo: str
    url: str
    fonte: str
    data: str
    categoria: str
    relevancia: int = 0  # 0-3: quantos termos-chave batem


@dataclass
class ResultadoPesquisa:
    noticias: list[NoticiaEncontrada] = field(default_factory=list)
    total_encontrado: int = 0
    executado_em: str = field(default_factory=lambda: datetime.now().isoformat())
    erros: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# Scraper principal
# ──────────────────────────────────────────────

class TrendsScraper:

    # Palavras-chave que aumentam a relevância de uma notícia
    PALAVRAS_ALTA_RELEVANCIA = [
        "são paulo", "sp", "preso", "flagrante", "resgate", "lei sansão",
        "cadeia", "multa", "delegacia", "depa", "ibama", "procon",
        "operação", "ministério público",
    ]
    PALAVRAS_BAIXA_RELEVANCIA = [
        "meme", "viral", "celebridade", "famoso", "humor",
    ]

    def __init__(self, max_results_per_query: int = 5):
        self.max_results = max_results_per_query
        self.ddgs = DDGS()

    def _calcular_relevancia(self, titulo: str, resumo: str) -> int:
        texto = (titulo + " " + resumo).lower()
        score = sum(1 for p in self.PALAVRAS_ALTA_RELEVANCIA if p in texto)
        score -= sum(2 for p in self.PALAVRAS_BAIXA_RELEVANCIA if p in texto)
        return max(0, min(score, 3))

    def _buscar_noticias(self, query: str, categoria: str) -> list[NoticiaEncontrada]:
        noticias = []
        try:
            resultados = self.ddgs.news(
                query,
                max_results=self.max_results,
                region="br-pt",
                safesearch="moderate",
            )
            for r in resultados:
                noticia = NoticiaEncontrada(
                    titulo=r.get("title", ""),
                    resumo=r.get("body", ""),
                    url=r.get("url", ""),
                    fonte=r.get("source", ""),
                    data=r.get("date", ""),
                    categoria=categoria,
                    relevancia=self._calcular_relevancia(
                        r.get("title", ""), r.get("body", "")
                    ),
                )
                noticias.append(noticia)
        except Exception as e:
            logger.warning(f"Erro ao buscar '{query}': {e}")
        return noticias

    def run(self) -> ResultadoPesquisa:
        resultado = ResultadoPesquisa()
        vistas = set()  # evitar duplicatas por URL

        for categoria, queries in SEARCH_QUERIES.items():
            for query in queries:
                logger.info(f"Buscando: {query}")
                noticias = self._buscar_noticias(query, categoria)
                for n in noticias:
                    if n.url not in vistas and n.relevancia >= 0:
                        vistas.add(n.url)
                        resultado.noticias.append(n)

        # Ordenar por relevância (maior primeiro)
        resultado.noticias.sort(key=lambda n: n.relevancia, reverse=True)
        resultado.total_encontrado = len(resultado.noticias)
        return resultado

    def formatar_para_agente(self, resultado: ResultadoPesquisa) -> str:
        """Formata o resultado como texto estruturado para o agente."""
        if not resultado.noticias:
            return "Nenhuma notícia relevante encontrada. Sugerir tema evergreen."

        linhas = [
            f"## Tendências encontradas ({resultado.total_encontrado} notícias)",
            f"_Pesquisa executada em: {resultado.executado_em}_",
            "",
        ]

        # Top 10 por relevância
        for i, n in enumerate(resultado.noticias[:10], 1):
            linhas += [
                f"### {i}. {n.titulo}",
                f"**Categoria:** {n.categoria} | **Relevância:** {'★' * n.relevancia}{'☆' * (3 - n.relevancia)}",
                f"**Fonte:** {n.fonte} | **Data:** {n.data}",
                f"**Resumo:** {n.resumo[:200]}..." if len(n.resumo) > 200 else f"**Resumo:** {n.resumo}",
                f"**URL:** {n.url}",
                "",
            ]

        if resultado.erros:
            linhas.append(f"⚠️ Erros durante a pesquisa: {'; '.join(resultado.erros)}")

        return "\n".join(linhas)

    def salvar_ideias_no_db(self, resultado: ResultadoPesquisa) -> list[int]:
        """
        Converte as notícias mais relevantes em ideias no PostgreSQL.
        Retorna lista de IDs criados.
        """
        try:
            from tools.db.db_manager import create_idea, ideas_by_tema, save_fallback
            use_db = True
        except Exception as e:
            logger.warning(f"DB indisponível: {e}")
            use_db = False

        ids_criados = []
        for n in resultado.noticias[:5]:  # salvar apenas top 5
            if n.relevancia < 1:
                continue

            # Mapear relevância para score preliminar (será refinado pelo Growth Hacker)
            score_inicial = 40 + (n.relevancia * 15)

            # Determinar formato sugerido baseado na categoria
            formato = "carrossel" if n.categoria == "legislacao" else "estatico"

            dados = {
                "tema": n.titulo,
                "formato": formato,
                "fonte": n.fonte,
                "score_potencial": score_inicial,
                "notas": f"URL: {n.url}\nResumo: {n.resumo[:300]}",
            }

            if use_db:
                # Verificar se tema similar já existe (últimos 30 dias)
                similares = ideas_by_tema(n.titulo[:30], days=30)
                if similares:
                    logger.info(f"Tema similar já existe no DB: {n.titulo[:50]}")
                    continue
                try:
                    idea_id = create_idea(**dados)
                    ids_criados.append(idea_id)
                    logger.info(f"Ideia criada no DB: id={idea_id} | {n.titulo[:50]}")
                except Exception as e:
                    logger.error(f"Erro ao salvar ideia: {e}")
                    save_fallback(dados, prefix="idea_fallback")
            else:
                # Fallback: salvar em JSON
                from tools.db.db_manager import save_fallback
                save_fallback(dados, prefix="idea_fallback")

        return ids_criados


# ──────────────────────────────────────────────
# Entry point para execução direta
# ──────────────────────────────────────────────

if __name__ == "__main__":
    scraper = TrendsScraper(max_results_per_query=5)

    print("🔍 Pesquisando tendências sobre proteção animal...\n")
    resultado = scraper.run()

    print(scraper.formatar_para_agente(resultado))
    print(f"\n📊 Total de notícias coletadas: {resultado.total_encontrado}")

    salvar = input("\nDeseja salvar as top ideias no PostgreSQL? (s/n): ").strip().lower()
    if salvar == "s":
        ids = scraper.salvar_ideias_no_db(resultado)
        if ids:
            print(f"✅ {len(ids)} ideias salvas no banco. IDs: {ids}")
        else:
            print("⚠️ Nenhuma ideia nova salva (já existentes ou DB indisponível).")
