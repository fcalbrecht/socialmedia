# Workflow: Criar Carrossel Educativo

**Objetivo:** Produzir um carrossel completo (slides + legenda) pronto para aprovação.
**Agentes:** Content Creator (copy dos slides) + Instagram Curator (validação visual)
**Trigger:** Após aprovação do Score de Potencial ≥ 60 em `avaliar_conteudo.md`, quando o formato carrossel for o recomendado.

---

## Inputs
- `content_idea_id` — ID da ideia aprovada no PostgreSQL
- Tema, ângulo e estrutura sugerida pelo workflow de avaliação
- Diretrizes de marca: `/references/diretrizes_marca.md`

## Ferramentas
- `tools/image_gen/image_processor.py` — validação de dimensões por slide
- `tools/db/db_manager.py` — leitura da ideia e registro
- Skills: `copywriting` (framework PAS adaptado), `social-content`

## Estrutura de Slides (5-10 slides, formato 1080x1350px)

| Slide | Conteúdo | Objetivo |
|---|---|---|
| 1 — Capa | Pergunta impactante ou dado chocante | Parar o scroll |
| 2 | Contextualização do problema | Estabelecer o problema (P do PAS) |
| 3-4 | Dados, estatísticas, casos reais | Agitar a emoção (A do PAS) |
| 5-7 | Informação educativa, legislação, como agir | Solução (S do PAS) |
| 8-9 | Exemplos positivos (resgates, conquistas) | Esperança / prova social |
| Penúltimo | "Salve para consultar depois" | Aumentar saves (sinal de qualidade) |
| Último | CTA principal + @cadeiaparamaustratossp | Converter em seguidor/compartilhamento |

## Passos

### 1. Delegar estrutura e copy ao Content Creator
Prompt obrigatório para o agente:
```
OBJETIVO: Criar texto para carrossel educativo sobre [TEMA].
CONTEXTO: [Resumo do tema e ângulo aprovado]
NÚMERO DE SLIDES: [5 a 10, definir com base na profundidade do tema]
ESTRUTURA: Seguir tabela de slides do workflow criar_carrossel.md
FRAMEWORK: PAS adaptado ao longo dos slides
RESTRIÇÕES: Máximo 3 linhas de texto por slide (legibilidade mobile). Tom firme mas informativo.
ENTREGÁVEL: Texto de cada slide + legenda completa do post
SKILLS: copywriting, social-content
```

### 2. Revisar copy (Orquestrador)
Para cada slide verificar:
- [ ] Capa tem gancho forte (pergunta ou dado impactante)
- [ ] Máximo 3 linhas de texto por slide
- [ ] Fluxo narrativo coerente entre slides
- [ ] Penúltimo slide tem CTA de save
- [ ] Último slide tem CTA de seguir/compartilhar e @ do perfil

Verificar legenda do post:
- [ ] Introduz o carrossel ("Arraste para ver →" ou similar)
- [ ] 15-20 hashtags relevantes + 3 fixas

### 3. Delegar validação visual ao Instagram Curator
O Curator verifica para CADA slide:
- [ ] Dimensão: 1080x1350px
- [ ] Paleta de cores consistente entre todos os slides
- [ ] Tipografia consistente entre slides
- [ ] Texto legível no mobile
- [ ] Logo no último slide
- [ ] Primeiro slide é atraente o suficiente para parar o scroll

### 4. Processar slides
Executar `image_processor.py` para cada slide:
- Validar dimensões e formato
- Salvar em `temp/carrossel_[content_idea_id]/slide_01.jpg`, `slide_02.jpg`, etc.

### 5. Apresentar para aprovação humana
Mostrar ao usuário:
- Lista de arquivos dos slides em `temp/`
- Texto de cada slide
- Legenda completa
- Score e horário sugerido

**O usuário pode:** Aprovar | Ajustar slide específico | Descartar

### 6. Após aprovação
- Registrar número de slides e caminhos em `content_ideas` (campo `notas`)
- Aguardar comando de publicação

## Tratamento de Erros
| Erro | Ação |
|---|---|
| Slide com texto muito longo | Delegar ao Content Creator para cortar para máx 3 linhas |
| Inconsistência visual entre slides | Instagram Curator refaz o checklist e aponta o slide problemático |
| Número de slides < 3 | Rejeitar — carrossel precisa de mínimo 3 slides para valer a pena |
