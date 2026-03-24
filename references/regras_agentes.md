# Regras para Sub-Agentes e Equipes de Agentes (Agent Teams)

## 1. Conceito Fundamental
O Agente Orquestrador (principal) deve preservar seu contexto principal. Para isso, delega tarefas pesadas, de pesquisa ou processamento massivo de dados para **sub-agentes** que rodam em paralelo.

## 2. Sub-Agentes vs Agent Teams

### 2.1 Sub-Agentes (Paralelos e Isolados)
- **Não se comunicam entre si.** Cada um recebe uma tarefa, executa e retorna o resultado ao Orquestrador.
- **Usados para:** Pesquisa web, leitura massiva de dados, scraping, processamento de imagens, consultas ao banco de dados.
- **Vantagem:** Preservam o contexto do agente principal. São mais baratos e rápidos.

### 2.2 Agent Teams (Equipes Colaborativas)
- **Se comunicam entre si.** Compartilham uma lista de tarefas, conversam e delegam trabalho uns aos outros.
- **Usados para:** Fluxos complexos onde um agente depende do output do outro.
- **Exemplo:** O Content Creator gera a copy → envia para o Instagram Curator validar o visual → Growth Hacker faz a análise final.
- **Importante:** Herdam permissões da sessão principal, mas **começam com memória em branco**. O objetivo deve ser passado com detalhes no prompt inicial.

## 3. Regra de Alocação de Modelos

| Tipo de Tarefa                          | Modelo Recomendado | Justificativa                        |
|-----------------------------------------|--------------------|-----------------------------------------|
| Pesquisa web e scraping                 | **Haiku**          | Rápido e barato, tarefa simples.        |
| Triagem e classificação de dados        | **Haiku**          | Não precisa de raciocínio profundo.     |
| Leitura massiva de arquivos/documentos  | **Haiku**          | Processamento bruto, sem criatividade.  |
| Consultas ao PostgreSQL                 | **Haiku**          | Execução direta de queries.            |
| Criação de copy e legendas              | **Sonnet/Opus**    | Requer criatividade e nuance.           |
| Avaliação estratégica de conteúdo       | **Sonnet/Opus**    | Requer raciocínio complexo.             |
| Curadoria visual e decisões estéticas   | **Sonnet**         | Equilíbrio entre qualidade e custo.     |
| Planejamento de campanha                | **Opus**           | Raciocínio estratégico de alto nível.   |

## 4. Agentes do Projeto @cadeiaparamaustratossp

### 4.1 Instagram Curator
**Localização:** `~/.claude/agents/instagram-curator`
**Responsabilidades:**
- Curadoria de assets visuais (imagens, vídeos).
- Validação de consistência do grid do Instagram.
- Storytelling visual e estética de feed.
- Verificação de conformidade com diretrizes de marca (`/references/diretrizes_marca.md`).
- Validação de dimensões e qualidade técnica dos assets.

**Skills que deve consultar:** `social-content` (para formatos).
**Modelo padrão:** Sonnet.

### 4.2 Content Creator
**Localização:** `~/.claude/agents/content-creator`
**Responsabilidades:**
- Redação de legendas para todos os formatos.
- Roteiros para Reels.
- Copy para slides de carrosséis.
- Seleção de hashtags otimizadas.
- Aplicação de frameworks de persuasão.

**Skills que DEVE consultar:** `copywriting` (obrigatório), `social-content`.
**Modelo padrão:** Sonnet (legendas simples) ou Opus (campanhas estratégicas).

### 4.3 Growth Hacker
**Localização:** `~/.claude/agents/growth-hacker`
**Responsabilidades:**
- Pesquisa de tendências no nicho animal/proteção.
- Análise de concorrência e benchmarking.
- Design de loops virais e ganchos de conversão.
- Experimentos de crescimento (testes A/B de horários, hashtags, formatos).
- Análise de métricas e retroalimentação do sistema.
- Avaliação de Score de Potencial quando o usuário sugere conteúdo.

**Skills que deve consultar:** `social-content`, `copywriting` (para avaliar ganchos).
**Modelo padrão:** Sonnet (análises) ou Haiku (scraping de tendências).

## 5. Como Delegar Tarefas para Sub-Agentes

### 5.1 Prompt Inicial Obrigatório
Todo sub-agente deve receber no prompt inicial:
1. **Objetivo claro:** O que ele precisa fazer.
2. **Contexto necessário:** Informações relevantes (NÃO enviar todo o contexto do projeto).
3. **Formato do output esperado:** Como deve retornar o resultado.
4. **Restrições:** O que NÃO deve fazer.
5. **Skills a consultar:** Quais skills carregar.

### 5.2 Exemplo de Delegação
```
TAREFA PARA: Content Creator
OBJETIVO: Criar legenda para post estático sobre a Lei Sansão.
CONTEXTO: Post educativo explicando que a Lei 14.064/2020 prevê 2-5 anos de reclusão para maus-tratos a cães e gatos.
FORMATO: Legenda com gancho + informação + CTA + 20 hashtags.
RESTRIÇÕES: Tom firme mas não agressivo. Sem sensacionalismo.
SKILLS: Carregar copywriting (framework PAS) e social-content.
```

## 6. Regras de Segurança para Agentes
- Sub-agentes **NUNCA** recebem credenciais ou tokens de acesso diretamente.
- Se precisarem acessar APIs, devem chamar ferramentas de `/tools/` que leem credenciais do `.env`.
- Resultados de sub-agentes devem ser **validados** pelo Orquestrador antes de uso final.

## 7. Criação de Novos Agentes
Ao criar um novo agente para o projeto:
1. Criar arquivo em `~/.claude/agents/` com front matter YAML (`name`, `description`).
2. Definir responsabilidades, skills obrigatórias e modelo recomendado.
3. Registrar o agente neste documento (`regras_agentes.md`).
4. Testar com tarefa de validação antes de integrar ao pipeline.
