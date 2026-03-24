# Workflow: Criar Reel

**Objetivo:** Produzir roteiro e assets de um Reel pronto para edição e aprovação.
**Agentes:** Content Creator (roteiro) + Instagram Curator (validação)
**Trigger:** Após aprovação do Score de Potencial ≥ 60 em `avaliar_conteudo.md`, quando formato Reel for recomendado.

> **Nota:** Este workflow produz o roteiro e os assets. A edição de vídeo final
> depende de `tools/video/reel_processor.py` (FFmpeg) — a ser implementado.

---

## Inputs
- `content_idea_id` — ID da ideia aprovada no PostgreSQL
- Tema, ângulo e gancho aprovado
- Diretrizes de marca: `/references/diretrizes_marca.md`

## Ferramentas
- `tools/video/reel_processor.py` — edição básica com FFmpeg (fase futura)
- `tools/db/db_manager.py` — registro
- Skills: `copywriting` (gancho dos 3 primeiros segundos), `social-content`

## Especificações Técnicas
- Duração: **15-30 segundos** (máximo alcance orgânico)
- Formato: **1080x1920px** (vertical 9:16)
- Gancho: **primeiros 3 segundos** definem se o usuário continua assistindo
- Legendas: embutidas no vídeo (acessibilidade e visualização sem som)
- Música: instrumental ou sem música (evitar copyright)

## Estrutura do Roteiro

| Tempo | Conteúdo | Objetivo |
|---|---|---|
| 0-3s | Gancho visual + texto de impacto | Parar o scroll |
| 3-10s | Problema / contexto em 1-2 frases | Criar conexão emocional |
| 10-20s | Dado, lei ou caso real relevante | Informar / agitar |
| 20-27s | Solução / o que fazer / como denunciar | Emponderar o espectador |
| 27-30s | CTA + @cadeiaparamaustratossp | Converter |

## Passos

### 1. Delegar roteiro ao Content Creator
Prompt obrigatório para o agente:
```
OBJETIVO: Criar roteiro para Reel de 15-30s sobre [TEMA].
CONTEXTO: [Resumo do tema e ângulo aprovado]
ESTRUTURA: Seguir tabela de roteiro do workflow criar_reel.md
GANCHO: Os primeiros 3 segundos são críticos — deve ser uma pergunta provocativa ou dado chocante em texto
RESTRIÇÕES: Linguagem simples e direta. Frases curtas (máx 8 palavras por cena). Sem imagens de sofrimento animal.
ENTREGÁVEL: Roteiro cena a cena (tempo | texto na tela | narração opcional) + legenda do post
SKILLS: copywriting, social-content
```

### 2. Revisar roteiro (Orquestrador)
- [ ] Gancho nos 3 primeiros segundos
- [ ] Duração total entre 15-30s
- [ ] Frases curtas e legíveis na tela
- [ ] CTA claro no final
- [ ] Menciona @cadeiaparamaustratossp

### 3. Checklist do Instagram Curator
- [ ] Proporção 9:16 (1080x1920px) respeitada
- [ ] Espaço seguro para UI do Instagram (evitar texto nos 15% superior e inferior)
- [ ] Consistência visual com identidade da marca
- [ ] Legendas planejadas para todos os textos falados/narrados

### 4. Apresentar roteiro para aprovação humana
Mostrar ao usuário:
- Roteiro completo cena a cena
- Legenda do post
- Lista de assets necessários (fotos/vídeos que o usuário deve fornecer)
- Observação sobre edição com FFmpeg

**O usuário pode:** Aprovar roteiro | Ajustar cenas | Descartar

### 5. Após aprovação do roteiro
- Registrar roteiro em `content_ideas` (campo `notas`)
- Solicitar ao usuário os assets de vídeo/foto necessários
- Quando assets disponíveis, executar `reel_processor.py` para edição

## Tratamento de Erros
| Erro | Ação |
|---|---|
| Roteiro > 30s | Delegar ao Content Creator para cortar — priorizar gancho e CTA |
| Assets de vídeo não disponíveis | Oferecer alternativa: slideshow de fotos editado como Reel |
| FFmpeg não instalado | Avisar usuário e fornecer instruções de instalação |
