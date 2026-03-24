# Workflow: Pesquisar Tendências

**Objetivo:** Identificar temas com alto potencial de engajamento para o nicho de proteção animal em SP.
**Agente responsável:** Growth Hacker (modelo Haiku para scraping, Sonnet para análise)
**Trigger:** Executado diariamente ou quando o usuário pede sugestões de pauta.

---

## Inputs
- Data atual
- Últimos 10 posts publicados (consultar PostgreSQL: `published_posts`)
- Hashtags com melhor performance histórica (consultar PostgreSQL: `hashtags`)

## Ferramentas
- `tools/scraper/trends_scraper.py` — scraping de hashtags e perfis referência
- `tools/db/db_manager.py` — leitura de histórico e escrita de novas ideias

## Passos

### 1. Coletar tendências externas
Executar `trends_scraper.py` para monitorar:
- Hashtags em alta: #cadeiaparamaustratos, #direitosanimais, #adoteNãoCompre, #leicao, #leisansao
- Perfis referência: @del.brunolima, @cadeiaparamaustratos, @cadeiaparamaustratos_sumare
- Notícias recentes: buscar termos "maus-tratos animais SP", "lei sansão", "resgate animal SP"
- Datas comemorativas próximas (Dia dos Animais: 4/out, Dia do Cão: 29/ago, etc.)

### 2. Cruzar com histórico interno
Consultar `content_ideas` e `published_posts` no PostgreSQL para:
- Evitar repetir temas publicados nos últimos 30 dias
- Identificar formatos que performaram melhor por tema similar

### 3. Gerar lista de ideias
Para cada ideia encontrada, calcular Score de Potencial preliminar (ver `avaliar_conteudo.md`) e salvar na tabela `content_ideas` com status `pendente`.

### 4. Retornar ao usuário
Apresentar top 5 ideias com:
- Tema e ângulo sugerido
- Formato recomendado (estático/carrossel/reel)
- Score de Potencial preliminar
- Justificativa em 1-2 linhas

## Tratamento de Erros
| Erro | Ação |
|---|---|
| Scraper falha / timeout | Usar busca web manual como fallback; logar em `temp/` |
| PostgreSQL indisponível | Continuar sem histórico; avisar usuário |
| Nenhuma tendência nova encontrada | Retornar ao usuário com sugestão baseada apenas no histórico interno |
