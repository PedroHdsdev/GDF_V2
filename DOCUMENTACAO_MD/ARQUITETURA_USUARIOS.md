# Arquitetura de usuários e controle por cliente/empresa

## Campos do usuário (Django `User`)

Os campos `is_superuser`, `is_staff` e `is_active` pertencem ao modelo de usuário e foram adaptados ao projeto da seguinte forma:

| Campo | Uso no projeto |
|-------|-----------------|
| **is_superuser** | Acesso total: pode fazer login sem estar vinculado a empresas; vê todas as soluções; pode **escolher o cliente ativo** na Home e gerenciar usuários, grupos (PermissaoGrupoCliente, GrupoEmpresa) e empresas para **qualquer cliente**. |
| **is_staff** | Acesso ao Django Admin (`/admin/`). Pode ser usado no futuro para perfis “staff” com permissões intermediárias. |
| **is_active** | Usuário ativo pode fazer login; inativo não consegue autenticar. |

## Fluxo por tipo de usuário

### Usuário normal (não superuser)
- Vinculado a **empresas** via `UsuarioEmpresa` e a **grupos** (Django `Group`) via `PermissaoGrupoCliente` (grupos por cliente).
- No login, o **cliente** é definido a partir das empresas do usuário (primeiro cliente encontrado).
- Só enxerga dados do cliente da sessão (`cod_cliente`).
- Criação/edição de usuários só no contexto do cliente ao qual tem acesso.

### Superuser
- Pode fazer login mesmo sem ter empresas vinculadas.
- Na **Home**, pode **trocar o cliente ativo** com o seletor “Cliente ativo (contexto)”.
- Com um cliente selecionado, pode:
  - Criar e editar **usuários** vinculados a empresas e grupos daquele cliente
  - Gerenciar **grupos de cliente** (`PermissaoGrupoCliente`) e **grupos de empresa** (`GrupoEmpresa`)
  - Gerenciar **empresas** e **clientes**
- Acesso à lista de **clientes** mesmo sem cliente selecionado (para cadastrar o primeiro ou trocar contexto).

## Modelos relacionados

- **ClienteGdf** – Cliente (contratante). Tabela: `cliente_gdf`.
- **Empresa** – Empresas do cliente; podem pertencer a um **GrupoEmpresa** (grupo de empresas). Tabela: `empresa`.
- **UsuarioEmpresa** – Vínculo User ↔ Empresa (quais empresas o usuário acessa). Tabela: `usuario_empresa`.
- **PermissaoGrupoCliente** – Vínculo Django `Group` ↔ ClienteGdf (grupos de permissão por cliente). Tabela: `permissao_grupo_cliente`.
- **GrupoEmpresa** – Agrupamento de empresas dentro de um cliente. Tabela: `grupo_empresa`.

## Sessão

- `cod_cliente`: cliente em que o usuário está atuando (obrigatório para listar usuários/empresas; superuser define na Home).
- `is_superuser` / `is_staff`: gravados no login para uso nas views.
- `t_solucoes`: soluções/subsoluções disponíveis no menu (superuser vê todas).

## Campo Cliente nos cadastros (superuser)

Nos formulários de **cadastro** (empresa, grupo de empresas, usuário), o **superuser** vê um campo **Cliente** no topo do modal, permitindo informar para qual cliente o registro será criado:

- **Cadastrar empresa**: select “* Cliente” (obrigatório); ao trocar o cliente, a lista de “Grupo de Empresas” é recarregada para aquele cliente.
- **Criar grupo de empresas**: select “* Cliente” (obrigatório).
- **Cadastrar usuário**: select “* Cliente” (obrigatório); ao trocar o cliente, as listas de empresas e grupos são recarregadas.

O usuário normal não vê esse campo; o cliente é sempre o da sessão.

- **GET** `/empresa/inserir/?cod_cliente=XXX` e **GET** `/usuario/inserir/?cod_cliente=XXX`: quando `is_superuser`, o parâmetro opcional `cod_cliente` define de qual cliente vêm grupos/empresas na resposta.
- **POST** dos formulários pode enviar `m_cod_cliente`; se for superuser, esse valor é usado como cliente do novo registro.

## API de troca de cliente (superuser)

- **POST** `/api/sessao/cliente/`  
  Corpo JSON: `{"cod_cliente": "CODIGO"}`  
  Define o cliente ativo na sessão. Só aceito para usuário com `is_superuser`.
