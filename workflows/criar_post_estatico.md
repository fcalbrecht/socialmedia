# Workflow: Criar Post Estático

**Objetivo:** Produzir um post estático completo (imagem + legenda) pronto para aprovação.
**Agentes:** Content Creator (copy) + Instagram Curator (validação visual)
**Trigger:** Após aprovação do Score de Potencial ≥ 60 em `avaliar_conteudo.md`.

---

## Inputs
- `content_idea_id` — ID da ideia aprovada no PostgreSQL
- Tema, ângulo e hashtags sugeridas pelo workflow de avaliação
- Diretrizes de marca: `/references/diretrizes_marca.md`

## Ferramentas
- `tools/image_gen/image_processor.py` — validação de dimensões e qualidade
- `tools/db/db_manager.py` — leitura da ideia e registro do post criado
- Skills: `copywriting` (framework PAS), `social-content`

## Passos

### 1. Delegar copy ao Content Creator
Prompt obrigatório para o agente:
```
OBJETIVO: Criar legenda para post estático sobre [TEMA].
CONTEXTO: [Resumo do tema e ângulo aprovado]
FRAMEWORK: PAS (Problem → Agitate → Solve)
FORMATO: Gancho (1 linha) + Contexto/Problema (2-3 linhas) + Dado/Informação (2-3 linhas) + CTA (1 linha) + Hashtags
RESTRIÇÕES: Tom firme mas não agressivo. Sem sensacionalismo. Sem imagens gráficas mencionadas.
HASHTAGS FIXAS: #CadeiaParaMausTratos #DireitosAnimais #ProteçãoAnimal
SKILLS: copywriting, social-content
```

### 2. Revisar copy (Orquestrador)
Verificar se a legenda:
- [ ] Tem gancho emocional na primeira linha
- [ ] Usa PAS corretamente
- [ ] Inclui CTA claro ("Compartilhe", "Denuncie pelo 190", "Siga")
- [ ] Tem entre 15-20 hashtags relevantes + 3 fixas
- [ ] Está dentro do tom definido em `/references/diretrizes_marca.md`

### 3. Delegar validação visual ao Instagram Curator
O Curator verifica (checklist):
- [ ] Dimensão: 1080x1080px (feed) ou 1080x1350px (retrato)
- [ ] Paleta de cores conforme `/references/diretrizes_marca.md`
- [ ] Texto legível no mobile (fonte mínima respeitada)
- [ ] Logo posicionado corretamente
- [ ] Consistência com os últimos 9 posts do grid

### 4. Processar imagem
Executar `image_processor.py` para:
- Validar dimensões e formato (JPEG/PNG, máx 8MB)
- Redimensionar se necessário
- Salvar em `temp/` com nome `post_[content_idea_id]_[timestamp].jpg`

### 5. Apresentar para aprovação humana
Mostrar ao usuário:
- Preview da imagem (caminho do arquivo em `temp/`)
- Legenda completa com hashtags
- Score de Potencial e justificativa
- Horário de publicação sugerido (baseado em `post_metrics` histórico)

**O usuário pode:** Aprovar → ir para publicação | Ajustar → voltar ao passo relevante | Descartar → marcar ideia como `descartado` no DB

### 6. Após aprovação ⚠️ OBRIGATÓRIO — não pular
**Imediatamente** após o usuário aprovar, salvar em `temp/post_[slug]_aprovado.json`:

```json
{
  "status": "aprovado",
  "data_aprovacao": "YYYY-MM-DD",
  "imagem": "temp/[nome_do_arquivo].jpg",
  "legenda": "texto completo da legenda",
  "hashtags": ["#tag1", "#tag2", "..."],
  "score": 0,
  "tema": "descrição do tema"
}
```

- Salvar o `.json` **antes** de qualquer outra ação pós-aprovação
- Salvar copy e caminho da imagem na tabela `content_ideas` (campo `notas`) — se DB disponível
- Aguardar comando de publicação (workflow `publicar_post.md` — fase futura)
- **Razão:** Claude Code não tem memória entre sessões; o arquivo JSON é a única persistência garantida

## Tratamento de Erros
| Erro | Ação |
|---|---|
| Imagem fora das dimensões | Executar redimensionamento automático via `image_processor.py` |
| Copy com tom inadequado | Delegar revisão ao Content Creator com feedback específico |
| Arquivo > 8MB após processamento | Reduzir qualidade JPEG para 85% e tentar novamente |
