# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Identidade do Projeto

Automação de marketing digital para o perfil **@cadeiaparamaustratossp** no Instagram — causa de proteção animal e endurecimento de penas contra maus-tratos, ligada ao movimento nacional **Cadeia para Maus-Tratos** (Dep. Fed. Delegado Bruno Lima).

**Missão:** Ser a maior referência digital contra maus-tratos no estado de SP.
**Frequência:** 1 post/dia. **Formatos (prioridade):** Posts estáticos > Carrosséis > Reels.

---

## Estado Atual do Projeto (Março/2026)

O projeto está na **fase de estruturação**. Os diretórios `workflows/`, `tools/`, `brand_assets/` e `temp/` ainda não foram criados. A pasta `references/` existe e contém os documentos de contexto. Ao criar ferramentas ou workflows, seguir a estrutura definida na seção de arquitetura abaixo.

---

## Framework WAT (Arquitetura Central)

- **Workflows** (`/workflows/`): SOPs em Markdown. Definem objetivo, inputs, ferramentas e tratamento de erros.
- **Agent (Você)**: Lê workflows, toma decisões, aciona ferramentas na ordem correta.
- **Tools** (`/tools/`): Scripts Python para ações atômicas (Meta API, geração de imagens, DB, scraping).

**Regra de Planejamento:** Antes de qualquer código ou arquivo, atue em Modo de Planejamento, crie uma to-do list e busque ferramentas existentes antes de criar novas.

---

## Agentes Especialistas

Delegue para os agentes em `~/.claude/agents/`:

| Agente | Responsabilidade | Modelo |
|---|---|---|
| **Growth Hacker** | Tendências, análise de concorrência, Score de Potencial, experimentos | Sonnet (análise) / Haiku (scraping) |
| **Content Creator** | Legendas, roteiros de Reels, copy de carrosséis | Sonnet / Opus (campanhas) |
| **Instagram Curator** | Validação visual, consistência de grid, checklist técnico | Sonnet |

**Regra de modelo:** Pesquisa massiva e triagem → Haiku. Raciocínio estratégico e criação → Sonnet/Opus.

Detalhes de delegação e prompts em `/references/regras_agentes.md`.

---

## Skills (Camada de Referência)

**Regra absoluta:** Nenhum conteúdo gerado sem consultar a skill relevante primeiro.

| Tarefa | Skill a consultar |
|---|---|
| Estratégia orgânica, calendário editorial | `social-content` |
| Legendas, CTAs, ganchos | `copywriting` (framework **PAS** prioritário para causa social) |
| Anúncios pagos (fase futura) | `ad-creative` |

Skills em `~/.claude/agents/skills/`. Regras em `/references/regras_skills.md`.

---

## Pipeline de Conteúdo

```
[IDEAÇÃO] → [AVALIAÇÃO/SCORE] → [CRIAÇÃO] → [VALIDAÇÃO VISUAL] → [APROVAÇÃO HUMANA] → [PUBLICAÇÃO] → [ANÁLISE]
     ↑_______________________________RETROALIMENTAÇÃO_______________________________________________|
```

Quando o usuário sugerir um tema, calcular **Score de Potencial (0-100)**:
- Relevância para a causa (0-25 pts)
- Timing/tendência (0-25 pts)
- Potencial de engajamento (0-25 pts)
- Viabilidade de produção (0-25 pts)

| Score | Ação |
|---|---|
| 80-100 | Prosseguir para criação |
| 60-79 | Prosseguir com ajustes sugeridos |
| 40-59 | Apresentar alternativas |
| 0-39 | Não recomendado — propor outro tema |

Fluxo detalhado em `/references/pipeline_instagram.md`.

---

## Ferramentas Python (a criar em `/tools/`)

```
tools/
├── db/db_manager.py              ← CRUD PostgreSQL (posts, métricas, hashtags, ideias)
├── meta_api/instagram_publisher.py   ← Publicação via Graph API
├── meta_api/instagram_insights.py    ← Coleta de métricas (24h / 48h / 7d)
├── scraper/trends_scraper.py     ← Tendências de hashtags e perfis concorrentes
├── image_gen/image_processor.py  ← Redimensionamento e validação de assets
└── video/reel_processor.py       ← Edição básica com FFmpeg
```

Credenciais Meta API e PostgreSQL **exclusivamente via `.env`** (nunca no código).

---

## Banco de Dados PostgreSQL

Quatro tabelas principais:

```sql
content_ideas      -- id, tema, formato, score_potencial, status, fonte
published_posts    -- id, instagram_post_id, content_idea_id, tipo, legenda, hashtags, data_publicacao
post_metrics       -- id, published_post_id, medicao (24h/48h/7d), impressions, reach, likes, comments, shares, saves, engagement_rate
hashtags           -- id, tag, vezes_usada, media_engagement, categoria
```

Schema completo em `/references/pipeline_instagram.md` (Seção 10).

---

## Limites da Graph API do Instagram

- Máximo 50 posts/dia (recomendado: 1-3/dia).
- Máximo 30 hashtags/post (recomendado: 15-20).
- Rate limit: 200 chamadas/hora por token.
- Imagens: JPEG/PNG até 8MB. Vídeos: MP4 até 100MB.
- Dimensões: 1080x1080px (feed quadrado), 1080x1350px (retrato), 1080x1920px (Reels).

---

## Regras Editoriais Inegociáveis

- **NUNCA** publicar imagens gráficas de animais em sofrimento.
- **NUNCA** expor menores de idade.
- **NUNCA** incitar violência contra agressores.
- Tom: firme e indignado ao denunciar, acolhedor ao mostrar resgates. Sempre informativo e embasado.
- Hashtags fixas: `#CadeiaParaMausTratos #DireitosAnimais #ProteçãoAnimal`
- CTAs preferidos: "Compartilhe para mais pessoas saberem", "Denuncie pelo 190", "Siga para se manter informado"

---

## Self-Healing (Autocura)

Ao encontrar erro em ferramenta ou API:
1. Leia o erro → pesquise documentação → corrija o script em `/tools/`.
2. Após corrigir, **atualize o workflow correspondente** para prevenir recorrência.
3. Registre o aprendizado na memória local.

| Erro comum | Ação |
|---|---|
| 429 (rate limit Meta) | Aguardar header `Retry-After`, retry com backoff exponencial |
| Token expirado | Notificar usuário para renovar no `.env` |
| PostgreSQL indisponível | Fallback para JSON temporário em `temp/` |
| Puppeteer timeout | Retry até 3x, logar em `temp/` |

---

## Mapa de Referências

| Preciso de... | Arquivo |
|---|---|
| Fluxo completo de produção | `/references/pipeline_instagram.md` |
| Contexto da causa / movimento | `/references/contexto_negocio.md` |
| Identidade visual e tom de voz | `/references/diretrizes_marca.md` |
| Base de conhecimento do movimento | `/references/cadeia_maus_tratos.md` |
| Regras de sub-agentes e delegação | `/references/regras_agentes.md` |
| Regras para criação/uso de skills | `/references/regras_skills.md` |
