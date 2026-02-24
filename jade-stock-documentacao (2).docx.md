

**JADE-STOCK**

*Estratégia, Arquitetura e Integração*

Documentação Técnica — v1.0

# **1\. Visão Geral do Sistema**

O Jade-stock é um sistema integrado que reúne três domínios distintos: Warehouse Management System (WMS), Contabilidade e Inteligência Artificial. Seu objetivo é otimizar operações logísticas, financeiras e preditivas de demanda dentro de um único ecossistema coeso, escalável e tolerante a falhas.

O sistema foi projetado levando em consideração uma equipe de desenvolvimento enxuta — de um a dois desenvolvedores — o que impõe requisitos específicos de arquitetura: cada decisão técnica deve reduzir a carga cognitiva de manutenção sem sacrificar a robustez ou a capacidade de crescimento futuro do produto.

O princípio norteador da arquitetura é o equilíbrio entre quatro eixos fundamentais: modularidade (cada domínio evolui de forma independente), segurança de execução (falhas em um módulo não propagam para outros), facilidade de manutenção (padrões consistentes que qualquer desenvolvedor familiar ao projeto consiga seguir) e tolerância a inconsistências de IA (outputs do motor de IA são tratados com verificação e validação antes de produzir efeitos colaterais em dados críticos).

# **2\. Arquitetura Técnica**

## **2.1 Monolito Modular vs. Microserviços Locais**

O Jade-stock adota uma abordagem híbrida que combina os benefícios do monolito modular com os do microserviço local, sem incorrer nos custos operacionais de uma arquitetura de microserviços distribuída completa.

### ***Monolito Modular***

Os três domínios — WMS, Contábil e Analytics (IA) — são organizados como módulos separados dentro do mesmo repositório de código, cada um com sua pasta, conjunto de responsabilidades e contrato de interface bem definidos. A comunicação entre módulos ocorre diretamente via chamadas de função, eliminando latência de rede e simplificando o rastreamento de bugs. Essa abordagem favorece a padronização do código, facilita revisões e evita o acoplamento excessivo que emerge quando módulos consomem APIs uns dos outros sem uma fronteira formal.

### ***Microserviços Locais***

Cada domínio expõe seus fluxos principais via uma API RESTful local, hospedada em localhost com porta dedicada. Isso garante que uma falha ou travamento em um módulo não bloqueie os demais, pois cada processo pode ser reiniciado de forma independente. A comunicação via localhost minimiza a latência, mantendo o isolamento de domínio. Módulos com alto consumo de CPU — especialmente o motor de IA — se beneficiam particularmente dessa separação, pois podem ser escalados ou substituídos sem interferir no WMS ou no Contábil.

## **2.2 SDK como Camada de Abstração**

O SDK é a interface oficial de integração entre o front-end e os módulos do sistema. Em vez de o front-end construir requisições HTTP manualmente, lidar com serializações JSON ou conhecer os detalhes internos de cada endpoint, ele utiliza funções de alto nível exportadas pelo SDK.

Um exemplo prático: para registrar uma entrada no estoque, o front-end chama MeuSistemaSDK.WMS.registrar\_entrada(payload), e o SDK se encarrega de construir a requisição, validar o contrato e retornar o resultado já tipado. Isso cria uma separação clara entre consumo e implementação, de modo que mudanças internas nos microserviços só exigem atualização do SDK, não do front-end.

O SDK também centraliza aspectos transversais como autenticação, logging, tratamento de erros padronizado e versionamento de contrato. Isso reduz drasticamente a complexidade cognitiva do desenvolvimento do front-end e facilita a evolução do backend sem quebrar clientes existentes.

Para garantir evolução segura, o SDK deve seguir versionamento semântico (ex.: v1.0, v1.1, v2.0). Versões menores adicionam funcionalidades mantendo compatibilidade retroativa; versões maiores podem introduzir mudanças de contrato, mas com período de depreciação explícito. Isso é especialmente importante quando mais de um cliente consome o SDK simultaneamente, como no caso de instalações em múltiplas máquinas.

## **2.3 Event Store e Arquitetura Baseada em Eventos**

A Event Store é o mecanismo central de resiliência do Jade-stock. Cada módulo — ao invés de chamar diretamente outro módulo — emite eventos padronizados para a Event Store. Os módulos consumidores processam esses eventos de forma assíncrona, desacoplando o produtor do consumidor e eliminando dependências de tempo real entre domínios.

### ***Fluxo de Eventos***

* O WMS conclui uma operação e emite um evento (ex.: movimentacao\_estoque\_registrada) para a Event Store.

* O módulo Contábil monitora a Event Store e, ao detectar eventos relevantes, processa as movimentações financeiras associadas de forma assíncrona.

* O módulo de IA consome eventos de inventário para alimentar seus modelos preditivos, sem travar o fluxo principal do WMS.

* Em caso de falha no processamento de um evento, o módulo consumidor registra o erro e o evento permanece na fila para nova tentativa (retry automático).

Esse modelo cria um amortecedor de falhas eficaz: se o módulo Contábil estiver temporariamente indisponível, o WMS continua operando normalmente e os eventos pendentes são processados assim que o Contábil se recuperar.

### ***Idempotência e Rastreabilidade***

Cada evento carrega um event\_id único (UUID) e um correlation\_id que agrupa eventos relacionados a uma mesma operação de negócio. A idempotência é garantida pelo uso do event\_id como chave de deduplicação: se o mesmo evento for processado mais de uma vez (por falha ou reenvio), o sistema identifica a duplicata e descarta o processamento redundante sem produzir efeitos colaterais.

### ***Retry e Dead-Letter Queue***

Para eventos que falham repetidamente no processamento, o sistema utiliza uma estratégia de retry com backoff exponencial: após a primeira falha, tenta novamente após 30 segundos; após a segunda, após 2 minutos; e assim por diante. Eventos que excedam o número máximo de tentativas (configurável, padrão: 5\) são movidos para uma Dead-Letter Queue (DLQ), onde ficam disponíveis para inspeção manual e reprocessamento controlado. Isso garante que nenhum evento crítico seja silenciosamente descartado.

## **2.4 Persistência Unificada com Isolamento Lógico**

Para evitar a proliferação de bancos de dados independentes — o que multiplicaria o custo de manutenção, backup e monitoramento — o Jade-stock adota um único banco de dados PostgreSQL, com isolamento lógico implementado via schemas separados.

* Schema wms: todas as tabelas de movimentação de estoque, recebimentos, endereçamento e inventário.

* Schema contabil: lançamentos contábeis, conciliações e relatórios financeiros.

* Schema ia: histórico de previsões, modelos treinados, logs de inferência e métricas de acurácia.

* Schema event\_store: tabela centralizada de eventos (events), com colunas indexadas por tenant\_id, event\_name e occurred\_at.

As permissões são restritas por schema: o módulo WMS possui permissão de escrita apenas no schema wms; o módulo Contábil pode ler o schema event\_store e escrever no schema contabil; o módulo de IA pode ler event\_store e wms (somente leitura) e escrever no schema ia. Isso previne que bugs ou erros de lógica em um módulo corrijam ou corrompam dados de outro domínio.

A tabela event\_store.events deve conter índices compostos em (tenant\_id, occurred\_at) e (event\_name, tenant\_id) para garantir consultas performáticas em cenários de replay de eventos e auditoria. O replay de eventos é a capacidade de reprocessar eventos históricos para reconstruir o estado de um módulo — fundamental em cenários de migração, correção de bugs ou inicialização de um novo módulo que precisa consumir o histórico.

# **3\. Contrato de Eventos**

## **3.1 Estrutura Padrão**

Todo evento emitido para a Event Store deve respeitar o seguinte contrato mínimo. Campos ausentes ou inválidos devem ser rejeitados na camada de emissão, nunca na camada de consumo.

| Campo | Tipo | Descrição |
| :---- | :---- | :---- |
| event\_name | *string* | Nome do evento em snake\_case. Ex.: movimentacao\_estoque\_registrada. |
| event\_id | *UUID v4* | Identificador único do evento. Utilizado para garantir idempotência no consumidor. |
| occurred\_at | *ISO 8601* | Timestamp UTC do momento em que o evento ocorreu no sistema produtor. |
| actor\_id | *string* | Identificador do usuário ou processo que gerou o evento. |
| tenant\_id | *string* | Identificador do tenant (cliente/filial), para suporte a multi-tenancy. |
| correlation\_id | *string* | Agrupa eventos relacionados a uma mesma operação de negócio. |
| schema\_version | *semver* | Versão do schema do payload. Permite evolução retrocompatível do contrato. |
| payload | *object* | Dados específicos do evento. Estrutura varia por event\_name e schema\_version. |

## **3.2 Catálogo de Eventos do Domínio WMS**

Os eventos abaixo representam o conjunto inicial do domínio WMS. Novos eventos devem ser adicionados ao catálogo antes de serem emitidos, garantindo rastreabilidade e documentação centralizada.

**Recebimento**

* recebimento\_conferido

* recebimento\_divergente

**Avarias**

* avaria\_registrada

* avaria\_aprovada

**Inventário Cíclico**

* contagem\_iniciada

* contagem\_confirmada

* divergencia\_identificada

**Reposição e Compras**

* reposicao\_sugerida

* compra\_aprovada

* compra\_rejeitada

**Movimentação de Estoque**

* movimentacao\_estoque\_registrada

* ajuste\_estoque\_registrado

## **3.3 Exemplo de Payload**

O exemplo abaixo ilustra a estrutura completa de um evento do tipo contagem\_confirmada, emitido ao término de uma contagem de inventário cíclico.

{  
  "event\_name":      "contagem\_confirmada",  
  "event\_id":        "evt\_7f3a9c2b-4d1e-4b8a-9f6d-2c8e1a0b3f5e",  
  "occurred\_at":     "2026-02-21T12:00:00Z",  
  "actor\_id":        "op\_42",  
  "tenant\_id":       "lojax",  
  "correlation\_id":  "cnt\_20260221\_001",  
  "schema\_version":  "1.0",  
  "payload": {  
    "item\_id":         "sku\_1",  
    "endereco":        "frente-A3",  
    "saldo\_anterior":  20,  
    "saldo\_contado":   18,  
    "divergencia":     \-2  
  }  
}

# **4\. Front-end: Cliente Rico**

## **4.1 Tecnologias Consideradas**

### ***Flutter***

Framework multi-plataforma da Google, com suporte nativo a Windows, Linux, macOS, iOS e Android a partir de uma única base de código Dart. Oferece máxima fidelidade ao Material Design, alta performance de renderização (engine própria, sem WebView) e APIs de integração com hardware como impressoras, scanners e balanças. É a opção mais robusta para aplicações que exigem experiência visual polida e integração de hardware em campo.

### ***Flet (Python)***

Framework que expõe o Flutter via Python, permitindo construir interfaces Flutter sem escrever Dart. Sua principal vantagem é a integração natural com o ecossistema Python já existente no backend do Jade-stock, facilitando o consumo de APIs internas, scripts e bibliotecas de IA. Reduz a barreira de entrada para equipes já familiarizadas com Python, sem abrir mão das capacidades visuais do Flutter.

## **4.2 Arquitetura Cliente \+ Backend**

O cliente rico executa localmente na máquina do operador, responsável por três frentes: renderização da interface de usuário, integração com periféricos de hardware (impressoras térmicas, leitores de código de barras, balanças e coletores) e exibição de dashboards analíticos com dados consumidos do backend.

O backend permanece centralizado na nuvem (ou em servidor local), hospedando os microserviços de WMS, Contábil, IA e integrações com serviços externos como gateways de pagamento. Toda a lógica de negócio reside no backend; o cliente rico é deliberadamente fino em termos de lógica, delegando decisões ao backend via SDK.

Atualizações de funcionalidades são aplicadas no backend e propagadas via SDK. O cliente rico, por consumir o SDK como dependência, recebe automaticamente novas capacidades sem necessidade de reinstalação completa da aplicação, exceto em casos de mudanças na camada de interface ou de integração com hardware.

## **4.3 Hot Reload Parcial**

Para minimizar interrupções durante atualizações de rotina, o cliente rico pode implementar hot reload parcial: novas rotas, telas ou dashboards são carregados dinamicamente sem reiniciar toda a aplicação. Isso é especialmente relevante em ambientes de operação contínua, como depósitos ou pontos de venda, onde reinicializações frequentes impactam a produtividade.

A implementação mais simples consiste em carregar a configuração de rotas de um arquivo de manifesto remoto na inicialização da aplicação. Quando o SDK detecta uma versão nova do manifesto, ele baixa a atualização em segundo plano e sinaliza para o cliente rico recarregar apenas os módulos afetados, mantendo o estado das telas abertas.

## **4.4 Compilação e Distribuição**

A partir de uma única base de código, são gerados builds nativos para cada sistema operacional suportado:

* Windows: executável .exe com instalador opcional (NSIS ou WiX).

* Linux: pacotes .AppImage (portável, sem instalação) e .deb/.rpm (integração com gerenciadores de pacote).

* macOS: bundle .app assinado, com suporte a distribuição via Homebrew ou download direto.

A base de código unificada elimina a necessidade de manter branches separados por plataforma, simplificando a cadência de releases e garantindo consistência de comportamento entre ambientes.

# **5\. Estratégia de Persistência e Dados**

## **5.1 PostgreSQL com Schemas Segregados**

A escolha por um único banco de dados PostgreSQL com schemas segregados reflete o princípio de minimizar a superfície de operação sem abrir mão do isolamento lógico. Um único servidor de banco de dados significa um único ponto de backup, monitoramento, rotina de manutenção (vacuum, analyze) e gerenciamento de conexões.

A segregação por schema garante que, mesmo no nível do banco de dados, os domínios não se misturem acidentalmente. Queries escritas pelo módulo WMS não têm visibilidade sobre as tabelas do schema contabil a menos que explicitamente autorizadas, o que previne erros de lógica que cruzem fronteiras de domínio.

## **5.2 Indexação da Event Store**

A tabela event\_store.events é o coração da resiliência do sistema e deve ser indexada estrategicamente para suportar os padrões de acesso mais comuns:

* Índice composto em (tenant\_id, occurred\_at DESC): para listar eventos recentes de um tenant específico.

* Índice composto em (tenant\_id, event\_name, occurred\_at): para filtrar eventos por tipo dentro de um tenant.

* Índice único em (event\_id): para verificação de idempotência.

* Índice em (correlation\_id): para rastrear todos os eventos de uma operação de negócio.

A tabela deve também incluir uma coluna processed\_at e status (pending, processed, failed, dead\_letter) para que os consumidores possam gerenciar o ciclo de vida dos eventos sem depender de filas externas, pelo menos nas fases iniciais do produto.

# **6\. Estratégia de Deploy e Escalabilidade**

## **6.1 Deploy Inicial: Servidor Único**

Na fase inicial, todos os microserviços podem coexistir em um único servidor, comunicando-se via localhost. Essa configuração simplifica radicalmente a operação: um único servidor para monitorar, um único conjunto de logs para analisar e um único ponto de deploy para gerenciar. A arquitetura desacoplada via APIs locais já prepara o sistema para a separação futura, sem impor sua complexidade prematuramente.

Um ponto de atenção nesse modelo: se o servidor cair, todos os módulos ficam indisponíveis simultaneamente. Para mitigar esse risco antes de adotar múltiplos servidores, recomenda-se configurar restart automático dos serviços (via systemd no Linux ou PM2 para Node.js) e manter backups periódicos do banco de dados em armazenamento separado.

## **6.2 Contêinerização**

À medida que o sistema cresce em complexidade ou número de instalações, a contêinerização via Docker se torna uma estratégia valiosa. Cada módulo é empacotado como uma imagem Docker independente, com todas as suas dependências, garantindo comportamento idêntico em qualquer ambiente que suporte o runtime de contêineres.

No contexto do Jade-stock, a contêinerização traz benefícios específicos: o módulo de IA — que frequentemente requer versões específicas de bibliotecas Python e drivers CUDA — pode ser atualizado independentemente do WMS sem risco de conflito de dependências. Da mesma forma, o módulo Contábil pode ser reiniciado para aplicar correções sem interromper o fluxo de registro de estoque.

A persistência de dados (PostgreSQL e volumes da Event Store) é mantida em Docker Volumes separados dos contêineres de aplicação. Isso significa que substituir uma imagem de contêiner por uma versão atualizada não afeta os dados persistidos, pois eles residem no volume, não dentro do contêiner.

A decisão de adotar contêineres deve ser guiada por necessidade concreta, não por tendência. Para um servidor único com uma equipe enxuta, o overhead de configuração de Docker Compose, gerenciamento de redes de contêineres e volumes pode superar os benefícios. O momento ideal de adoção é quando houver necessidade de múltiplos ambientes (desenvolvimento, homologação, produção), múltiplos servidores ou instalações em máquinas de clientes com ambientes heterogêneos.

## **6.3 Orquestrador de Atualizações de Contêineres**

Quando a contêinerização for adotada, o Jade-stock pode se beneficiar de um orquestrador de atualizações que aplique novas versões sem interromper o usuário final. O princípio central é o Shadow Update: a nova versão de um módulo é baixada e preparada em segundo plano enquanto a versão atual continua operando normalmente. A troca é aplicada em um momento de baixo impacto — tipicamente no encerramento do expediente ou no reinício do sistema.

### ***Fluxo de Atualização***

* O orquestrador detecta uma nova imagem disponível no registro (Docker Hub ou registro privado).

* A nova imagem é baixada em segundo plano, camada por camada. Apenas as camadas alteradas são transferidas, minimizando o consumo de banda.

* A nova imagem fica armazenada como inativa no host, aguardando o momento de aplicação.

* Ao encerrar o expediente ou reiniciar o sistema, o orquestrador executa: docker stop \<módulo-v-anterior\> && docker run \<módulo-v-nova\>.

* O downtime total é inferior a 5 segundos, pois a nova imagem já está disponível localmente.

### ***Ferramentas Recomendadas***

Watchtower é a solução mais simples para automação de atualizações de contêineres: monitora registros de imagens, baixa atualizações automaticamente e pode ser configurado para aplicá-las apenas em janelas de manutenção programadas. Para controle mais fino — especialmente em ambientes de produção crítica — o SDK do Jade-stock pode integrar endpoints de gerenciamento do Docker via API, permitindo que atualizações sejam disparadas de forma controlada pela própria interface do sistema.

### ***Imutabilidade de Contêineres***

Um princípio fundamental da contêinerização é que contêineres não são modificados em runtime — eles são substituídos por novas imagens. Isso elimina a categoria de bugs causados por patches manuais aplicados diretamente em servidores de produção, onde o estado do servidor diverge gradualmente do que está documentado ou versionado. Com contêineres imutáveis, o estado de produção é sempre derivável a partir do Dockerfile e do código-fonte.

## **6.4 Escalabilidade Horizontal Futura**

Caso o volume de operações exija distribuição em múltiplos servidores, a arquitetura do Jade-stock já está preparada para essa transição. Os microserviços expostos via API RESTful podem ser posicionados atrás de um load balancer sem alterações de contrato. A Event Store, já centralizada no PostgreSQL, pode ser migrada para uma solução de mensageria como RabbitMQ ou Kafka para suportar maior throughput de eventos sem mudanças nos produtores e consumidores, apenas na camada de infraestrutura.

A adoção de Kubernetes ou Docker Swarm para orquestração em múltiplos nós é uma evolução natural da contêinerização, mas deve ser considerada apenas quando a carga operacional justificar a complexidade adicional de gerenciamento de cluster. Para a maioria dos cenários do Jade-stock em fase inicial, um único servidor bem dimensionado com Docker Compose é suficiente e muito mais simples de operar.

# **7\. Orquestrador como Gestor de Licenças**

O mesmo orquestrador responsável por gerenciar atualizações de contêineres pode assumir uma segunda responsabilidade igualmente estratégica: o controle de licenças do software. Essa abordagem é natural porque o orquestrador já é o ponto de controle de quais imagens sobem, quando e em quais condições — adicionar validação de licença nessa camada elimina a necessidade de um serviço separado e garante que nenhum módulo do Jade-stock opere fora de uma licença ativa.

O modelo é inspirado em soluções como o Adobe Creative Cloud: em vez de chaves de licença locais que podem ser copiadas ou burladas, a licença é validada dinamicamente no momento em que o sistema tenta subir ou renovar seus contêineres. Sem validação bem-sucedida, os módulos simplesmente não iniciam.

## **7.1 Validação de Licença na Inicialização**

Antes de iniciar qualquer contêiner de módulo (WMS, Contábil, IA), o orquestrador consulta o servidor de licenças do Jade-stock via HTTPS, enviando o identificador da instalação e o token de licença associado. O servidor responde com o status da licença: ativa, expirada, suspensa ou revogada.

* Licença ativa: o orquestrador prossegue normalmente com a inicialização ou atualização dos contêineres.

* Licença expirada: o orquestrador notifica o usuário com uma mensagem clara e bloqueia a inicialização de novos contêineres. Contêineres já em execução permanecem ativos até o encerramento natural do expediente.

* Licença revogada: o orquestrador derruba todos os contêineres imediatamente e bloqueia qualquer nova inicialização até regularização.

Esse comportamento garante que o fornecedor do software tenha controle efetivo sobre o uso do sistema, independentemente de onde ele esteja instalado.

## **7.2 Licença Amarrada ao Registro de Imagens**

Uma camada adicional de proteção pode ser implementada no nível do registro privado de imagens Docker. Em vez de imagens publicamente acessíveis, o registro exige autenticação via token de licença para autorizar o comando docker pull. Sem um token válido, o orquestrador não consegue baixar novas imagens — e portanto não consegue instalar nem atualizar nenhum módulo do Jade-stock.

Esse modelo protege também a propriedade intelectual do software: o código empacotado nas imagens nunca é acessível sem uma licença válida, pois o próprio download é bloqueado. Clientes com licença vencida não apenas perdem o acesso funcional, mas também a capacidade de instalar novas cópias a partir das imagens protegidas.

## **7.3 Operação Offline e Grace Period**

Em cenários onde o cliente opera sem acesso à internet por períodos prolongados — como depósitos em áreas remotas ou ambientes com restrições de rede — o orquestrador implementa um grace period configurável. Durante esse período, o sistema opera normalmente mesmo sem conseguir contato com o servidor de licenças, desde que a última validação bem-sucedida esteja dentro do prazo definido.

O grace period padrão recomendado é de 7 dias, renovável a cada validação bem-sucedida. O orquestrador armazena localmente um token assinado criptograficamente com a data da última validação e o prazo de validade offline. Esse token não pode ser forjado sem a chave privada do servidor, garantindo que o período offline não seja explorado para uso fraudulento.

Quando o grace period expira sem que uma validação online tenha sido realizada, o orquestrador exibe um aviso progressivo nos dias que antecedem o bloqueio, permitindo que o operador tome providências antes de uma interrupção inesperada.

## **7.4 Controle Remoto e Revogação**

Uma das vantagens mais significativas desse modelo em relação a licenças tradicionais baseadas em chave local é a capacidade de controle remoto em tempo real. O servidor de licenças do Jade-stock pode, a qualquer momento, alterar o status de uma licença específica — e essa mudança é aplicada na próxima validação do orquestrador, que ocorre no intervalo configurado (padrão: a cada 24 horas e sempre na inicialização do sistema).

Isso viabiliza cenários como: suspensão imediata de uma instalação em caso de inadimplência, migração de licença entre máquinas sem intervenção manual no cliente, e desativação de instalações não autorizadas identificadas por uso anômalo.

## **7.5 Telemetria de Uso**

O orquestrador pode transmitir ao servidor de licenças métricas básicas de uso durante as validações periódicas: número de sessões ativas, módulos em execução e identificador único da instalação. Esses dados permitem ao fornecedor monitorar o uso real do software, identificar instalações duplicadas de uma mesma licença e embasar decisões comerciais como limites por número de instalações simultâneas.

A telemetria deve ser transparente para o cliente: os dados coletados, sua finalidade e o endereço do servidor receptor devem ser documentados no contrato de licença e exibidos na interface do sistema. Isso garante conformidade com legislações de privacidade como a LGPD.

# **8\. Autenticação via OAuth 2.0 e Provedores de Identidade**

Em vez de construir e manter um sistema próprio de cadastro, login e recuperação de senha, o Jade-stock delega a autenticação de usuários a provedores de identidade consolidados via protocolo OAuth 2.0. Essa abordagem — utilizada amplamente pela indústria em produtos como Figma, Notion, Slack e outros — elimina toda uma categoria de responsabilidades sensíveis: armazenamento de senhas, proteção contra vazamentos de credenciais, fluxos de recuperação de acesso e conformidade com requisitos de segurança de autenticação.

O princípio é simples: o provedor de identidade (Google, Microsoft, Apple ou outros) é responsável por provar quem é o usuário. O Jade-stock recebe essa prova, registra o usuário no seu próprio banco de dados e associa a ele uma licença ativa ou não. A separação é clara: o provedor cuida da identidade, o Jade-stock cuida da autorização e do acesso ao produto.

## **8.1 Como Funciona o Fluxo OAuth 2.0**

O fluxo de autenticação com um provedor como o Google ocorre da seguinte forma:

* O usuário clica em 'Entrar com Google' na tela de acesso do Jade-stock.

* O cliente rico abre o navegador do sistema (ou uma webview embutida) redirecionando para a tela de login do Google.

* O usuário confirma sua identidade no Google — que pode já estar logado automaticamente, tornando o processo de um clique.

* O Google redireciona de volta ao Jade-stock com um token de autorização assinado criptograficamente.

* O backend do Jade-stock valida esse token junto à API do Google, extrai o identificador único do usuário (sub) e o e-mail.

* O backend verifica se esse identificador já existe no banco de dados. Se não existir, cria um novo registro de usuário automaticamente. Se existir, atualiza a sessão.

* O backend retorna ao cliente rico um token de sessão próprio do Jade-stock, que será usado nas chamadas subsequentes ao SDK.

Em nenhum momento o Jade-stock toca ou armazena a senha do usuário. O Google apenas confirma a identidade e devolve um identificador verificado. Todo o controle de acesso ao produto — licença, permissões, tenant — é gerenciado exclusivamente pelo Jade-stock a partir daí.

## **8.2 Integração com o Orquestrador de Licenças**

A autenticação via OAuth se integra naturalmente ao orquestrador de licenças descrito na seção anterior. O fluxo combinado funciona da seguinte forma: ao iniciar o sistema, o orquestrador verifica se há uma sessão de usuário válida. Se não houver, o cliente rico apresenta a tela de login com OAuth. Após a autenticação bem-sucedida, o orquestrador consulta o servidor de licenças usando o identificador do usuário autenticado e determina se aquela conta possui uma licença ativa para operar o Jade-stock.

Isso cria um pipeline de acesso com duas etapas independentes: primeiro a prova de identidade (OAuth, responsabilidade do Google), depois a verificação de licença (responsabilidade do Jade-stock). Um usuário pode ter conta Google válida mas licença expirada — e vice-versa não é possível, pois sem identidade verificada não há como consultar a licença.

## **8.3 Provedores Suportados**

O Jade-stock pode suportar múltiplos provedores OAuth simultaneamente sem esforço adicional significativo, pois o protocolo OAuth 2.0 é padronizado. Os provedores mais relevantes para o perfil de usuários do sistema são:

* Google: provedor mais universal, com altíssima taxa de adoção. A maioria dos usuários já possui conta ativa e frequentemente está logada no navegador, tornando o processo de autenticação de um único clique.

* Microsoft: especialmente relevante para clientes corporativos que operam em ambientes Windows com contas Microsoft 365 ou Azure Active Directory já provisionadas.

* Apple: obrigatório caso o Jade-stock seja distribuído via App Store no iOS ou macOS, pois a Apple exige suporte ao 'Sign in with Apple' como condição de publicação.

A recomendação para o estágio inicial é implementar o Google como provedor primário, por ser o de maior cobertura e menor fricção. Os demais provedores podem ser adicionados progressivamente conforme o perfil dos clientes demandar.

## **8.4 O Que o Jade-stock Armazena**

Após a autenticação OAuth, o banco de dados do Jade-stock registra apenas as informações necessárias para operar o sistema, sem duplicar dados que são responsabilidade do provedor:

* Identificador único do provedor (sub): string opaca fornecida pelo Google que identifica o usuário de forma permanente, mesmo que ele troque de e-mail.

* E-mail: utilizado para comunicações transacionais como notificações de licença, faturas e alertas do sistema.

* Nome de exibição: recuperado do perfil do provedor e utilizado na interface do sistema.

* Provedor de origem: indica qual provedor foi utilizado na autenticação (google, microsoft, apple).

* Data do primeiro acesso e do último acesso: para auditoria e monitoramento de uso.

* Vínculo com a licença: referência ao registro de licença associado àquele usuário ou organização.

O fluxo OAuth 2.0 envolve três tipos de token, cada um com ciclo de vida e estratégia de armazenamento distintos:

* Access Token: token de curta duração emitido pelo Google (validade típica de 1 hora) que autoriza chamadas à API do provedor. Não é persistido no banco de dados, pois expira rapidamente e é renovado automaticamente pelo backend sempre que necessário.

* Refresh Token: token de longa duração emitido pelo Google no momento da primeira autenticação. Esse token deve ser armazenado no banco de dados do Jade-stock, criptografado em repouso. É ele que permite ao backend obter novos access tokens sem exigir que o usuário passe pelo fluxo de login novamente. Sem persistir o refresh token, a sessão seria encerrada a cada hora, quebrando completamente a experiência de uso contínuo.

* Token de sessão interno (JWT): gerado pelo próprio backend do Jade-stock após autenticação bem-sucedida. É armazenado localmente no cliente, em área segura do sistema operacional — Keychain no macOS, Credential Manager no Windows. O servidor mantém um registro dos tokens de sessão ativos por usuário, o que permite revogação remota de sessões específicas, como ao encerrar o acesso em todos os dispositivos simultaneamente.

Nenhuma senha é armazenada em nenhum momento. O refresh token, embora persistido, é armazenado criptografado e nunca exposto ao cliente ou ao front-end — ele trafega exclusivamente entre o backend do Jade-stock e a API do Google.

## **8.5 Experiência do Usuário Final**

Do ponto de vista do operador que utiliza o Jade-stock no dia a dia, o fluxo de acesso é o mais simples possível. Na primeira utilização, o sistema exibe a tela de login com o botão 'Entrar com Google'. Como a maioria dos computadores já possui uma sessão Google ativa no navegador — seja pelo Gmail, YouTube ou pelo próprio sistema operacional em dispositivos Android e Chromebook — a confirmação é feita com um único clique, sem digitar nenhuma credencial.

Nas utilizações subsequentes, o cliente rico armazena o token de sessão do Jade-stock localmente de forma segura, e o usuário acessa o sistema diretamente sem precisar passar pelo fluxo OAuth novamente, até que a sessão expire ou o usuário encerre manualmente. Isso replica a experiência fluida que os usuários já conhecem de ferramentas como o Creative Cloud, onde o login é feito uma vez e o acesso persiste entre sessões.

# **9\. Migrations, Pipeline de Deploy e Operação Profissional**

Um princípio fundamental de operação profissional é que o usuário final jamais interage com o banco de dados diretamente, jamais executa comandos de terminal e jamais precisa saber que tabelas existem ou como elas foram criadas. Toda a preparação do ambiente — criação de schemas, aplicação de migrations, validação de integridade — é responsabilidade exclusiva do time técnico e dos scripts automatizados de deploy.

O output de testes apresentado abaixo confirma que o módulo WMS do Jade-stock já opera dentro desse princípio: 91 testes passando, incluindo testes transacionais, de idempotência, de comportamento sob concorrência e de integração completa com PostgreSQL, todos executados e validados na camada técnica sem qualquer intervenção manual do usuário final. O release gate automatizado garante que o sistema só avança para produção quando todas essas validações estão verdes.

## **9.1 Migrations Versionadas com Alembic**

O Jade-stock utiliza Alembic como ferramenta de migrations versionadas para o PostgreSQL. Migrations são arquivos de código que descrevem cada alteração no schema do banco de dados — criação de tabelas, adição de colunas, criação de índices, alteração de constraints — de forma incremental e rastreável via controle de versão.

O princípio de funcionamento é análogo ao do Git para código: cada migration representa um delta entre o estado anterior e o novo estado do banco. O Alembic mantém uma tabela de controle (alembic\_version) no próprio banco que registra qual migration foi aplicada por último. Ao fazer deploy de uma nova versão do Jade-stock, o sistema identifica automaticamente quais migrations ainda não foram aplicadas e as executa em ordem, sem intervenção manual.

Isso resolve um problema crítico de manutenção: sem migrations versionadas, qualquer alteração no schema precisaria ser aplicada manualmente em cada ambiente (desenvolvimento, homologação, produção), criando risco real de divergência entre ambientes e dependência de memória humana para saber o estado atual do banco. Com Alembic, o estado do banco é sempre derivável a partir do histórico de migrations no repositório.

## **9.2 Pipeline de Deploy: Ordem de Operações**

O deploy de uma nova versão do Jade-stock segue uma sequência rigorosa e automatizada, que garante que o banco de dados esteja sempre atualizado antes de qualquer módulo de aplicação ser iniciado ou reiniciado:

* Etapa 1 — Validação de dependências: o script verifica que todas as bibliotecas Python necessárias estão instaladas nas versões corretas, conforme o arquivo de requirements versionado.

* Etapa 2 — Conexão e validação do banco: o sistema testa a conectividade com o PostgreSQL e verifica que o usuário de deploy possui as permissões necessárias nos schemas relevantes.

* Etapa 3 — Aplicação de migrations: o Alembic executa todas as migrations pendentes em ordem cronológica. Se qualquer migration falhar, o deploy é interrompido e o banco permanece no estado anterior, garantindo consistência.

* Etapa 4 — Testes de sanidade pós-migration: um subconjunto dos testes de integração é executado para confirmar que o schema atualizado está operacional antes de subir a API.

* Etapa 5 — Inicialização dos microserviços: somente após todas as etapas anteriores serem concluídas com sucesso, os módulos WMS, Contábil e IA são iniciados ou reiniciados.

Esse pipeline é o que o release\_gate.sh já implementa parcialmente no módulo WMS, conforme evidenciado pelos logs de validação: dependências, conexão e schema, testes transacionais, testes de API e testes de domínio — cinco etapas sequenciais, todas com critério de aprovação ou falha explícito.

## **9.3 Health Check de Startup**

Cada microserviço do Jade-stock implementa um health check de startup: antes de aceitar qualquer requisição da API, o módulo verifica que todas as suas dependências críticas estão operacionais. Para o módulo WMS, isso inclui verificar que o schema wms existe, que as tabelas críticas estão presentes e que a tabela de idempotência está acessível.

Se qualquer verificação falhar, o microserviço recusa inicializar e emite um erro técnico controlado e descritivo — não uma exceção genérica de conexão recusada, mas uma mensagem que identifica exatamente qual dependência está ausente. Isso é fundamental em ambientes de deploy automatizado: o orquestrador de contêineres (ou o systemd, no caso de deploy sem Docker) detecta a falha de startup e pode acionar alertas ou tentativas de recuperação automática sem intervenção humana.

Do ponto de vista do usuário final, o health check é invisível quando tudo funciona corretamente. Quando algo está errado, ele vê uma mensagem clara de que o sistema está temporariamente indisponível, sem exposição de detalhes técnicos do banco de dados ou do ambiente de infraestrutura.

## **9.4 Integração com o Orquestrador de Contêineres**

Quando o Jade-stock opera em ambiente contêinerizado, o pipeline de deploy descrito acima é encapsulado no processo de inicialização do contêiner. O Docker Compose, por exemplo, pode ser configurado para garantir que o contêiner do PostgreSQL esteja healthy antes de inicializar os contêineres de aplicação, e que o contêiner de migrations execute e conclua com sucesso antes que os microserviços de WMS, Contábil ou IA sejam iniciados.

Esse encadeamento transforma o deploy inteiro em uma operação de um único comando — docker compose up — que executa automaticamente, na ordem correta: banco de dados, migrations, testes de sanidade e microserviços. Do ponto de vista operacional, isso nivela a complexidade de um deploy completo à de uma atualização rotineira, sem diferença de procedimento independentemente de quantas migrations ou quantos módulos foram alterados.

## **9.5 Ambientes Separados: Desenvolvimento, Homologação e Produção**

Com migrations versionadas e pipeline automatizado, o Jade-stock pode manter múltiplos ambientes com schema idêntico e comportamento previsível. O ambiente de desenvolvimento é onde novas migrations são criadas e testadas localmente. O ambiente de homologação replica exatamente a configuração de produção e é onde o release gate é executado antes de qualquer deploy em produção. O ambiente de produção recebe apenas código que já passou por todas as validações automáticas.

Para uma equipe enxuta, a separação entre homologação e produção pode inicialmente ser implementada como dois schemas separados no mesmo servidor PostgreSQL — o mesmo padrão de isolamento lógico já adotado para WMS, Contábil e IA. À medida que o sistema crescer, a migração para servidores separados é facilitada precisamente porque o pipeline de deploy já trata os ambientes como entidades independentes, sem hardcode de configurações específicas de ambiente no código.

# **10\. Conclusão**

O Jade-stock implementa uma arquitetura híbrida moderna que foi desenhada com um objetivo claro: entregar um sistema robusto, extensível e tolerante a falhas sem impor uma carga operacional incompatível com uma equipe de desenvolvimento enxuta.

Os pilares arquiteturais que sustentam esse objetivo são:

* Monolito Modular: organização interna clara, manutenção simplificada e padrões consistentes entre domínios.

* Microserviços Locais via API RESTful: isolamento de falhas e independência de ciclo de vida entre WMS, Contábil e IA.

* SDK Centralizado: abstração total da complexidade de integração para o front-end, com versionamento semântico para evolução segura.

* Event Store com Retry e Dead-Letter Queue: consistência eventual, resiliência contra falhas transitórias e rastreabilidade completa de operações.

* Cliente Rico Flutter/Flet: experiência de usuário polida, integração com hardware e multiplataforma a partir de uma única base de código.

* Persistência Unificada com Isolamento Lógico via Schemas PostgreSQL: operação simplificada sem abrir mão da separação de domínios.

* Contêinerização Progressiva: caminho claro de evolução para ambientes múltiplos e escalabilidade horizontal, sem complexidade prematura.

* Orquestrador como Gestor de Licenças: controle remoto efetivo sobre uso, revogação, grace period offline e telemetria, sem depender de chaves locais.

* Autenticação via OAuth 2.0: identidade delegada a provedores como Google e Microsoft, eliminando o gerenciamento de senhas e entregando ao usuário final uma experiência de acesso de um clique.

* Pipeline de Deploy Profissional com Migrations Versionadas: banco de dados sempre atualizado automaticamente antes da API subir, com health check de startup, release gate e separação rigorosa de ambientes — o usuário final jamais interage com infraestrutura.

Cada decisão arquitetural foi tomada com dois critérios simultâneos em mente: resolver o problema técnico presente e preservar a capacidade de crescer no futuro sem reescritas. O resultado é um sistema que pode ser operado e evoluído por uma equipe pequena sem comprometer a qualidade, a confiabilidade ou a experiência do usuário final.

*Jade-stock — Documentação Técnica v1.0 — 2026*

Plano de Execução Consolidado (Jade-stock)

Fase A — WMS Produção (base estável)
Alembic migrations reais
Seed inicial controlado
Startup check de schema/tabelas críticas
Runbook de deploy único
Done: sobe em servidor limpo com 1 comando e passa release_gate.sh
Fase B — Operação e Observabilidade
Logs estruturados por correlation_id
Métricas mínimas: latência, erro, eventos pendentes
Alertas mínimos operacionais
Done: saúde do sistema visível sem abrir código
Fase C — Módulo IA/Estatística (ultra processamento)
Entrada: event_store + histórico WMS (vendas/estoque)
Processamento estatístico: sazonalidade, tendência, variância, outliers, lead time efetivo
Rede neural: previsão de demanda por SKU/local/período
Saída versionada: previsao_demanda, reposicao_sugerida, risco_ruptura
Regra de segurança: IA não grava saldo e não executa movimento (só recomenda)
Aplicação operacional: WMS decide/aprova e só depois executa
Auditoria: todo output com model_version, feature_window, correlation_id
Done: pipeline IA executável e auditável gerando recomendações consumíveis pelo WMS
Fase D — Contábil via eventos (MVP)
Consumidor contábil dos eventos do WMS
Lançamentos contábeis básicos auditáveis
Retry + DLQ simples em banco para falhas de processamento
Done: evento de estoque gera reflexo contábil rastreável ponta a ponta
Fase E — IAM e Comercial
OAuth (Google primeiro)
Sessão interna + vínculo com tenant/licença
Licenciamento progressivo (iniciar simples, sem bloqueio agressivo)
Done: login social + controle de acesso por cliente/tenant
Ordem final oficial: A -> B -> C -> D -> E.