# Regras para Criação e Uso de Skills (Habilidades)

## 1. Definição
Skills são receitas ou instruções reutilizáveis em formato Markdown que o agente carrega sob demanda. Elas funcionam como "manuais especializados" que o agente consulta apenas quando precisa executar uma tarefa específica, economizando tokens.

## 2. Localização
- Skills instaladas (marketing-skills): `.claude/skills/`
- Skills customizadas do projeto: `.claude/skills/custom/`

## 3. Estrutura Obrigatória (Front Matter YAML)
Toda skill DEVE começar com um cabeçalho YAML contendo `name` e `description`. O agente lê APENAS essas descrições iniciais para decidir qual skill carregar — isso implementa o **carregamento progressivo de contexto**, poupando tokens.

```yaml
---
name: nome-da-skill
description: "Descrição concisa do que a skill faz e quando deve ser usada"
---
```

## 4. Regras de Tamanho e Economia de Tokens
- Uma skill deve ter **menos de 500 linhas**.
- Se precisar de muito contexto, a skill deve **apontar para arquivos de referência** em `/references/` em vez de conter toda a informação internamente.
- Prefira bullet points e exemplos curtos em vez de explicações longas.

## 5. Quando Criar uma Nova Skill
- Quando uma tarefa é **repetitiva** e segue um padrão consistente.
- Quando a qualidade do output melhora significativamente com instruções específicas.
- **Antes de criar:** Verifique se já existe uma skill no `marketing-skills` que resolva o problema.

## 6. Skills do Marketing-Skills Disponíveis

### 6.1 `social-content`
**Quando usar:** Estratégia orgânica, calendário editorial, estrutura de posts, formatos por plataforma.
**Invocar quando:** Planejar calendário semanal/mensal, decidir formato de post, definir estratégia de hashtags.

### 6.2 `copywriting`
**Quando usar:** Frameworks de persuasão para legendas e textos.
**Invocar quando:** Escrever legendas, CTAs, ganchos. Frameworks disponíveis: PAS (Problem-Agitate-Solve), AIDA, BAB (Before-After-Bridge).
**Prioridade para este projeto:** Usar PAS como framework principal (funciona bem para causa social: expõe o problema, agita a emoção, apresenta a solução/ação).

### 6.3 `ad-creative`
**Quando usar:** Criação de anúncios pagos no Meta Ads.
**Invocar quando:** Fase futura de escalonamento com tráfego pago.
**Status:** Reservada para fases futuras.

## 7. Como Invocar Skills
O agente pode carregar skills de duas formas:
1. **Automática:** Ao identificar a tarefa no workflow, o agente consulta a skill relevante.
2. **Via slash command:** O usuário pode invocar diretamente usando `/skill nome-da-skill`.

## 8. Atualização de Skills
- Se o agente identificar que uma skill produziu resultados abaixo do esperado, deve registrar o aprendizado na memória local e sugerir atualização da skill.
- Skills customizadas podem ser editadas pelo agente após aprovação do usuário.
- Skills do marketing-skills são read-only (atualizadas via repositório).
