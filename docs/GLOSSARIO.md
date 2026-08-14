# Glossário – GDF_V2

Termos usados na documentação e no sistema GDF_V2.

---

## A

**Acesso subsolução (grupo)**  
Registro que define quais **subsoluções** um **grupo** (Django) pode acessar. Controla o menu e as telas disponíveis para os usuários daquele grupo. Modelo: `AcessoSubsolucaoGrupo`.

**Acesso solução (cliente)**  
Registro que define quais **soluções** um **cliente GDF** tem contratado/habilitado. Modelo: `AcessoSolucaoCliente`.

---

## C

**Carga SPED**  
Processo de leitura de arquivos .txt do SPED (EFD ICMS/IPI ou EFD Contribuições) e gravação dos dados nos schemas `sped_fiscal` e `sped_contribuicao` do banco. Pode ser manual (upload na tela) ou via parâmetros agendados.

**Carga XML**  
Processo de leitura de arquivos XML de NFe, CTe ou NFSe e gravação nos schemas `nfe`, `cte` e `nfse`. Inclui extração de dados (emitente, destinatário, produtos, impostos, totais, pagamento, etc.). Pode ser manual (upload) ou agendada (Celery/script usando `ParametroCargaXml`).

**Certificado digital**  
Arquivo .pfx (PKCS#12) usado para assinatura de documentos fiscais. Cadastrado por raiz de CNPJ no modelo `CertificadoDigital`; associado à empresa. O sistema pode exibir status de validade (verde, amarelo, vermelho).

**Cliente 1000**  
Cliente GDF com código 1000, considerado “dona do projeto”. Usuários vinculados a empresas desse cliente (ou superusuários) podem trocar de cliente na sessão e ter acesso total ao painel (listar e gerenciar todos os clientes).

**Cliente GDF**  
Entidade de negócio identificada por `cod_cliente`. Agrupa empresas e usuários (via vínculo usuário–empresa). O multi-tenancy do sistema é baseado no cliente: a sessão guarda um `cod_cliente` ativo e os dados exibidos são filtrados por esse cliente.

**Condição de pagamento (lote)**  
Registro que associa uma NFe (chave) a uma condição de pagamento informada na NFe e à condição correspondente no SAP, para envio via RFC. Modelo: `CondicaoPagamentoLote` (schema reprocessamento). Status típicos: Pendente, Enviado ao SAP, Processado no SAP.

**Condição parâmetro**  
Mapeamento, por cliente GDF, entre a descrição/código da condição de pagamento na NFe e a condição no SAP (e tipo de pagamento). Usado ao gerar as condições de pagamento do lote e ao enviar ao SAP. Modelo: `CondicaoParam` (schema reprocessamento).

**Confronto (reprocessamento)**  
Comparação entre os registros do SPED e as NFe gravadas no banco para uma dada empresa e competência. Gera **lote** e **divergências**.

**CTe**  
Conhecimento de Transporte eletrônico (modelos 57 e 67). Documento fiscal de transporte; carga via XML no schema `cte`.

**Conexão SAP**  
Configuração de acesso ao SAP (host, sistema, cliente, usuário, senha) por cliente GDF. Modelo: `ConexaoSap` (schema public). Usada pela classe SapRfc para chamadas RFC (ex.: envio de condições de pagamento).

---

## D

**Divergência**  
Inconsistência encontrada no confronto SPED x NFe: por exemplo NFe ausente no SPED, registro SPED sem NFe, valor ou CFOP diferente, data de emissão diferente, cancelamento. Modelo: `Divergencia` (schema reprocessamento). Pode ter status: Aberta, Em reprocessamento, Resolvida, Ignorada.

**Dashboard**  
Telas de relatórios visuais (vendas/compras) servidas por aplicação Streamlit em iframe. O acesso é autenticado via JWT gerado pelo backend (ClGdf.gerar_token).

---

## E

**Empresa**  
Estabelecimento (CNPJ) cadastrado no sistema; pertence a um **cliente GDF**. Recebe carga de XML, SPED e é unidade de filtro em relatórios e reprocessamento. Modelo: `Empresa` (schema public). Pode ter certificado digital e grupo de empresa.

**EFD ICMS/IPI**  
Escrituração Fiscal Digital – ICMS/IPI. Um dos tipos de SPED (arquivo .txt). Carga grava no schema `sped_fiscal`.

**EFD Contribuições**  
Escrituração Fiscal Digital – Contribuições. Outro tipo de SPED; carga grava no schema `sped_contribuicao`.

---

## G

**GDF**  
Nome do projeto/sistema: ERP multi-tenant para gestão de documentos fiscais (NFe, CTe, NFSe, SPED) e integração SAP. Sigla pode ser lida como Gestão Documentos Fiscais ou equivalente.

**Grupo (Django)**  
Grupo de permissões do Django (`auth.Group`). No GDF, o grupo do usuário define as **subsoluções** a que ele tem acesso (via `AcessoSubsolucaoGrupo`).

**Grupo de empresa**  
Agrupamento lógico de empresas (ex.: matriz e filiais) dentro de um cliente GDF. Usado em filtros de relatório e cadastro. Modelo: `GrupoEmpresa`.

---

## I

**IDOR (Insecure Direct Object Reference)**  
Risco de segurança em que o usuário tenta acessar recurso de outro cliente (ex.: empresa ou usuário). O sistema usa decorators `validate_idor_empresa` e `validate_idor_usuario` para garantir que o recurso pertence ao `cod_cliente` da sessão.

**Integração SAP**  
Conexão com o sistema SAP via RFC (PyRFC): teste de conexão e envio de condições de pagamento por lote. Configurada por cliente (ConexaoSap).

---

## J

**Job (carga XML/SPED)**  
Tarefa de processamento de uma execução de carga (manual ou agendada). Modelos: `JobCargaXml`, `JobCargaSped`. Status: Pendente, Executando, Sucesso, Erro. Armazena totais (arquivos, sucesso, erro) e mensagem de log.

**JWT (JSON Web Token)**  
Token usado para autenticar o usuário nos dashboards Streamlit (iframe), sem novo login. Gerado pelo backend (ClGdf.gerar_token) com tempo de expiração limitado.

---

## L

**Lote (reprocessamento)**  
Uma execução de confronto SPED x NFe para uma empresa (ou escopo) e competência. Modelo: `ReprocessamentoLote`. Contém totais (NFe esperado/encontrado, divergências), status (Pendente, Em confronto, Concluído, Erro, Cancelado) e referência ao arquivo SPED quando aplicável.

---

## M

**Multi-tenant**  
Arquitetura em que um único sistema atende vários “inquilinos” (clientes). No GDF, o inquilino é o **cliente GDF**; empresas e usuários pertencem a um cliente e a sessão filtra todos os dados pelo cliente ativo.

**Manifesto**  
Funcionalidade de painel para consulta e gestão de manifestos de NFe, CTe e NFSe (subsolução Mnf_Painel).

---

## N

**NFe**  
Nota Fiscal eletrônica (modelo 55). Carga via XML no schema `nfe`; consulta no Relatório e uso no Reprocessamento (confronto com SPED).

**NFSe**  
Nota Fiscal de Serviços eletrônica. Carga via XML no schema `nfse`; vários layouts (ex.: modelo 13, prefeituras). Consulta no Relatório.

---

## P

**Parâmetro carga XML**  
Configuração de carga automática de XML: diretório, horário, empresa, cliente e origem (LOCAL, SAP, SPED, OUTROS). Modelo: `ParametroCargaXml`. O Celery Beat processa esse diretório no horário definido.

**Parâmetro carga SPED**  
Configuração análoga para carga automática de SPED. Modelo: `ParametroCargaSped`.

**Permissão grupo–cliente**  
Vínculo entre um grupo Django e um cliente GDF: define que aquele grupo tem acesso àquele cliente. Modelo: `PermissaoGrupoCliente`.

---

## R

**Relatório fiscal**  
Consulta a documentos gravados: NFe, CTe, NFSe e SPED, com filtros por empresa (ou grupo) e período. Listagem e detalhe por documento.

**Reprocessamento**  
Módulo que confronta dados do SPED com as NFe, gera divergências e condições de pagamento para envio ao SAP. Inclui lotes, divergências, parâmetros de condição NFe→SAP e envio RFC.

**RFC (SAP)**  
Remote Function Call. Interface do SAP para chamada de funções remotas. O GDF usa PyRFC para conectar e enviar condições de pagamento (e eventualmente outras funções).

---

## S

**SAP**  
Sistema ERP; no GDF há integração via RFC para teste de conexão e envio de condições de pagamento por lote.

**Schema**  
No PostgreSQL, namespace de tabelas. O GDF usa: `public` (cadastros), `nfe`, `cte`, `nfse`, `sped_fiscal`, `sped_contribuicao`, `reprocessamento`. Cada model que não é do public referencia `db_table = '"schema"."tabela"'`.

**Solução**  
Conjunto amplo de funcionalidades (ex.: Cadastros, Processamento, Relatórios). Cadastrada em `Solucao`; cada cliente tem acesso a um subconjunto via `AcessoSolucaoCliente`.

**SPED**  
Sistema Público de Escrituração Digital. Inclui EFD ICMS/IPI, EFD Contribuições, ECD, etc. No GDF a carga é feita a partir de arquivos .txt; os dados são gravados nos schemas sped_fiscal e sped_contribuicao.

**Subsolução**  
Módulo granular de permissão (ex.: Dm_Usuarios, Pro_CargaXml, Pro_Relatorio, Reproc_Painel, Mnf_Painel, Db_Vendas, Db_Compras). O menu e as telas são liberados conforme as subsoluções do grupo do usuário. Cadastrada em `Subsolucao`; acesso por grupo em `AcessoSubsolucaoGrupo`.

---

## U

**Usuário**  
Login do sistema (Django auth.User). Vinculado a uma ou mais **empresas** (UsuarioEmpresa) e a um **grupo** (Group). O grupo define as subsoluções; o primeiro cliente das empresas do usuário (ou 1000) costuma ser o cliente inicial da sessão.

**Usuário–Empresa**  
Vínculo entre usuário e empresa: define a quais empresas o usuário tem acesso. Modelo: `UsuarioEmpresa` (schema public).

---

## X

**XML (NFe/CTe/NFSe)**  
Arquivo XML do documento fiscal. O GDF lê esse XML, extrai os dados e persiste nos models dos schemas nfe, cte e nfse. Aceita também ZIP contendo vários XMLs.

---

*Última atualização: Março 2026*
