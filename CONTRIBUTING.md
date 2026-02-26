# Guia de Contribuicao - Jade-stock

Este guia define o fluxo minimo para contribuir sem quebrar o que ja esta estavel no projeto.

## Escopo atual (26/02/2026)

- Modulo ativo para entrega: `WMS`.
- Modulos `Contabil`, `PDV` e `IA/Analytics`: em planejamento/documentacao.
- Nao commitar pastas vazias ou placeholders de modulos futuros.

## Setup local

```bash
cd Jade-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

## Validacao obrigatoria antes de commit

```bash
cd WMS
source ../.venv/bin/activate
pytest -q -rs
./scripts/release_gate_enhanced.sh
```

## Fluxo recomendado de contribuicao

1. Crie branch de trabalho (`feature/...`, `fix/...`, `docs/...`).
2. Implemente com testes/ajustes de docs no mesmo contexto.
3. Rode validacoes locais.
4. Faça staging seletivo com `git add -p`.
5. Abra PR com descricao clara do que mudou e por que.

## Regra de staging seletivo

Use `git add -p` para separar com clareza:

- nucleo pronto para deploy (WMS, scripts, testes de regressao);
- trilhas experimentais/legadas que ainda nao devem ir para o mesmo commit.

## Convencao de commits

Formato recomendado:

```text
<tipo>(escopo): descricao curta
```

Tipos comuns: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Checklist de PR

- [ ] Testes locais passando
- [ ] Release gate passando
- [ ] Documentacao atualizada
- [ ] Sem pastas vazias/placeholder de modulos futuros
- [ ] Commits com escopo claro

## Recursos principais

- [README](./README.md)
- [Biblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md)
- [WMS README](./WMS/README.md)
- [Boas Praticas de Docs](./DOCS_BOAS_PRACTICES.md)
- [Guia de Estrutura](./guia_de_estruture.md)
