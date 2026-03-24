# Pipeline de Produção de Conteúdo: Instagram (@cadeiaparamaustratossp)

## 1. Visão Geral do Ciclo
Este documento detalha o fluxo completo de operação do sistema de automação de conteúdo para Instagram, desde a ideação até a análise pós-publicação.

```
[IDEAÇÃO] → [AVALIAÇÃO] → [CRIAÇÃO] → [VALIDAÇÃO VISUAL] → [APROVAÇÃO] → [PUBLICAÇÃO] → [ANÁLISE]
    ↑                                                                                         |
    └─────────────────────── RETROALIMENTAÇÃO ────────────────────────────────────────────────┘
```

---

## 2. Etapa 1: Ideação e Pesquisa de Tendências

### 2.1 Fontes de Ideação
- **Usuário sugere tema:** O sistema avalia o potencial antes de prosseguir.
- **Pesquisa automatizada:** O Growth Hacker utiliza `tools/scraper/trends_scraper.py` para monitorar:
  - Hashtags em alta no nicho animal/proteção (#cadeiaparamaustratos, #direitosanimais, #adoteNãoCompre, etc.)
  - Conteúdo viral de perfis referência no nicho.
  - Notícias recentes sobre maus-tratos ou legislação animal (foco SP, depois Brasil, depois mundo).
  - Datas comemorativas relevantes (Dia dos Animais, datas legislativas, etc.)

### 2.2 Banco de Ideias (PostgreSQL)
Todas as ideias são armazenadas na tabela `content_ideas` com campos:
- `id`, `tema`, `formato` (estático/carrossel/reel), `fonte`, `score_potencial`, `status` (pendente/aprovado/descartado/publicado), `data_criacao`, `data_publicacao`, `notas`.

### 2.3 Agente Responsável
- **Growth Hacker** → pesquisa tendências, analisa concorrência, sugere ganchos.
- **Skill consultada:** `social-content` para verificar alinhamento com calendário editorial.

---

## 3. Etapa 2: Avaliação de Conteúdo (Score de Potencial)

### 3.1 Quando o Usuário Sugere um Conteúdo
O sistema executa uma avaliação estruturada:

1. **Relevância para a causa (0-25 pts):** O tema está alinhado com proteção animal e endurecimento de penas?
2. **Timing e tendência (0-25 pts):** O tema é atual? Existe buzz nas redes? É uma data relevante?
3. **Potencial de engajamento (0-25 pts):** O tema gera emoção, indignação, esperança? Tem potencial de compartilhamento?
4. **Viabilidade de produção (0-25 pts):** Temos assets? O formato é adequado? É factível no prazo?

**Score final = soma dos 4 critérios (0-100)**

| Score    | Ação                                                    |
|----------|---------------------------------------------------------|
| 80-100   | Aprovado. Prosseguir para criação imediatamente.        |
| 60-79    | Aprovado com ajustes. Sugerir melhorias antes de criar.  |
| 40-59    | Duvidoso. Apresentar alternativas ao usuário.            |
| 0-39     | Não recomendado. Explicar motivos e propor outro tema.   |

### 3.2 Sugestões de Melhoria
Para qualquer score, o sistema DEVE sugerir:
- Ajustes no ângulo/abordagem do tema.
- Melhor formato (estático vs carrossel vs reel) para o tema.
- Hashtags recomendadas baseadas no histórico do PostgreSQL.
- Melhor horário de publicação baseado em dados de insights.

---

## 4. Etapa 3: Criação de Conteúdo

### 4.1 Posts Estáticos (Formato Principal)
**Agentes:** Content Creator (copy) + Instagram Curator (visual).
**Skills:** `copywriting` (framework PAS prioritário para causa social) + `social-content`.

**Entregáveis:**
- Imagem no formato 1080x1080px (feed) ou 1080x1350px (retrato).
- Legenda com: gancho emocional + informação/dado + CTA + hashtags (máx 30).
- Texto alternativo (alt text) para acessibilidade.

### 4.2 Carrosséis Educativos
**Estrutura recomendada (5-10 slides):**
1. Capa com gancho forte (pergunta ou dado chocante).
2. Contextualização do problema.
3-8. Informação educativa, dados, exemplos.
9. CTA de engajamento ("Salve para consultar depois").
10. CTA final (seguir, compartilhar, denunciar).

**Formato:** 1080x1350px por slide. Consistência visual obrigatória entre slides.

### 4.3 Reels
**Agentes:** Content Creator (roteiro) + Instagram Curator (validação visual).
**Ferramenta:** `tools/video/reel_processor.py` (FFmpeg).

**Estrutura recomendada:**
- Duração: 15-30s para maior alcance.
- Gancho nos primeiros 3 segundos.
- Formato vertical 1080x1920px.
- Legenda embutida no vídeo (acessibilidade).

---

## 5. Etapa 4: Validação Visual

### 5.1 Checklist Automático
Antes de aprovar qualquer asset visual, o Instagram Curator verifica:
- [ ] Dimensões corretas para o formato escolhido.
- [ ] Paleta de cores conforme `/brand_assets/paleta_cores.md`.
- [ ] Logo posicionado conforme diretrizes em `/references/diretrizes_marca.md`.
- [ ] Texto legível em dispositivos móveis (tamanho mínimo de fonte).
- [ ] Consistência com os últimos 9 posts do grid (harmonia visual).

### 5.2 Validação com Puppeteer
O script `tools/scraper/grid_validator.py` utiliza Puppeteer para:
- Capturar screenshot do grid atual do Instagram.
- Simular como o novo post ficará no grid.
- Verificar se a composição geral mantém a identidade visual.

---

## 6. Etapa 5: Aprovação Humana
O sistema SEMPRE apresenta o conteúdo final para aprovação do usuário antes de publicar:
- Preview da imagem/carrossel/reel.
- Legenda completa com hashtags.
- Score de potencial e justificativa.
- Sugestão de horário de publicação.

**O usuário pode:** Aprovar, Solicitar ajustes, ou Descartar.

---

## 7. Etapa 6: Publicação

### 7.1 Ferramenta de Publicação
`tools/meta_api/instagram_publisher.py` utiliza a Graph API da Meta.

### 7.2 Limites da Graph API do Instagram
- **Publicações:** Máximo de 50 posts por dia (recomendado: 1-3 posts/dia para não saturar).
- **Hashtags:** Máximo de 30 por post (recomendado: 15-20 relevantes).
- **Rate Limiting:** Respeitar limites de 200 chamadas/hora por token de acesso.
- **Formatos aceitos:** JPEG, PNG (imagens); MP4 (vídeos, máx 60min, recomendado < 60s para Reels).
- **Tamanho máximo:** Imagens até 8MB; Vídeos até 100MB.

### 7.3 Registro no PostgreSQL
Após publicação, salvar na tabela `published_posts`:
- `id`, `instagram_post_id`, `tipo` (estático/carrossel/reel), `legenda`, `hashtags`, `data_publicacao`, `horario`, `tema`, `score_potencial`, `content_idea_id`.

---

## 8. Etapa 7: Análise e Retroalimentação

### 8.1 Coleta de Métricas
`tools/meta_api/instagram_insights.py` coleta dados em 3 momentos:
- **24 horas** após publicação (engajamento inicial).
- **48 horas** (estabilização).
- **7 dias** (performance consolidada).

### 8.2 Métricas Coletadas
Salvas na tabela `post_metrics`:
- `impressions`, `reach`, `likes`, `comments`, `shares`, `saves`, `engagement_rate`, `profile_visits`, `follows_from_post`.

### 8.3 Retroalimentação
O sistema usa os dados de métricas para:
- Atualizar o modelo de score de potencial (quais temas/formatos performam melhor).
- Alimentar o Growth Hacker com dados reais para sugestões futuras.
- Identificar melhores horários de publicação.
- Registrar aprendizados na memória local (`MEMORY.md`).

---

## 9. Autocura (Self-Healing) Específica

| Erro                                | Ação                                                        |
|-------------------------------------|-------------------------------------------------------------|
| API Meta retorna 429 (rate limit)   | Aguardar tempo indicado no header, retry com backoff.       |
| Imagem rejeitada pela API           | Verificar dimensões/formato, reprocessar, tentar novamente. |
| Token expirado                      | Notificar usuário para renovar token no `.env`.             |
| Puppeteer timeout                   | Aumentar timeout, retry até 3x, logar erro em `temp/`.     |
| PostgreSQL indisponível             | Fallback para arquivo JSON temporário em `temp/`.           |

Após resolver qualquer erro, **atualizar o workflow correspondente** e **registrar na memória**.

---

## 10. Esquema do Banco de Dados PostgreSQL

```sql
-- Tabela de ideias de conteúdo
CREATE TABLE content_ideas (
    id SERIAL PRIMARY KEY,
    tema TEXT NOT NULL,
    formato VARCHAR(20) CHECK (formato IN ('estatico', 'carrossel', 'reel')),
    fonte VARCHAR(50),
    score_potencial INTEGER CHECK (score_potencial BETWEEN 0 AND 100),
    status VARCHAR(20) DEFAULT 'pendente',
    notas TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de posts publicados
CREATE TABLE published_posts (
    id SERIAL PRIMARY KEY,
    instagram_post_id VARCHAR(100),
    content_idea_id INTEGER REFERENCES content_ideas(id),
    tipo VARCHAR(20),
    legenda TEXT,
    hashtags TEXT[],
    data_publicacao TIMESTAMP,
    horario TIME,
    tema TEXT,
    score_potencial INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de métricas
CREATE TABLE post_metrics (
    id SERIAL PRIMARY KEY,
    published_post_id INTEGER REFERENCES published_posts(id),
    medicao VARCHAR(10) CHECK (medicao IN ('24h', '48h', '7d')),
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    profile_visits INTEGER DEFAULT 0,
    follows_from_post INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de hashtags com performance
CREATE TABLE hashtags (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(100) UNIQUE NOT NULL,
    vezes_usada INTEGER DEFAULT 0,
    media_engagement DECIMAL(5,2) DEFAULT 0,
    categoria VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 11. Roadmap de Expansão

| Fase | Rede      | Estratégia                                                   | Pré-requisito                        |
|------|-----------|--------------------------------------------------------------|--------------------------------------|
| 1    | Instagram | Estabilizar pipeline completo, atingir métricas base.        | Pipeline atual funcionando.          |
| 2    | Facebook  | Reaproveitamento direto de posts do IG via Graph API.        | Fase 1 estável por 30 dias.         |
| 3    | TikTok    | Adaptar Reels para formato TikTok (duração, estilo).         | Biblioteca de Reels consolidada.     |
| 4    | X/Twitter | Microcopy, threads educativas, breaking news de maus-tratos. | Content Creator adaptado para texto. |
| 5    | YouTube   | Documentários, compilações, conteúdo educativo longo.        | Equipe de vídeo ou IA avançada.      |
