# Dicionário de Campos Compartilhados (Base)

## 1. Objetivo

Definir nomenclatura padrão entre módulos para evitar inconsistências na API e no banco.

## 2. Entidades e campos comuns

## Item

- `item_master_id`: identificador do produto base (família).
- `item_nome`: nome comercial do produto base.
- `categoria_id`: categoria de negócio do item.
- `classe_abc`: classe ABC (`A`, `B`, `C`, `D`, `E`).

## SKU

- `sku_id`: identificador único da variação.
- `sku_codigo`: código interno de gestão do SKU.
- `sku_nome`: descrição da variação (ex.: "Brahma 350ml").
- `item_master_id`: vínculo com o produto base.
- `ean`: código de barras associado ao SKU.
- `variacao_volume`: volume/peso da variação (quando aplicável).
- `variacao_cor`: cor da variação (quando aplicável).
- `variacao_tamanho`: tamanho/numeração da variação (quando aplicável).

## Saldo

- `saldo_disponivel`: quantidade liberada para venda por SKU.
- `saldo_avariado`: quantidade indisponível por avaria por SKU.
- `saldo_bloqueado`: quantidade bloqueada para análise por SKU.
- `saldo_total`: soma de todos os status por SKU.

## Cobertura e giro

- `cobertura_dias`: dias estimados de cobertura.
- `giro_periodo`: giro no período de análise.
- `lead_time_dias`: tempo médio de reposição.

## Validade

- `shelf_life_dias`: prazo total de validade.
- `validade_data`: data de vencimento do lote.
- `risco_vencimento`: status de risco de vencimento.

## Sazonalidade

- `sazonalidade_status`: `ativo`, `inativo`, `baixa_confianca`.
- `fator_sazonal`: fator de ajuste sazonal.
- `janela_analise_meses`: meses usados na análise.

## Orçamento

- `orcamento_total_periodo`: orçamento global de compra.
- `orcamento_categoria_periodo`: orçamento por categoria.
- `consumo_orcamento`: valor já consumido.
- `aporte_externo_valor`: valor extraordinário registrado.

## Endereçamento

- `endereco_codigo`: código completo do endereço (ex.: `DEP-P03-02`).
- `zona_codigo`: zona operacional (ex.: `LOJA`, `DEP`).
- `prateleira_codigo`: identificação da prateleira (ex.: `P03`).
- `posicao_codigo`: posição dentro da prateleira (ex.: `02`).
- `tipo_endereco`: tipo lógico (`venda`, `reserva`, `avariado`, `bloqueado`).

## Auditoria

- `created_at`: data/hora de criação.
- `updated_at`: data/hora de atualização.
- `created_by`: usuário responsável.
- `correlation_id`: identificador de rastreio da operação.

## 3. Regra de nomenclatura

- padrão obrigatório: `snake_case`;
- evitar abreviações ambíguas;
- manter unidade explícita quando aplicável (`_dias`, `_valor`, `_percentual`).
