**JADE-STOCK**

Adendos à Documentação Técnica

Seção 11 — WMS: Importação de NF-e via XML   ·   Seção 12 — API PDV: Frente de Caixa   ·   Seção 13 — WMS: Gestão Inteligente de Múltiplos Fornecedores e Aprendizado Contínuo

v1.2  —  Complemento à Documentação Técnica v1.0

> **Nota de estado atual (26/02/2026):** este arquivo concentra adendos arquiteturais e trilhas em evolução. O núcleo estável da API WMS para operação diária está em `WMS/wms/interfaces/api/app.py` e `WMS/README.md`. Endpoints XML/PDV descritos aqui devem ser tratados como extensão progressiva.

# **11\. Adendo WMS — Importação de NF-e via XML**

O módulo WMS é responsável pelo ciclo de vida completo do estoque: recebimento, movimentação, inventário, avarias e reposição. O adendo desta seção documenta a extensão de recebimento via importação de arquivo XML de Nota Fiscal Eletrônica (NF-e), que é o padrão nacional SEFAZ para registro de operações de compra. Esta funcionalidade não faz parte do módulo Contábil — ela pertence inteiramente ao WMS porque seu resultado é uma operação de recebimento de mercadoria, idêntica em efeito a um recebimento conferido manualmente.

| PRINCÍPIO DE DESIGN Importar uma NF-e é receber mercadoria. O XML é apenas o veículo que carrega as informações do fornecedor. O resultado final — saldo atualizado, eventos emitidos, histórico auditável — é idêntico ao de um recebimento manual. O módulo Contábil consumirá os mesmos eventos gerados por qualquer outro recebimento, sem distinção de origem. |
| :---- |

## **11.1 Contexto: Por que importar XML no WMS?**

Quando o Jade-stock recebe uma compra de fornecedor, a operação fiscal obriga a emissão de uma NF-e pelo vendedor. O comprador recebe esse documento em formato XML — um arquivo padronizado pela SEFAZ que contém a relação completa de itens, quantidades, valores e dados fiscais da operação. Sem integração de XML, o operador precisaria digitar manualmente cada item da nota no sistema — processo lento, sujeito a erros e incompatível com a escala de operação de um comércio real.

A importação de XML resolve esse problema eliminando a entrada manual: o operador faz upload do arquivo, o WMS interpreta os itens, o operador revisa e confirma. O processo é guiado, auditável e muito mais rápido. É uma das funcionalidades de maior impacto prático imediato no dia a dia da operação.

## **11.2 Endpoint de Importação**

A importação segue o mesmo padrão de semântica HTTP definido para todos os endpoints do Jade-stock (RFC 9110 e OpenAPI 3.1). O fluxo é dividido em duas etapas para separar a análise da confirmação — o operador sempre tem a oportunidade de revisar antes de qualquer alteração de saldo.

| Método | Endpoint | Descrição |
| :---- | :---- | :---- |
| **POST** | /wms/v1/xml/analisar | Faz upload do XML e retorna análise: itens parseados, sugestões de vinculação e alertas. Não altera saldo. |
| **POST** | /wms/v1/xml/confirmar | Confirma a importação com as decisões do operador (vínculos, avarias). Altera saldo e emite eventos. |
| **GET** | /wms/v1/recebimentos/{id}/xml | Recupera o XML original arquivado vinculado a um recebimento. |

**Etapa 1 — Análise (\`/analisar\`):** O endpoint recebe o arquivo XML via multipart/form-data. O sistema parseia o arquivo, identifica os itens da nota (cEAN, xProd, NCM, CFOP, qCom, vUnCom) e executa o algoritmo de vinculação de produtos descrito na seção 11.4. O retorno é um objeto de análise completo que o front-end usa para renderizar a tela de revisão. **Nenhum saldo é alterado nesta etapa.** O status 200 indica que o XML foi parseado com sucesso — não que o recebimento foi registrado.

**Etapa 2 — Confirmação (\`/confirmar\`):** O operador revisa a análise no front-end, faz os ajustes necessários (vinculações manuais, marcação de avarias) e envia a confirmação. O payload inclui as decisões do operador para cada item. Somente aqui o WMS atualiza saldos, emite eventos na Event Store e arquiva o XML original. Requer Idempotency-Key no header para prevenir registros duplicados em caso de falha de rede.

## **11.3 Fluxo de Processamento do XML**

O processamento do arquivo XML segue uma sequência de validações progressivas antes de qualquer interação com o operador:

* **Validação estrutural:** O sistema verifica que o arquivo é um XML válido e segue o schema da NF-e (namespace http://www.portalfiscal.inf.br/nfe). XMLs malformados ou de tipos incompatíveis (CT-e, MDF-e) são rejeitados com 422 Unprocessable Entity e mensagem descritiva.

* **Extração de cabeçalho:** CNPJ do emitente, número da nota, série, data de emissão e chave de acesso são extraídos do elemento \<ide\> e armazenados como metadados do recebimento.

* **Extração de itens:** Cada elemento \<det\> é processado para extrair: código EAN (cEAN), descrição (xProd), NCM, CFOP, quantidade comercial (qCom), unidade (uCom) e valor unitário (vUnCom).

* **Verificação de duplicidade:** A chave de acesso da NF-e é verificada contra o histórico de recebimentos do tenant. Se a mesma nota já foi importada anteriormente, o sistema retorna 409 Conflict com referência ao recebimento original — prevenindo entrada dupla de estoque.

* **Execução do algoritmo de vinculação:** Descrito em detalhe na seção 11.4.

## **11.4 Vinculação Inteligente de Produtos — Product Matching**

| POR QUE EXISTE ESSE PROBLEMA O nome de um produto na NF-e do fornecedor raramente coincide com o nome cadastrado no sistema. O fornecedor escreve 'COCA COLA 2L PET RETORNAVEL GRUPO SOLAR' — o sistema tem 'Coca-Cola 2L'. São o mesmo produto, mas a comparação literal retorna zero correspondências. Sem vinculação inteligente, cada importação criaria produtos duplicados no catálogo. |
| :---- |

O algoritmo de vinculação executa uma comparação multi-critério entre cada item do XML e os produtos já cadastrados no banco de dados do tenant. O objetivo é sugerir a correspondência mais provável e deixar para o operador apenas os casos verdadeiramente ambíguos.

### **Critérios de Comparação**

A pontuação de correspondência (0 a 100\) é calculada combinando quatro critérios com pesos distintos:

| Critério | Peso | Descrição |
| :---- | :---- | :---- |
| Código EAN/GTIN (cEAN) | 40% | Correspondência exata do código de barras. Se o EAN bate, a pontuação desse critério é 100\. É o critério mais confiável. |
| Código NCM | 20% | Classificação fiscal do produto. Itens do mesmo NCM são da mesma categoria. Confiável para reduzir falsos positivos. |
| Similaridade de descrição | 30% | Algoritmo de distância de edição normalizada (Levenshtein) entre xProd do XML e o nome do produto no banco, após normalização (minúsculas, remoção de acentos e pontuação). |
| Histórico do fornecedor | 10% | Se o CNPJ do emitente já foi vinculado anteriormente ao mesmo produto, essa correspondência recebe bônus. Aprende com o histórico do tenant. |

### **Estados de Correspondência por Item**

Com base na pontuação final, cada item do XML recebe um dos três estados:

* **MATCHED (pontuação ≥ 85):** O sistema tem alta confiança na correspondência. O item é vinculado automaticamente ao produto cadastrado. O operador vê o vínculo sugerido e pode aceitar sem revisão ou corrigir se discordar.

* **AMBIGUOUS (pontuação entre 50 e 84):** O sistema encontrou candidatos mas não tem certeza suficiente para vincular automaticamente. O operador deve revisar a lista de candidatos e escolher o produto correto — ou indicar que é um produto novo.

* **NEW (pontuação \< 50 ou nenhum candidato):** Nenhum produto no catálogo corresponde ao item do XML. O sistema apresenta o item para cadastro como novo produto, pré-preenchido com os dados do XML (descrição, EAN, NCM, unidade).

### **Vinculação Manual e Aprendizado**

Para qualquer item, independentemente do estado sugerido, o operador pode substituir a decisão do algoritmo pela sua própria. Se o operador vincula manualmente o item do XML 'COCA COLA 2L PET RETORNAVEL GRUPO SOLAR' ao produto 'Coca-Cola 2L', o sistema registra essa associação no histórico do fornecedor (CNPJ \+ xProd → produto\_id). Na próxima importação de NF-e do mesmo fornecedor, esse par já receberá pontuação máxima pelo critério de histórico, eliminando a necessidade de revisão manual recorrente.

## **11.5 Marcação de Avarias na Importação**

A tela de revisão da importação integra o fluxo de avarias já documentado no WMS. Em vez de descobrir uma avaria depois que o recebimento já foi confirmado, o operador pode registrá-la diretamente na etapa de revisão — antes da confirmação final.

| POR QUE ISSO É IMPORTANTE Em muitos cenários, o operador recebe a mercadoria, percebe que parte veio danificada, mas não pode recusar toda a NF-e — as outras mercadorias são necessárias. Com essa funcionalidade, ele recebe tudo, marca os itens avariados na própria tela de importação, e o sistema trata cada grupo de forma adequada sem passos extras. |
| :---- |

### **Mecânica da Marcação**

Na tela de revisão, cada item do XML tem um campo de quantidade avariada (padrão zero). O operador pode inserir a quantidade que chegou danificada — que deve ser menor ou igual à quantidade total do item na nota. Por exemplo: NF-e traz 20 unidades de um item; o operador marca 3 como avariadas.

**Regra de consistência:** A quantidade avariada nunca pode superar a quantidade da NF-e, pois o recebimento é sempre pelo total da nota (obrigação fiscal). O saldo recebido entra integralmente — mas o sistema imediatamente separa as unidades avariadas para o fluxo de avarias.

### **Efeito na Confirmação**

Ao confirmar o recebimento com avarias, o sistema executa atomicamente as seguintes operações para os itens marcados:

* Registra a quantidade total da NF-e como recebida (ex.: 20 unidades entram no saldo).

* Move as unidades avariadas para endereço de quarentena dedicado (se configurado) ou as marca com status avaria\_pendente no próprio endereço de destino.

* Emite recebimento\_conferido cobrindo a totalidade dos itens, com indicação da quantidade avariada no payload.

* Emite avaria\_registrada para cada item com avaria, com correlation\_id compartilhado com o evento de recebimento — garantindo rastreabilidade direta entre a nota fiscal e a avaria registrada.

* A partir daí, o fluxo de avarias segue normalmente: avaria\_aprovada (ou reprovada) via workflow já existente no WMS, podendo gerar devolução ao fornecedor ou ajuste de valor de indenização.

## **11.6 Confirmação e Transação**

O endpoint /confirmar executa a operação inteira em uma única transação PostgreSQL. O payload de confirmação inclui, para cada item: o produto\_id ao qual foi vinculado, a quantidade total, a quantidade avariada e o endereço de destino no WMS. Toda a lógica de vinculação já foi resolvida na etapa de análise — neste ponto, o sistema apenas executa as decisões do operador.

Caso qualquer etapa da transação falhe — por exemplo, endereço de destino inválido ou produto sem cadastro completo — a transação inteira é revertida e o recebimento não é registrado. O operador recebe uma mensagem descritiva indicando qual item causou o problema. O XML original permanece arquivado no banco para reprocessamento.

## **11.7 Catálogo de Eventos — Importação XML**

Os eventos emitidos pela importação de XML são adicionados ao catálogo WMS existente (Seção 3.2 da documentação base):

**NOVOS EVENTOS — IMPORTAÇÃO NF-E**

**▸** xml\_analisado

Emitido após análise bem-sucedida do XML. Payload inclui chave de acesso, CNPJ do emitente, número de itens parseados, itens com status MATCHED/AMBIGUOUS/NEW e itens com avaria pré-marcada.

**▸** recebimento\_xml\_confirmado

Emitido após confirmação bem-sucedida. Complementa o recebimento\_conferido padrão com campo xml\_chave\_acesso e xml\_numero\_nota, permitindo ao módulo Contábil cruzar o lançamento com o documento fiscal de origem.

# **12\. API PDV — Frente de Caixa**

O módulo de Ponto de Venda (PDV) é o quarto domínio do Jade-stock — ao lado do WMS, Contábil e IA. Seu propósito é registrar operações de venda ao cliente final, integrando-se ao WMS para dar baixa no estoque e emitindo eventos na Event Store para consumo futuro pelo módulo Contábil. Em sua fase inicial, o PDV opera sem emissão de NF-e de saída: gera apenas um comprovante interno em PDF para controle do operador. A emissão fiscal é uma evolução planejada para fase posterior.

| DECISÃO DE DESIGN: PDV COMO API INDEPENDENTE O PDV poderia ser implementado como parte do WMS, já que ambos movimentam estoque. A separação como API independente foi escolhida por duas razões: (1) o ciclo de vida de uma venda tem semântica própria — caixa aberto, venda em andamento, pagamento, troco, comprovante — que é diferente da semântica de movimentação de estoque; (2) a evolução futura do PDV (integração fiscal, múltiplas formas de pagamento, TEF) é independente da evolução do WMS. Módulos separados evoluem sem se impedir. |
| :---- |

## **12.1 Posicionamento na Arquitetura**

O PDV segue os mesmos princípios arquiteturais dos módulos existentes:

* **API RESTful local:** exposta em porta dedicada (ex.: 8004), comunicando-se via localhost com o WMS (porta 8000 por padrão local, configurável) e com a Event Store.

* **Schema próprio no PostgreSQL:** pdv, com permissões restritas. O módulo WMS não tem acesso ao schema pdv; o PDV acessa o WMS exclusivamente via SDK, nunca via query direta.

* **Semântica HTTP conforme RFC 9110:** status codes com propósito, erros padronizados com correlation\_id, idempotência em operações críticas via Idempotency-Key.

* **Contrato OpenAPI 3.1:** todos os endpoints documentados antes da implementação, com exemplos de request e response.

* **Event Store:** toda operação relevante emite evento padronizado. O módulo Contábil consumirá esses eventos sem qualquer alteração no PDV quando estiver pronto.

## **12.2 Schema de Dados — \`pdv\`**

O schema pdv mantém as entidades próprias do domínio de venda, sem duplicar dados do WMS:

| Tabela | Campos principais | Responsabilidade |
| :---- | :---- | :---- |
| caixa\_sessoes | id, operador\_id, tenant\_id, aberto\_em, fechado\_em, saldo\_abertura, saldo\_fechamento, status | Controla abertura e fechamento do caixa por turno. Nenhuma venda é registrada fora de uma sessão ativa. |
| vendas | id, sessao\_id, correlation\_id, status, total, forma\_pagamento, criado\_em, concluido\_em, cancelado\_em | Representa uma transação de venda. Status: rascunho → concluida / cancelada. |
| venda\_itens | id, venda\_id, produto\_id, descricao\_snapshot, quantidade, preco\_unitario\_snapshot, subtotal | Itens de uma venda. descricao e preco são snapshots do momento da venda — nunca referências vivas ao catálogo, pois o preço pode mudar. |
| produto\_cache | produto\_id, descricao, preco\_venda, unidade, ativo, sincronizado\_em | Cache local dos produtos do WMS, sincronizado periodicamente. Permite ao PDV operar mesmo que o WMS esteja momentaneamente indisponível. |

**Nota sobre o \`produto\_cache\`:** O PDV não gerencia catálogo de produtos — essa é responsabilidade do WMS. O cache local é mantido pelo SDK do PDV, que sincroniza periodicamente as alterações do WMS. O operador pesquisa e adiciona produtos pelo nome ou código de barras — o PDV consulta o cache local, que é mais rápido e resiliente a falhas momentâneas de rede interna.

## **12.3 Endpoints e Semântica HTTP**

**SESSÃO DE CAIXA**

| Método | Endpoint | Descrição |
| :---- | :---- | :---- |
| **POST** | /pdv/v1/sessoes | Abre sessão de caixa. Registra saldo inicial informado pelo operador. Retorna 201 com o sessao\_id. |
| **PATCH** | /pdv/v1/sessoes/{sessao\_id}/fechar | Fecha a sessão ativa. Registra saldo final, sangrias e total de vendas do turno. Retorna 200\. |
| **GET** | /pdv/v1/sessoes/{sessao\_id} | Retorna estado atual da sessão: total vendido, número de transações, status. |

**VENDAS**

| Método | Endpoint | Descrição |
| :---- | :---- | :---- |
| **POST** | /pdv/v1/vendas | Inicia nova venda na sessão ativa. Retorna 201 com venda\_id e status 'rascunho'. Sem itens ainda. |
| **POST** | /pdv/v1/vendas/{venda\_id}/itens | Adiciona item à venda. Verifica disponibilidade no WMS (via SDK) antes de adicionar. 409 se sem estoque. |
| **DELETE** | /pdv/v1/vendas/{venda\_id}/itens/{item\_id} | Remove item do rascunho. Só permitido enquanto venda está em status 'rascunho'. |
| **POST** | /pdv/v1/vendas/{venda\_id}/concluir | Finaliza a venda. Requer Idempotency-Key. Deduz estoque no WMS, gera comprovante e emite evento. 200 se já concluída (idempotente). |
| **POST** | /pdv/v1/vendas/{venda\_id}/cancelar | Cancela venda. Se já concluída, executa estorno no WMS. Se ainda em rascunho, descarta sem alterar estoque. |
| **GET** | /pdv/v1/vendas/{venda\_id}/comprovante | Retorna o comprovante em PDF. Disponível apenas para vendas concluídas. |

**CONSULTAS E RELATÓRIOS**

| Método | Endpoint | Descrição |
| :---- | :---- | :---- |
| **GET** | /pdv/v1/vendas | Lista vendas com filtros: sessao\_id, status, data. Paginação por cursor. |
| **GET** | /pdv/v1/relatorios/caixa/{sessao\_id} | Resumo do fechamento: total vendido, número de vendas, formas de pagamento, cancelamentos. |
| **GET** | /pdv/v1/produtos/buscar?q={termo} | Busca produtos no cache local por nome ou código de barras. Retorna lista para o operador selecionar. |

## **12.4 Integração com o WMS via SDK**

O PDV nunca acessa o banco de dados do WMS diretamente. Toda interação ocorre via SDK, que encapsula as chamadas HTTP ao módulo WMS. Essa separação garante que o contrato entre os dois módulos seja explícito, versionado e testável.

### **Verificação de Estoque na Adição de Item**

Ao adicionar um item à venda, o SDK do PDV chama WMS.consultar\_saldo(produto\_id, quantidade\_solicitada). Se o WMS confirmar saldo suficiente, o item é adicionado ao rascunho. Se não, o PDV retorna 409 Conflict com mensagem clara: **"Estoque insuficiente: disponível X unidades, solicitado Y."** O saldo no WMS **não é reservado** neste momento — apenas consultado. A dedução ocorre somente na confirmação.

### **Dedução de Estoque na Conclusão da Venda**

O endpoint /concluir executa a sequência abaixo de forma **atomicamente coordenada**. Se qualquer etapa falhar, a operação é revertida por completo:

* O PDV solicita ao WMS a dedução de cada item via WMS.registrar\_saida(produto\_id, quantidade, correlation\_id).

* O WMS valida novamente o saldo (pode ter mudado desde a consulta), executa a dedução e emite movimentacao\_estoque\_registrada.

* Se qualquer item falhar (ex.: estoque zerou entre a consulta e a conclusão), o WMS reverte a dedução dos itens já processados e retorna erro. O PDV cancela a conclusão e informa o operador.

* Somente após confirmação de todos os itens, o PDV registra a venda como concluida, gera o comprovante e emite venda\_concluida.

### **Estorno na Cancelamento de Venda**

Se uma venda concluída for cancelada, o PDV chama WMS.estornar\_saida(produto\_id, quantidade, correlation\_id) para cada item. O WMS reverte as deduções e emite ajuste\_estoque\_registrado com referência ao correlation\_id da venda original. O PDV emite venda\_cancelada. O módulo Contábil, ao consumir venda\_cancelada, saberá que deve reverter o lançamento financeiro associado ao correlation\_id da venda.

## **12.5 Idempotência e Segurança Transacional**

A conclusão de uma venda é a operação mais crítica do PDV: ela deduz estoque, gera comprovante e move dinheiro. Uma falha de rede no momento da confirmação poderia resultar em estoque deduzido sem venda registrada — ou vice-versa. A estratégia de idempotência do Jade-stock resolve esse problema:

* O front-end gera um Idempotency-Key único (UUID v4) antes de enviar a requisição de conclusão e o inclui no header.

* O PDV armazena a chave e o resultado da operação ao concluir. Se receber a mesma Idempotency-Key novamente, retorna o resultado original sem reprocessar — garantindo que uma falha de rede seguida de retry não gere venda duplicada.

* A chave expira após 24 horas. Após esse período, uma nova tentativa com a mesma chave seria tratada como nova operação.

## **12.6 Catálogo de Eventos do Domínio PDV**

Todos os eventos seguem o contrato padrão da Event Store definido na Seção 3.1 da documentação base: event\_name, event\_id, occurred\_at, actor\_id, tenant\_id, correlation\_id, schema\_version, payload.

**EVENTOS DE SESSÃO DE CAIXA**

**▸** caixa\_aberto

Emitido quando o operador abre o turno. Payload: sessao\_id, operador\_id, saldo\_abertura. O módulo Contábil usa esse evento para abrir o período contábil de caixa do dia.

**▸** caixa\_fechado

Emitido no fechamento do turno. Payload: sessao\_id, total\_vendas, total\_cancelamentos, saldo\_fechamento, formas\_pagamento (dicionário com totais por método). Alimenta o relatório de fechamento de caixa.

**EVENTOS DE VENDA**

**▸** venda\_iniciada

Emitido ao criar a venda. Payload mínimo: venda\_id, sessao\_id. Marca o início da transação para fins de auditoria de tempo de atendimento.

**▸** venda\_concluida

Evento central do domínio PDV. Payload: venda\_id, itens (lista com produto\_id, quantidade, preco\_snapshot e subtotal), total, forma\_pagamento, troco. O módulo Contábil consumirá esse evento para gerar o lançamento: D: Caixa / C: Receita de Vendas e D: CMV / C: Estoque.

**▸** venda\_cancelada

Emitido ao cancelar venda. Referencia o correlation\_id da venda\_concluida original, permitindo ao Contábil estornar o lançamento sem busca adicional. Payload: venda\_id, motivo\_cancelamento, correlation\_id\_original.

## **12.7 Comprovante PDF**

O comprovante é um documento interno — não é uma NF-e e não tem validade fiscal na fase 1\. Seu propósito é dar ao cliente e ao operador um registro legível da transação. É gerado sob demanda pelo endpoint /comprovante e construído a partir dos dados da venda persistidos no banco.

Conteúdo mínimo do comprovante:

* Cabeçalho: nome do estabelecimento, CNPJ, data e hora da venda, número da venda.

* Corpo: lista de itens com descrição, quantidade, preço unitário e subtotal.

* Rodapé: total, forma de pagamento, troco (se houver), identificação do operador.

* Aviso explícito: **"Este comprovante não é uma Nota Fiscal."**

O PDF é gerado programaticamente no backend (sem dependência de serviço externo) e retornado como application/pdf. O front-end pode abri-lo para visualização em tela ou enviá-lo diretamente para a impressora térmica via SDK de impressão.

## **12.8 Estratégia de Evolução Futura**

A arquitetura do PDV foi desenhada para crescer em fases sem reescrita. As evoluções previstas são:

* **Fase 2 — NF-e de saída:** Integração com SEFAZ para emissão de NF-e ao consumidor. O evento venda\_concluida já contém todos os dados necessários. O módulo fiscal apenas consumirá esse evento e transmitirá o XML para a SEFAZ.

* **Fase 2 — Módulo Contábil ativo:** Ao implementar o Contábil, ele consumirá venda\_concluida e caixa\_fechado da Event Store — que já estão sendo emitidos desde a Fase 1\. O histórico acumulado de vendas poderá ser reprocessado retroativamente.

* **Fase 3 — Integração TEF:** Pagamentos com cartão via maquininha integrada ao sistema. O fluxo de conclusão de venda permanece o mesmo; apenas forma\_pagamento ganha novos estados e um provider de TEF é adicionado ao SDK.

* **Fase 3 — Multiforma de pagamento:** Uma venda dividida entre dinheiro e cartão. O modelo de dados já suporta isso com o campo formas\_pagamento como dicionário — na Fase 1, apenas um método é permitido por venda.

* **Fase 4 — IA de precificação:** O módulo IA, ao acumular histórico de vendas do PDV via Event Store, pode sugerir ajustes de preço por sazonalidade, giro e margem — consumindo os mesmos eventos sem qualquer alteração no PDV.

Jade-stock — Adendos à Documentação Técnica v1.1 — 2026

# **13\. Adendo WMS — Gestão Inteligente de Múltiplos Fornecedores e Aprendizado Contínuo**

"O sistema que aprende com a operação, não o contrário."

## **13.1 O Desafio da Cadeia de Suprimentos Flexível**

Na operação real de um armazém, um mesmo produto pode ser adquirido de diferentes fornecedores ao longo do tempo. O cenário é comum: a Ambev (distribuidor primário) eventualmente não consegue entregar, e o comprador recorre a um distribuidor intermediário que possui o mesmo produto em estoque.

O problema técnico que surge é: como o sistema trata o mesmo produto físico quando ele chega com identificadores (códigos de fornecedor) completamente diferentes?

| PRINCÍPIO DE DESIGN O estoque é cego quanto à origem. O produto físico na prateleira é o mesmo, independentemente de ter sido comprado da Ambev ou de um distribuidor local. O sistema deve refletir essa realidade: estoque unificado, rastreabilidade preservada, aprendizado contínuo sobre como cada fornecedor identifica cada produto. |
| :---- |

### **13.1.1 Modelo de Dados: Tabela de Vínculos Fornecedor-Produto**

A solução para o dilema dos múltiplos fornecedores é uma tabela de relacionamento N-para-N (muitos para muitos) que atua como um tradutor oficial entre o mundo externo (fornecedores) e o mundo interno (seu catálogo).

```sql
-- Schema: wms
-- Tabela: vinculo_fornecedor_produto

CREATE TABLE vinculo_fornecedor_produto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    fornecedor_id UUID NOT NULL REFERENCES fornecedor(id),
    codigo_fornecedor VARCHAR(100) NOT NULL,  -- Código do produto no sistema do fornecedor
    produto_id_interno UUID NOT NULL REFERENCES produto(id),
    fator_conversao DECIMAL(10,4) NOT NULL DEFAULT 1.0,  -- Multiplicador de unidades
    unidade_origem VARCHAR(10),  -- Unidade usada pelo fornecedor (CX, FD, PCT)
    unidade_destino VARCHAR(10), -- Sua unidade interna (UN, KG)
    
    -- Metadados de auditoria e aprendizado
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ultima_importacao TIMESTAMP,
    criado_por UUID REFERENCES usuario(id),
    
    -- Aprendizado: contador de uso para estatísticas
    vezes_utilizado INTEGER DEFAULT 0,
    
    -- Garantias de integridade
    UNIQUE(tenant_id, fornecedor_id, codigo_fornecedor),  -- Um código por fornecedor só pode apontar para UM produto interno
    CONSTRAINT fator_positivo CHECK (fator_conversao > 0)
);

-- Índices para performance nas consultas de importação
CREATE INDEX idx_vinculo_fornecedor ON vinculo_fornecedor_produto(fornecedor_id, codigo_fornecedor);
CREATE INDEX idx_vinculo_produto ON vinculo_fornecedor_produto(produto_id_interno);
```

**Por que uma tabela separada é a escolha correta?**

| Abordagem | Problema | Solução Jade-stock |
| :---- | :---- | :---- |
| Embutir no cadastro do produto | Um produto teria campos fixos para "código Ambev", "código Distribuidor X" — explode conforme novos fornecedores surgem | Tabela de vínculos permite N fornecedores para 1 produto |
| Criar produtos duplicados | Estoque fragmentado, relatórios inconsistentes | Tabela unifica o estoque no mesmo produto_id_interno |
| Guardar apenas no código | Perda de rastreabilidade fiscal | Tabela mantém histórico de quem forneceu o quê |

### **13.1.2 A Lógica de Conversão de Unidades**

O XML do fornecedor pode vir em unidades diferentes das que você controla internamente. A tabela de vínculos resolve isso com o campo fator_conversao.

**Exemplos Práticos:**

| Cenário | XML do Fornecedor | Seu Controle Interno | Fator | Lógica Aplicada |
| :---- | :---- | :---- | :---- | :---- |
| Caixa com múltiplas unidades | 10 CX (caixas) | UN (unidade) - cada caixa tem 12 unidades | 12 | Estoque final = 10 × 12 = 120 unidades |
| Peso com unidade diferente | 5 KG | GR (gramas) | 1000 | Estoque final = 5 × 1000 = 5000 gramas |
| Unidade compatível | 15 UN | UN | 1 | Estoque final = 15 unidades |

**Implementação da Lógica:**

```python
def calcular_quantidade_estoque(
    quantidade_xml: float, 
    fator_conversao: float,
    unidade_xml: str,
    unidade_destino: str
) -> dict:
    """
    Retorna a quantidade final e metadados da conversão.
    """
    quantidade_final = quantidade_xml * fator_conversao
    
    return {
        "quantidade_original": quantidade_xml,
        "unidade_original": unidade_xml,
        "fator_aplicado": fator_conversao,
        "quantidade_final": quantidade_final,
        "unidade_final": unidade_destino,
        "log_conversao": f"{quantidade_xml} {unidade_xml} × {fator_conversao} = {quantidade_final} {unidade_destino}"
    }
```

### **13.1.3 O Dilema dos Múltiplos Fornecedores — Resolvido**

**Cenário Real:**
- Produto: Refrigerante 2L (seu ID interno: PROD-REFRIG-2L)
- Fornecedor Primário: Ambev — código no sistema deles: AMB-REFRIG-2L
- Fornecedor Secundário: Distribuidor Local — código no sistema deles: DIST-999

**Como a Tabela Resolve:**

| fornecedor_id | codigo_fornecedor | produto_id_interno | fator_conversao |
| :---- | :---- | :---- | :---- |
| Ambev (UUID) | AMB-REFRIG-2L | PROD-REFRIG-2L | 12 (caixa com 12) |
| Distribuidor Local (UUID) | DIST-999 | PROD-REFRIG-2L | 1 (venda unitária) |

**Resultado:**
- Quando chega XML da Ambev com código AMB-REFRIG-2L, sistema sabe: é o mesmo produto, converte caixa para unidades.
- Quando chega XML do Distribuidor com código DIST-999, sistema sabe: é o mesmo produto, entrada direta.
- Estoque unificado: ambas as entradas somam no mesmo PROD-REFRIG-2L.

**Benefício Fiscal e Gerencial:**
- Histórico de compras por fornecedor preservado (via eventos)
- Custo médio calculado corretamente (preços diferentes por fornecedor)
- Rastreabilidade: você sabe que naquela data, veio do fornecedor secundário

### **13.1.4 Fluxo de Aprendizado Contínuo — A Tela de Conciliação**

O sistema não nasce sabendo todos os vínculos. Ele aprende com a operação. A Tela de Conciliação é o mecanismo de aprendizado supervisionado.

```
XML RECEBIDO → [SISTEMA CONSULTA VÍNCULOS] → 
    ├── Se vínculo encontrado → PROCESSAMENTO AUTOMÁTICO
    └── Se vínculo NÃO encontrado → TELA DE CONCILIAÇÃO
```

**Tela de Conciliação — Passo a Passo:**

**1. Apresentação dos Dados do XML:**
```
Item da Nota (Fornecedor: Distribuidor Local)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Código do Fornecedor: DIST-999
Descrição: REFRIGERANTE COLA 2L
Quantidade: 5
Unidade: UN
NCM: 2202.10.00
EAN/GTIN: 7891234567890
```

**2. Ações do Operador:**

| Ação | Comportamento do Sistema |
| :---- | :---- |
| Buscar produto existente | Campo de busca com autocomplete no catálogo interno |
| Vincular a produto existente | Sistema pergunta: "Qual o fator de conversão para este fornecedor?" (ex: 1 UN = 1 UN, ou 1 CX = 12 UN) |
| Cadastrar novo produto | Sistema pré-preenche formulário com dados do XML (descrição, NCM, EAN) |
| Ignorar item | Apenas se for item de bonificação ou algo que não entra em estoque |

**3. Confirmação do Vínculo:**

```json
// Payload enviado pelo front-end ao confirmar vínculo
{
  "item_xml_id": "item_001",
  "acao": "vincular_existente",
  "produto_id_interno": "PROD-REFRIG-2L",
  "fator_conversao": 1.0,
  "criar_vinculo_permanente": true  // Aprende para o futuro
}
```

**4. Aprendizado Concluído:**
- Sistema insere registro na tabela vinculo_fornecedor_produto
- Campo vezes_utilizado incrementado a cada uso
- Próxima nota do mesmo fornecedor com mesmo código: automático

### **13.1.5 Extração Inteligente para Cadastro de Novos Produtos**

Quando o produto é realmente novo (não encontrado na busca), o sistema usa os dados do XML para pré-preencher o cadastro, reduzindo digitação e erros.

**Mapeamento XML → Cadastro:**

| Campo no XML | Campo no Cadastro do Produto | Tratamento |
| :---- | :---- | :---- |
| xProd (descrição) | nome | Capitalizado, removido excesso de espaços |
| cEAN (código de barras) | gtin | Validado (se vazio ou não numérico, fica em branco) |
| NCM | ncm | Validado contra tabela oficial |
| uCom (unidade) | unidade_padrao | Mapeado: CX → UN (se fator configurado), UN → UN, KG → KG |

**Exemplo de Pré-Preenchimento:**

```json
// Dados extraídos do XML
{
  "descricao_fornecedor": "REFRIGERANTE GUARANA 2L",
  "gtin": "7894900011517",
  "ncm": "2202.10.00",
  "unidade": "UN"
}

// Formulário pré-preenchido para o operador
{
  "nome": "Refrigerante Guarana 2L",
  "gtin": "7894900011517",
  "ncm": "2202.10.00",
  "unidade_padrao": "UN",
  "categoria": "[aguardando seleção]",
  "preco_custo": "[campo vazio]",
  "preco_venda": "[campo vazio]"
}
```

### **13.1.6 Endpoints da Funcionalidade**

| Método | Endpoint | Descrição |
| :---- | :---- | :---- |
| POST | /wms/v1/vinculos/consultar | Consulta se código de fornecedor já tem vínculo |
| POST | /wms/v1/vinculos | Cria novo vínculo (aprendizado) |
| GET | /wms/v1/vinculos/fornecedor/{fornecedor_id} | Lista todos vínculos de um fornecedor |
| PATCH | /wms/v1/vinculos/{vinculo_id} | Atualiza fator de conversão |
| DELETE | /wms/v1/vinculos/{vinculo_id} | Remove vínculo (apenas se não usado em importações recentes) |
| GET | /wms/v1/produtos/busca-expressa?q={termo} | Busca otimizada para tela de conciliação |

### **13.1.7 Catálogo de Eventos — Aprendizado e Vínculos**

**NOVOS EVENTOS — GESTÃO DE FORNECEDORES**

**▸** vinculo_fornecedor_criado

Emitido quando um novo vínculo é estabelecido manualmente. Payload: fornecedor_id, codigo_fornecedor, produto_id_interno, fator_conversao, criado_por.

**▸** vinculo_fornecedor_utilizado

Emitido sempre que um vínculo existente é usado em uma importação. Payload: vinculo_id, importacao_id. Usado para estatísticas e auditoria.

**▸** produto_sugerido_importacao

Emitido quando o sistema pré-preenche um cadastro com dados do XML, mas o operador ainda não concluiu. Permite rastrear tentativas de cadastro.

### **13.1.8 Idempotência e Consistência em Vínculos**

Assim como nas movimentações de estoque, a criação de vínculos deve ser idempotente para evitar duplicidade em caso de retry.

**Regra:** O par (tenant_id, fornecedor_id, codigo_fornecedor) é único. Se o front-end tentar criar o mesmo vínculo duas vezes (mesma Idempotency-Key), o sistema retorna o vínculo existente com status 200 (não 201).

### **13.1.9 Exemplo Completo de Fluxo**

**Cenário:** Primeira compra de um fornecedor novo

1. Operador faz upload do XML → endpoint /wms/v1/xml/analisar
2. Sistema identifica item com código DIST-999 → consulta vínculos → não encontrado
3. Sistema retorna análise com status AMBIGUOUS para este item
4. Front-end renderiza Tela de Conciliação:
   - Dados do XML exibidos
   - Campo de busca para produto interno
5. Operador busca por "refrigerante 2L" → encontra PROD-REFRIG-2L
6. Operador seleciona e informa fator de conversão (1 UN = 1 UN)
7. Front-end envia confirmação para /wms/v1/vinculos
8. Sistema:
   - Cria registro na tabela de vínculos
   - Emite vinculo_fornecedor_criado
   - Agora pode processar o recebimento
9. Próxima nota do mesmo fornecedor → sistema reconhece automaticamente

### **13.1.10 Considerações sobre NFC-e (Nota Fiscal ao Consumidor)**

A mesma lógica de vínculos se aplica à NFC-e (venda no PDV), mas com uma diferença fundamental:

| Aspecto | NF-e (Compra) | NFC-e (Venda) |
| :---- | :---- | :---- |
| Direção | Entrada no estoque | Saída do estoque |
| Vínculo | Fornecedor → seu produto | Seu produto → descrição na venda |
| Conversão | Necessária (cx → un) | Necessária (cx → un) |
| Aprendizado | CNPJ do fornecedor + código | (não se aplica) |

Na NFC-e, o sistema não precisa "aprender" vínculos de fornecedores, mas sim garantir que a descrição impressa no cupom seja amigável ao cliente, enquanto o controle interno permanece rigoroso.

### **13.1.11 Resumo: O Que Foi Adicionado ao Sistema**

| Funcionalidade | Benefício |
| :---- | :---- |
| Tabela de vínculos fornecedor-produto | Um produto, múltiplos fornecedores, estoque unificado |
| Fator de conversão por fornecedor | Unidades diferentes, mesma contagem |
| Tela de conciliação com aprendizado | Sistema melhora com o uso |
| Extração inteligente para cadastro | Produtos novos cadastrados em segundos |
| Eventos de auditoria | Rastreabilidade completa de vínculos |

---

*Jade-stock — Adendos à Documentação Técnica v1.2 — 2026*

"Um sistema que aprende com a operação é um sistema que cresce com o negócio."
