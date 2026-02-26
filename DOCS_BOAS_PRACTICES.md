# Boas Praticas de Documentacao - Jade-stock

**Versao:** 1.1  
**Data:** 2026-02-26  
**Aplicavel:** Todo o repositorio

## Objetivo

Padronizar como a documentacao e escrita, atualizada e referenciada para evitar divergencia entre o que esta no papel e o que esta no codigo.

## Documentos fixos e seus papeis

| Documento | Papel no projeto |
|---|---|
| `README.md` | Porta de entrada: setup, execucao, status atual |
| `JADE-STOCK-BIBLIA-DO-SISTEMA.md` | Mapa arquitetural e de negocio de alto nivel |
| `WMS/README.md` | Verdade operacional do modulo ativo (WMS) |
| `CONTRIBUTING.md` | Regras para contribuir e commitar sem ruido |
| `guia_de_estruture.md` | Estrutura oficial de pastas e fronteiras por modulo |
| `jade-stock-adendos.docx.md` | Adendos de evolucao (XML, PDV, fornecedores, etc.) |

## Regras de escrita

- Use titulos claros e secoes curtas.
- Prefira exemplos executaveis no ambiente real do projeto.
- Sempre usar caminhos relativos em links markdown.
- Evite links para arquivos inexistentes.
- Quando citar status de testes/deploy, inclua data explicita.

## Regras de atualizacao

Atualize docs quando houver mudanca em:

- comandos de setup/execucao;
- portas, rotas e contratos de API;
- scripts de release/deploy;
- politica de estrutura de diretorios;
- status real de modulos ativos vs planejados.

## Higiene de repositorio ligada a documentacao

- Nao criar/commitar pastas vazias para modulos futuros.
- Nao manter placeholders sem dono/uso claro.
- Se algo estiver apenas planejado, documente como "planejado" em vez de simular modulo pronto no filesystem.

## Checklist rapido para PR de documentacao

- [ ] Links internos validos
- [ ] Comandos testados localmente
- [ ] Data/versao atualizadas quando relevante
- [ ] Estado real do sistema refletido (sem marketing tecnico)
- [ ] Coerencia com `README.md` e `WMS/README.md`

## Exemplo de link relativo correto

```markdown
Veja o fluxo em [WMS README](./WMS/README.md).
```
