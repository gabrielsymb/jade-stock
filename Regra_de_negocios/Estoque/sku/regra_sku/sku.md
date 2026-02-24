# Regra de Negócio: Gestão de SKU

## 1. Objetivo

Definir SKU como unidade mínima de gestão de estoque, garantindo precisão de saldo, curva ABC, giro, cobertura e previsão.

## 2. Definições

- **SKU (Stock Keeping Unit):** identificador interno único de cada variação física de produto.
- **Item (quantidade):** unidade física disponível de um SKU.
- **EAN (código de barras):** identificador padronizado externo, associado ao SKU.

## 3. Regra Fundamental de Variação

Se mudar atributo relevante, muda SKU.

Exemplos:

- Brahma 1L != Brahma 350ml
- Arroz 1kg != Arroz 5kg
- Camiseta azul P != Camiseta azul M
- Monster tradicional != Monster sem açúcar

## 4. Regras Obrigatórias

1. Cada variação física deve ter `sku_id` único.
2. Cada SKU deve ter endereçamento específico no estoque.
3. O sistema não deve agrupar variações diferentes em um único SKU.
4. Curva, giro, cobertura e previsão devem ser calculados por SKU, não por nome genérico de produto.
5. SKU e EAN devem existir em campos distintos.

## 5. Erro que deve ser evitado

Criar um único código para itens semelhantes ("cerveja", "camiseta manga curta") invalida estatística e oculta ruptura/excesso por variação.

## 6. Escalabilidade

O modelo deve suportar alto volume de SKUs no varejo. A gestão por classe (ABC/XYZ) existe justamente para priorizar atenção dentro da grande variedade.

## 7. Alertas Obrigatórios

- `sku_sem_endereco`
- `sku_sem_ean_quando_obrigatorio`
- `variacao_sem_sku_dedicado`
- `agrupamento_invalido_de_variacoes`

## 8. Saídas Esperadas

- cadastro de SKU consistente por variação;
- saldo por SKU e endereço;
- indicadores (giro/cobertura/ABC) por SKU;
- rastreabilidade de ruptura e excesso por variação específica.

## 9. Conexão com outros módulos

- **Curva:** classificação por SKU.
- **Giro:** renovação por SKU.
- **Sazonalidade:** padrão temporal por SKU.
- **Endereçamento:** localização específica por SKU.
- **Recebimento/Avarias:** entrada e perdas sempre referenciadas por SKU.
