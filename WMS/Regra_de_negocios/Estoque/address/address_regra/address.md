# Regra de Negócio: Address (Endereçamento Operacional)

## 1. Objetivo

Garantir localização exata de cada SKU no estoque, reduzir erro de armazenagem/separação e padronizar a lógica de endereços para operação pequena e média.

## 2. Princípio Fundamental

Cada SKU deve possuir um endereço único e rastreável.  
Sem endereço específico por variação, o sistema perde precisão de saldo, ruptura e reposição.

## 3. Estrutura do Endereço

Formato recomendado:

- `deposito-rua-bloco-nivel-posicao`
- Exemplo: `D1-A-02-03-05`

Significado:

- `deposito`: área/site lógico;
- `rua`: corredor ou faixa de estantes;
- `bloco`: estante/conjunto físico;
- `nivel`: prateleira/altura;
- `posicao`: local exato na prateleira.

## 4. Regras Obrigatórias

1. Endereço deve ser único por posição física.
2. SKU não pode ser cadastrado sem endereço ativo.
3. SKU diferente não pode compartilhar a mesma posição quando a política for de ocupação exclusiva.
4. Endereço deve ser validado no recebimento e na movimentação interna.
5. Avarias devem ser movidas para endereço de tipo `avariado` ou `bloqueado`.

## 5. Sugestão Automática de Endereço

No cadastro/recebimento, o sistema pode sugerir endereço seguindo esta prioridade:

1. afinidade por família/categoria do SKU;
2. proximidade com SKUs semelhantes;
3. primeira posição livre no fluxo sequencial (`rua > bloco > nivel > posicao`).

Se não houver posição elegível, o sistema deve emitir alerta de capacidade.

## 6. Mitigação de Erro Operacional

Para reduzir erro humano:

- confirmação por leitura de etiqueta (quando houver coletor);
- validação de endereço ocupado/livre;
- apoio visual por nível/zona (cores e identificação clara);
- instrução de armazenagem na tela com código completo do endereço.

## 7. Picking e Rota de Separação

A lista de separação deve ser ordenada por endereço, não por ordem de venda, para reduzir deslocamento improdutivo e fadiga do operador.

## 8. Alertas Obrigatórios

- `sku_sem_endereco`
- `endereco_ocupado_indevidamente`
- `movimentacao_para_endereco_invalido`
- `divergencia_endereco_fisico_vs_sistemico`
- `capacidade_de_endereco_insuficiente`

## 9. Saídas Esperadas

- saldo por SKU e endereço;
- histórico de movimentação entre endereços;
- sugestão de endereço no recebimento/cadastro;
- rastreabilidade de divergências por localização.

## 10. Conexão com outros módulos

- **SKU:** define a unidade que será endereçada.
- **Recebimento:** valida entrada no endereço correto.
- **Cíclico:** contagem por item + localização.
- **Avarias:** bloqueia venda via endereço específico.
- **Giro/Curva/Sazonalidade:** decisões de reposição com base em localização confiável.
