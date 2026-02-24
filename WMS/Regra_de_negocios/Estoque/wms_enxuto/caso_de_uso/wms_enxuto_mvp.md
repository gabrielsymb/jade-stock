# Caso de Uso Integrador: WMS Enxuto (MVP)

## 1. Objetivo

Definir o escopo mínimo de um WMS enxuto para operações com equipe reduzida (3 a 4 pessoas), priorizando controle operacional, acuracidade e decisões de reposição com simplicidade.

## 2. Perfil de Operação-Alvo

- mercadinho;
- loja de bairro;
- pequeno depósito;
- operação com baixa especialização por função.

## 3. Escopo Funcional (Alto Impacto)

1. Recebimento com conferência simples.
2. Endereçamento básico (ex.: frente/fundo).
3. Inventário cíclico guiado.
4. Avarias e perdas com motivo obrigatório.
5. Alertas de ruptura, excesso e validade.
6. Reposição sugerida sem complexidade excessiva.

## 4. Fluxo Operacional Resumido

1. Entrada de nota e conferência.
2. Armazenagem com endereçamento básico.
3. Registro de avaria quando aplicável.
4. Ciclo periódico de contagem com snapshot.
5. Geração de alertas operacionais.
6. Sugestão de reposição conforme regras de cobertura e giro.

## 5. Regras-Chave do MVP

- Toda nota deve permitir apontamento explícito de avaria.
- Item com avaria não entra em saldo vendável.
- Inventário cíclico deve ocorrer sem paralisação total da operação.
- Contagens devem manter histórico comparável (última vs atual).
- Cobertura sugerida deve respeitar shelf life.
- Reposição deve considerar classe do item e risco de ruptura.

## 6. Fronteira do MVP (o que fica fora por enquanto)

- slotting avançado;
- roteirização complexa de picking;
- otimização multi-armazém;
- automações de grande escala com alta dependência de dispositivos especializados.

## 7. Indicadores de Sucesso

- acuracidade de estoque;
- ruptura (%);
- excesso (%);
- perda por avaria (% e valor);
- aderência à reposição sugerida.

## 8. Mapeamento para Documentos Detalhados

- Curva ABC e política de cobertura:
`Regra_de_negocios/Estoque/curva/regra_abc/curva_abcd.md`
- Shelf life e limite de cobertura:
`Regra_de_negocios/Estoque/curva/regra_abc/shelf_life.md`
- Giro e gatilho de reposição:
`Regra_de_negocios/Estoque/giro/regra_giro/giro_estoque.md`
- Sazonalidade:
`Regra_de_negocios/Estoque/sazonalidade/regra_sazo/sazonalidade.md`
- Inventário cíclico:
`Regra_de_negocios/Estoque/ciclico/regra_ciclico/ciclico.md`
- Avarias:
`Regra_de_negocios/Estoque/avarias/regra_avarias/avarias.md`

## 9. Resultado Esperado

Ter um produto de execução de estoque com mentalidade WMS, porém enxuto, adotável por operações pequenas e pronto para evoluir gradualmente sem sobrecarga de processo.
