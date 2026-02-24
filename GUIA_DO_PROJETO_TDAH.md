# Guia Simples do Projeto WMS

## 1) Onde voce esta agora

Voce nao esta perdido no codigo. Voce esta na fase certa:

1. Estudou regras de negocio e fluxos de estoque.
2. Transformou isso em documentacao.
3. Criou casos de uso executaveis.
4. Validou com testes.

Resumo: a base do motor do WMS ja funciona.

## 2) O que ja esta pronto (sem tecniquês)

- Cadastro/validacao de SKU ativo.
- Validacao de endereco.
- Movimentacao de estoque.
- Ajuste de estoque.
- Recebimento com divergencia.
- Registro de eventos.
- Persistencia em PostgreSQL (fase core).
- Testes automatizados passando.
- Testes de transacao e concorrencia passando.

## 3) Casos de uso implementados hoje

1. `RegistrarMovimentacaoEstoque`
2. `RegistrarAjusteEstoque`
3. `RegistrarRecebimento`

Nao foram esquecidos. Estao implementados e testados.

## 4) O que os testes estao testando (em portugues claro)

- Se regra de negocio esta sendo respeitada.
- Se saldo nao fica inconsistente.
- Se erro faz rollback (desfaz tudo).
- Se duas operacoes ao mesmo tempo nao quebram o saldo.
- Se recebimento e movimentacao realmente gravam no banco.

## 5) Comandos oficiais (copiar e colar)

Ativar ambiente:

```bash
cd ~/meus_projetos/Jade-stock
source .venv/bin/activate
```

Rodar todos os testes:

```bash
cd ~/meus_projetos/Jade-stock/WMS
set -a
source .env
set +a
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Rodar apenas SQL (Postgres):

```bash
cd ~/meus_projetos/Jade-stock/WMS
set -a
source .env
set +a
./scripts/run_sql_tests.sh
```

## 6) Proximo passo unico (sem te confundir)

Proximo passo recomendado e apenas um:

**Criar camada de API minima para os 3 casos de uso ja prontos.**

Nada de microservico agora.
Nada de frontend agora.
Nada de ML agora.

Status: este passo foi implementado.

Endpoints:

1. `POST /v1/movimentacoes`
2. `POST /v1/ajustes`
3. `POST /v1/recebimentos`
4. `GET /v1/health`

Subir API:

```bash
cd ~/meus_projetos/Jade-stock/WMS
source ../.venv/bin/activate
python -m pip install -r requirements-dev.txt
./scripts/run_api.sh
```

## 7) Regra de foco para nao travar

Sempre decidir assim:

1. Isso ajuda `movimentacao`, `ajuste` ou `recebimento`?
2. Se nao ajuda, nao faz agora.

Essa regra evita overengineering e reduz ansiedade.
