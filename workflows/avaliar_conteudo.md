# Workflow: Avaliar Conteúdo (Score de Potencial)

**Objetivo:** Calcular um score 0-100 para qualquer tema sugerido antes de iniciar a produção.
**Agente responsável:** Growth Hacker (modelo Sonnet)
**Trigger:** Sempre que o usuário sugerir um tema OU antes de iniciar qualquer workflow de criação.

---

## Inputs
- Tema proposto (texto livre do usuário)
- Formato desejado (se o usuário especificou)
- Dados históricos de posts similares (PostgreSQL: `published_posts` + `post_metrics`)

## Ferramentas
- `tools/db/db_manager.py` — consulta de performance histórica
- Skills: `social-content` (timing e formato), `copywriting` (avaliação do gancho)

## Critérios de Avaliação (25 pts cada)

### 1. Relevância para a causa (0-25 pts)
- 25: Diretamente sobre maus-tratos, legislação animal ou resgate em SP
- 15-24: Relacionado à causa (adoção, bem-estar animal, denúncia)
- 5-14: Periférico (animais em geral, sem foco em proteção)
- 0-4: Sem relação com a causa

### 2. Timing e tendência (0-25 pts)
- 25: Acontecimento recente (< 48h) ou data comemorativa hoje/amanhã
- 15-24: Tema em alta nos últimos 7 dias
- 5-14: Tema evergreen relevante
- 0-4: Tema ultrapassado ou fora de contexto temporal

### 3. Potencial de engajamento (0-25 pts)
- 25: Gera forte emoção (indignação, esperança, urgência) + alta compartilhabilidade
- 15-24: Engaja, mas de forma mais racional/informativa
- 5-14: Pouco apelo emocional
- 0-4: Tema árido, baixo potencial de reação

### 4. Viabilidade de produção (0-25 pts)
- 25: Assets disponíveis, formato simples, pode publicar hoje
- 15-24: Requer criação de assets, mas factível em 1-2h
- 5-14: Depende de dados externos difíceis de obter
- 0-4: Inviável no prazo ou sem recursos necessários

## Passos

### 1. Coletar contexto
- Buscar posts similares no PostgreSQL pelo campo `tema`
- Verificar se o tema foi publicado nos últimos 30 dias

### 2. Pontuar cada critério
Avaliar os 4 critérios e documentar justificativa para cada nota.

### 3. Calcular score final
`score = critério1 + critério2 + critério3 + critério4`

### 4. Determinar ação
| Score | Decisão |
|---|---|
| 80-100 | Aprovado — prosseguir para criação imediatamente |
| 60-79 | Aprovado com ajustes — sugerir melhorias antes de criar |
| 40-59 | Duvidoso — apresentar 2 alternativas ao usuário |
| 0-39 | Não recomendado — explicar motivos e propor outro tema |

### 5. Sempre sugerir (independente do score)
- Ajuste no ângulo/abordagem
- Melhor formato para o tema
- 5 hashtags recomendadas baseadas no histórico
- Melhor horário de publicação (baseado em `post_metrics`)

### 6. Salvar no PostgreSQL
Registrar ideia na tabela `content_ideas` com o score calculado e status `pendente`.

## Tratamento de Erros
| Erro | Ação |
|---|---|
| PostgreSQL indisponível | Avaliar sem dados históricos; avisar usuário que o score pode ser menos preciso |
| Tema muito vago | Pedir ao usuário para detalhar antes de avaliar |
