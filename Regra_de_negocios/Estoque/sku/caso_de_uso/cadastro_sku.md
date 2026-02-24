# Caso de Uso: Cadastro de SKU

## 1. Objetivo

Cadastrar SKUs de forma padronizada, garantindo diferenciação por variação física e evitando agrupamentos que distorçam estoque e estatística.

## 2. Atores

- Operador de Cadastro
- Sistema de Estoque
- Gestor (aprovação de exceções)

## 3. Pré-condições

- Produto base (`item_master`) já cadastrado.
- Categoria e unidade de medida definidas.
- Regra de endereçamento ativa.

## 4. Fluxo Principal

1. Operador seleciona o produto base.
2. Operador informa variações (ex.: tamanho, cor, volume, sabor).
3. Sistema gera ou valida `sku_codigo` único.
4. Operador informa/associa `ean` (quando aplicável).
5. Operador define endereço inicial do SKU.
6. Sistema valida duplicidade de variação.
7. Sistema salva SKU e registra evento de auditoria.

## 5. Regras de Negócio

- Cada combinação de variação deve resultar em 1 SKU distinto.
- Não é permitido reutilizar o mesmo `sku_codigo`.
- Não é permitido duplicar a mesma combinação de variação no mesmo produto base.
- `ean` não substitui `sku_codigo`; ambos têm papel diferente.
- SKU deve nascer com endereço válido para operação.

## 6. Validações Obrigatórias

- unicidade de `sku_codigo`;
- unicidade de combinação (`item_master_id` + atributos de variação);
- formato mínimo de nome/descrição de SKU;
- endereço válido e ativo;
- validação de `ean` quando for obrigatório.

## 7. Fluxos Alternativos

- **Duplicidade detectada:** sistema bloqueia cadastro e sugere SKU existente.
- **EAN ausente (quando obrigatório):** sistema impede publicação do cadastro.
- **Endereço inválido:** sistema exige correção antes de concluir.
- **Exceção de negócio:** gestor pode aprovar cadastro com justificativa auditável.

## 8. Alertas Obrigatórios

- `sku_codigo_duplicado`
- `variacao_duplicada_no_produto_base`
- `sku_sem_endereco_valido`
- `ean_invalido_ou_ausente`
- `cadastro_sku_em_excecao`

## 9. Saídas Esperadas

- SKU ativo e rastreável;
- vínculo correto com produto base;
- endereço inicial definido;
- histórico de criação e aprovação de exceções;
- base pronta para giro, cobertura, curva ABC e previsão por SKU.
