# Matriz de Integracao: Regras, Abas, API e Midias

## 1. Objetivo

Conectar documentacao funcional (`.md`), experiencia do operador (abas/telas), contratos de API e conteudo educacional (midias), evitando modulos isolados.

## 2. Principio

Cada regra de negocio deve ter:

1. uma aba/tela no produto;
2. um conjunto minimo de endpoints/eventos;
3. um indicador operacional;
4. uma midia ou ajuda contextual (quando aplicavel).

## 3. Matriz Conceitual (Principal)

| Dominio | Regra de Negocio | Aba/Tela | API/Evento Minimo | KPI Principal | Midia de Apoio |
| --- | --- | --- | --- | --- | --- |
| WMS Enxuto | `wms_enxuto_mvp.md` | Visao Geral da Operacao | `GET /operacao/resumo` | nivel de servico | - |
| SKU | `sku.md` | Cadastro e Variacoes | `POST /skus` | integridade de cadastro SKU | `sku.png` |
| Address (Enderecamento) | `address.md` | Address Operacional | `POST /address/sugestoes` | taxa de acerto de localizacao | - |
| Recebimento | `recebimento_conferencia.md` | Recebimento e Conferencia | `POST /recebimentos/conferencia` | divergencia no recebimento | - |
| Avarias | `avarias.md` | Avarias e Perdas | `POST /avarias/registros` | perda por avaria | - |
| Ciclico | `ciclico.md` | Inventario Ciclico | `POST /inventario/contagens` | acuracidade | `Inventario_Ciclico.mp4` |
| Curva ABC | `curva_abcd.md` | Curva e Politica | `GET /curva/classificacao` | aderencia a politica | `curva_abcd.mp4` |
| Giro | `giro_estoque.md` | Giro e Cobertura | `GET /giro/itens` | giro por classe | - |
| Sazonalidade | `sazonalidade.md` | Previsao e Sazonalidade | `GET /previsao/sazonalidade` | erro de previsao (WAPE) | - |
| Shelf Life | `shelf_life.md` | Validade e Risco | `GET /validade/riscos` | perda por vencimento | - |
| Kanban | `kanban.md` | Quadro de Reposicao | `GET /kanban/quadro` | ruptura evitada por kanban | - |
| Governanca Orcamentaria | `regra_orcamentaria.md` | Orcamento de Compra | `POST /compras/simulacao` | consumo orcamentario | - |

## 4. Fluxo Integrado Entre Modulos

1. SKU define a unidade minima de controle.
2. Address/Enderecamento define e valida localizacao por SKU.
3. Recebimento atualiza saldo por SKU.
4. Avarias removem saldo vendavel e impactam perdas por SKU.
5. Inventario ciclico corrige divergencia e melhora acuracidade por SKU/endereco.
6. Curva + Giro + Sazonalidade calculam necessidade por SKU.
7. Kanban traduz necessidade em fila visual puxada para SKUs elegiveis.
8. Shelf life limita cobertura por SKU/lote.
9. Governanca orcamentaria valida viabilidade de compra.
10. Sistema gera sugestao final + alertas.

## 5. Matriz de Documentos Base

| Tipo | Documento | Caminho |
| --- | --- | --- |
| Modelagem | Modelagem de Dominio WMS | `Regra_de_negocios/Estoque/integracao/modelagem_dominio_wms.md` |
| Casos de Uso | Casos de Uso WMS | `Regra_de_negocios/Estoque/integracao/casos_de_uso_wms.md` |
| Contrato Executavel | RegistrarRecebimento | `Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_recebimento.md` |
| Contrato Executavel | RegistrarAjusteEstoque | `Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_ajuste_estoque.md` |
| Caso de Uso | Recebimento e Conferencia | `Regra_de_negocios/Estoque/recebimento/caso_de_uso/recebimento_conferencia.md` |
| Caso de Uso | Enderecamento Basico | `Regra_de_negocios/Estoque/enderecamento/caso_de_uso/enderecamento_basico.md` |
| Regra | Address (Enderecamento) | `Regra_de_negocios/Estoque/address/address_regra/address.md` |
| Regra | Kanban de Reposicao | `Regra_de_negocios/Estoque/kanban/regra_kanban/kanban.md` |
| Integracao | Contrato de Eventos | `Regra_de_negocios/Estoque/integracao/contrato_eventos.md` |
| Integracao | Dicionario de Campos Compartilhados | `Regra_de_negocios/Estoque/integracao/dicionario_campos_compartilhados.md` |

## 6. Uso de Midias no Produto

| Contexto | Acao Recomendada |
| --- | --- |
| Primeira utilizacao da aba | Exibir ajuda contextual curta (2-5 min) |
| Operacao recorrente | Botao `Como funciona` dentro da aba |
| Treinamento interno | Card lateral `Treinamento rapido` |
| Gestao de equipe | Registro de visualizacao (opcional) |

## 7. Padrao Minimo para Nova Regra

| Item Obrigatorio | Descricao |
| --- | --- |
| Objetivo de negocio | Qual problema a regra resolve |
| Entradas e saidas | Dados que entram e resultado esperado |
| Alertas | Situacoes de risco e notificacoes |
| Aba/Tela responsavel | Onde a regra aparece para o operador |
| Endpoint/Evento | Contrato tecnico minimo |
| KPI | Indicador para medir efetividade |
| Midia de apoio | Material educacional quando fizer sentido |

## 8. Ordem de Evolucao Recomendada

| Etapa | Entregavel |
| --- | --- |
| 1 | Regras de negocio (`.md` de dominio) |
| 2 | Modelagem de dominio (`modelagem_dominio_wms.md`) |
| 3 | Casos de uso (`casos_de_uso_wms.md`) |
| 4 | Contratos (eventos/campos/API) |
| 5 | Implementacao tecnica (codigo, banco, endpoints) |

## 9. Separacao de Responsabilidades (Obrigatoria)

| Camada | Responsabilidade | Nao deve fazer |
| --- | --- | --- |
| WMS (dominio operacional) | aplicar regras deterministicas, validar politicas, executar recebimento/estoque/reposicao | inferencia estatistica, deteccao automatica de padrao, previsao probabilistica |
| Estatistica/ML (motor desacoplado) | identificar sazonalidade, anomalias, previsoes e recomendar parametros | executar movimentacao operacional no estoque |

Regra de integracao:

1. O motor estatistico/ML consome dados do WMS.
2. O motor retorna sinais/parametros.
3. O WMS aplica os parametros com regras explicitas e auditaveis.
