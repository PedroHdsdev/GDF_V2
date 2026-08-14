# Manual do usuário – GDF_V2

Manual de uso das telas e fluxos principais do sistema GDF_V2: acesso, cadastros, carga de documentos, relatórios, reprocessamento e dashboards.

---

## 1. Acesso ao sistema

### 1.1 URL e login

- **URL de acesso:** conforme ambiente (ex.: `https://seu-dominio/` ou `https://seu-dominio/Login/`).
- **Tela de login:** informe **usuário** (username) e **senha**. O sistema valida as credenciais e, em caso de sucesso, define automaticamente o **cliente GDF** da sua sessão (geralmente o primeiro cliente ao qual suas empresas estão vinculadas).
- **Após o login:** você é redirecionado para a **Home**. O menu exibido depende das **subsoluções** do seu grupo (permissões). Usuários do **cliente 1000** (dona do projeto) ou **superusuários** podem trocar de cliente pelo painel e ver todos os clientes.

### 1.2 Troca de cliente (quando permitido)

Se você tiver permissão (cliente 1000 ou superuser), na Home haverá opção de **trocar de cliente**. Ao trocar, o sistema passa a exibir dados (empresas, usuários, cargas, relatórios) apenas do cliente selecionado. A troca é feita via API de sessão (`api/sessao/cliente/`).

### 1.3 Logout

Use o link/botão **Sair** (Logout) para encerrar a sessão com segurança.

---

## 2. Menu e subsoluções

O menu (lateral ou superior) é montado dinamicamente conforme as **subsoluções** do seu grupo. Abaixo, o que cada item representa e o que você pode fazer em cada tela.

| Item de menu | Código (subsolução) | O que você pode fazer |
|--------------|---------------------|------------------------|
| **Usuários** | Dm_Usuarios | Listar usuários do cliente, incluir novo usuário, editar usuário (dados, empresas e grupos). O grupo define quais subsoluções o usuário acessa. |
| **Empresas** | Dm_Empresas | Listar empresas, incluir empresa, editar empresa, criar grupo de empresa, atualizar certificado digital (.pfx) da empresa. |
| **Clientes** | Dm_Clientes | Listar clientes GDF, incluir cliente, editar cliente, configurar acessos (soluções) e grupos do cliente, configurar conexão SAP (tela cliente/sap). Visível em geral apenas para quem tem acesso ao cliente 1000 ou admin. |
| **Carga XML** | Pro_CargaXml | Enviar arquivos XML (ou ZIP com XMLs) de NFe, CTe ou NFSe; configurar parâmetros de carga agendada; acompanhar jobs e avisos; ver relatório de carga. |
| **Carga SPED** | Pro_CargaSped | Enviar arquivos .txt do SPED (EFD ICMS/IPI ou EFD Contribuições); configurar parâmetros; acompanhar jobs e avisos. |
| **Relatório** | Pro_Relatorio | Consultar NFe, CTe, NFSe e SPED por empresa (ou grupo), data inicial e final; ver listagem e abrir detalhe de cada documento. |
| **Reprocessamento** | Reproc_Painel | Ver lotes de confronto SPED x NFe; disparar novo confronto; analisar divergências; gerar condições de pagamento e enviar ao SAP. |
| **Manifesto** | Mnf_Painel | Painel de manifesto (consulta e gestão de manifestos de NFe, CTe, NFSe). |
| **Dashboard Vendas / Compras** | Db_Vendas / Db_Compras | Acesso aos dashboards em iframe (Streamlit), com autenticação via JWT. |

---

## 3. Cadastros

### 3.1 Usuários (Dm_Usuarios)

- **Listagem:** exibe os usuários do **cliente atual**. É possível filtrar por nome ou empresa.
- **Incluir usuário:** abra o modal de inclusão (ex.: “Novo usuário”). Preencha:
  - Nome, e-mail, usuário (username) e senha.
  - Empresas às quais o usuário terá acesso (vinculação usuário–empresa).
  - Grupo do usuário (o grupo define as subsoluções que ele verá no menu).
- **Editar usuário:** na listagem, use a ação de editar. Você pode alterar dados, empresas e grupo. O campo **senha** só é alterado se for preenchido; deixar em branco mantém a senha atual.
- **Importante:** um usuário só “enxerga” o cliente das empresas às quais está vinculado; o primeiro cliente encontrado costuma ser o da sessão inicial após o login.

### 3.2 Empresas (Dm_Empresas)

- **Listagem:** exibe as empresas do cliente atual.
- **Incluir empresa:** preencha código da empresa, CNPJ, razão social, nome fantasia e, se houver, grupo de empresa. Outros campos (IE, IM, tipo, matriz, CRT, CNAE, etc.) podem ser opcionais conforme a tela.
- **Editar empresa:** altere código, CNPJ, razão, fantasia, grupo e demais dados permitidos.
- **Grupo de empresa:** use a opção de inserir grupo de empresa para criar agrupamentos (ex.: matriz e filiais). Depois associe as empresas ao grupo nos cadastros.
- **Certificado digital:** em “Atualizar certificado” (ou equivalente), faça o upload do arquivo **.pfx** e informe a **senha** do certificado. O sistema valida e armazena de forma segura. O certificado é usado para assinatura de documentos; o status (ex.: válido, próximo do vencimento, vencido) pode ser exibido na tela de empresas.

### 3.3 Clientes GDF (Dm_Clientes)

- **Listagem:** geralmente visível apenas para usuários do cliente 1000 ou administradores. Mostra todos os clientes GDF cadastrados.
- **Incluir cliente:** informe código do cliente, razão social, CNPJ e ativo. Após salvar, configure acessos (soluções) e grupos.
- **Editar cliente:** altere dados cadastrais; em “Acesso” defina quais soluções o cliente tem; em “Grupos” gerencie os grupos do cliente.
- **Conexão SAP:** em “SAP” (ou “cliente/<cod_cliente>/sap/”) informe host, sistema, cliente SAP, usuário e senha para integração RFC. É possível testar a conexão pela API “Testar conexão SAP” (usada pela tela de configuração).

---

## 4. Carga de XML (Pro_CargaXml)

### 4.1 Carga manual (upload)

1. Acesse o menu **Carga XML**.
2. Selecione a **empresa** para a qual os XMLs serão associados (obrigatório para identificar o emitente).
3. Selecione o **tipo** de documento: NFe, CTe ou NFSe.
4. Envie um ou mais arquivos **XML** ou um **ZIP** contendo XMLs. O sistema aceita múltiplos arquivos em uma única submissão.
5. Após enviar, o sistema cria um **job** e processa em background. Na própria tela (ou na listagem de jobs) acompanhe o status: **Executando**, **Sucesso** ou **Erro**.
6. Em caso de sucesso, os documentos passam a aparecer no **Relatório** (NFe, CTe ou NFSe, conforme o tipo). Em caso de erro, a mensagem do job indica quais arquivos falharam e o motivo (ex.: empresa não cadastrada, XML inválido).

### 4.2 Parâmetros de carga agendada

- É possível configurar **parâmetros** de carga automática: diretório no servidor, horário de execução (ex.: 08:00), empresa e tipo de origem (LOCAL, SAP, SPED, OUTROS).
- O Celery Beat verifica periodicamente os parâmetros ativos e, no horário configurado, processa os XMLs do diretório (extrai ZIPs, detecta NFe/CTe/NFSe e grava no banco). Arquivos processados podem ser movidos para subpastas “processados” ou “pendentes”.
- Na tela de Carga XML você pode listar parâmetros, ativar/desativar (toggle), ver detalhes e, quando houver opção, enviar ZIP para um parâmetro específico.

### 4.3 Jobs e avisos

- **Jobs:** listagem de todas as execuções (manuais e agendadas) com status, totais (sucesso/erro) e mensagem. Ao clicar em um job, é exibido o detalhe (arquivos processados e erros).
- **Avisos:** mensagens do sistema sobre problemas (ex.: certificado próximo do vencimento, erros recorrentes em parâmetros).
- **Resumo:** quantidade de jobs por status ou por período, conforme implementado na tela.

---

## 5. Carga SPED (Pro_CargaSped)

1. Acesse o menu **Carga SPED**.
2. Selecione a **empresa** e o **tipo** de SPED (EFD ICMS/IPI ou EFD Contribuições, conforme disponível).
3. Envie o arquivo **.txt** do SPED.
4. O sistema cria um **job** e processa em background. Acompanhe o status na listagem de jobs.
5. Após conclusão com sucesso, os dados ficam disponíveis no **Relatório** (consulta SPED) e no **Reprocessamento** (confronto com NFe).

---

## 6. Relatório fiscal (Pro_Relatorio)

1. Acesse o menu **Relatório**.
2. Defina os **filtros**:
   - **Empresa** (ou grupo de empresas), quando aplicável.
   - **Data inicial** e **data final** (período de emissão ou de referência).
   - **Tipo de documento:** NFe, CTe, NFSe ou SPED.
3. A listagem exibe os documentos encontrados (chave, número, série, data, valor, etc.). A quantidade de colunas e o formato dependem do tipo (NFe, CTe, NFSe, SPED).
4. **Detalhe:** ao clicar em um item, o sistema abre o detalhe completo do documento (emitente, destinatário, produtos, impostos, totais, pagamento, etc.), conforme os dados gravados no banco.

---

## 7. Reprocessamento (Reproc_Painel)

O reprocessamento serve para **confrontar** os dados do **SPED** com as **NFe** gravadas e gerar **condições de pagamento** para envio ao **SAP**.

### 7.1 Fluxo resumido

1. **Selecionar empresa e período (competência):** defina para qual empresa (ou escopo: uma, várias, todas) e qual competência (mês) deseja rodar o confronto.
2. **Disparar o confronto:** o sistema gera um **lote** e compara registros do SPED com as NFe. O resultado são **divergências** (NFe ausente no SPED, registro SPED sem NFe, valor ou CFOP diferente, etc.).
3. **Revisar divergências:** na tela do lote, liste as divergências; abra o **detalhe** de cada uma para analisar e, se aplicável, use **Reprocessar** para tentar corrigir ou reclassificar.
4. **Gerar condições de pagamento:** a partir do lote, gere a lista de **condições de pagamento** (mapeamento entre condição informada na NFe e condição no SAP). O sistema usa a tabela de parâmetros **condição NFe → SAP** por cliente (CondicaoParam).
5. **Enviar ao SAP:** se a conexão SAP estiver configurada para o cliente, use “Enviar ao SAP”. O sistema envia as condições via RFC e pode atualizar o status (pendente, enviado, processado). Opcionalmente existe fluxo para **atualizar retorno** (sincronizar status com o SAP).

### 7.2 Tipos de divergência

- **NF-e ausente no SPED:** a NFe existe no banco mas não foi encontrada no SPED.
- **Registro SPED sem NF-e:** o SPED referencia uma NFe que não está no banco.
- **Valor divergente / CFOP divergente / Data de emissão divergente:** confronto numérico ou de dados entre SPED e NFe.
- **Cancelamento/denegação:** situação de cancelamento ou denúncia.
- **Outra inconsistência:** agrupamento para demais casos.

### 7.3 Condições de pagamento e parâmetros

- As **condições de pagamento** por lote relacionam chave da NFe, condição informada na NFe e condição no SAP (mapeada via parâmetros do cliente).
- Em **Condição parâmetro** (ou equivalente na tela de cliente/reprocessamento), cadastre o mapeamento: **condição NFe** → **condição SAP** e **tipo de pagamento**. Assim, ao gerar as condições do lote, o sistema já preenche o valor SAP correto para envio.

---

## 8. Manifesto e Dashboards

- **Manifesto (Mnf_Painel):** painel para consulta e gestão de manifestos (NFe, CTe, NFSe). Use os filtros e ações disponíveis na tela (consulta, modais de item e manifesto).
- **Dashboards (Db_Vendas / Db_Compras):** abrem as telas de vendas e compras em **iframe**, com autenticação JWT. O token é gerado pelo backend (ClGdf.gerar_token) e passado para o Streamlit; assim o usuário não precisa fazer login novamente no dashboard.

---

## 9. Dicas e troubleshooting

- **“Cliente não identificado” ou “Sessão inválida”:** faça login novamente. Se o problema persistir, verifique se seu usuário está vinculado a pelo menos uma empresa do cliente desejado.
- **“Empresa não pertence ao seu cliente”:** você está tentando acessar uma empresa de outro cliente. Troque de cliente (se tiver permissão) ou use uma empresa do seu cliente.
- **Carga XML com “empresa não cadastrada”:** o CNPJ do emitente do XML não está cadastrado como empresa do cliente. Cadastre a empresa com o mesmo CNPJ (raiz ou completo, conforme a regra do sistema) e reprocesse.
- **Job em “Executando” por muito tempo:** pode haver muitos arquivos ou arquivos muito grandes. Consulte o detalhe do job; se estiver em erro, a mensagem indicará o motivo.
- **Relatório vazio:** confira filtros (empresa, grupo, período) e se já existe carga de XML/SPED para esse período e empresa.
- **Reprocessamento sem divergências:** verifique se há SPED e NFe carregados para a mesma empresa e competência; o confronto só gera divergências onde houver diferença ou ausência.
- **SAP “conexão falhou”:** verifique em Clientes → SAP se host, sistema, cliente, usuário e senha estão corretos e se o servidor SAP está acessível da rede onde o GDF roda.

---

## 10. Referências

- **Termos do sistema:** [GLOSSARIO.md](GLOSSARIO.md).
- **Detalhes técnicos e arquitetura:** [DOCUMENTACAO_PROJETO_GDF.md](DOCUMENTACAO_PROJETO_GDF.md) e [ARQUITETURA.md](ARQUITETURA.md).

---

*Última atualização: Março 2026*
