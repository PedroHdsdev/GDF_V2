# Análise Completa do Sistema de Usuários - GDF_V2

## 1. VISÃO GERAL DA ARQUITETURA

O sistema de gerenciamento de usuários no GDF_V2 é composto por 3 camadas principais:

### 1.1 **Camada de Negócio** (`app/classes/Gdf.py`)
- **Classe Principal**: `Cl_Gdf()`
- **Responsabilidade**: Todas as operações de banco de dados
- **Métodos Críticos para Usuários**:
  - `get_usuarios(cod_cliente)` - Retorna lista de usuários do cliente
  - `get_usuario_ins(cod_cliente)` - Retorna dados para modal de INSERT
  - `get_usuario_upd(user_id, cod_cliente)` - Retorna dados para modal de UPDATE
  - `ins_usuario(...)` - Cria novo usuário com empresas e grupos
  - `upd_usuario(...)` - Atualiza usuário com empresas e grupos

### 1.2 **Camada de Apresentação** (Views)
- **Views Principais** em `app/views.py`:
  - `Dm_Usuarios_view()` - Renderiza a página com tabela de usuários (GET)
  - `Usuario_ins()` - Recebe dados do modal INSERT e cria usuário (POST)
  - `Usuario_upd(user_id)` - Fornece dados para edição (GET) e atualiza (POST)

### 1.3 **Camada de Interface** (Templates + JavaScript)
- **Templates**:
  - `Usuarios.html` - Página principal com tabela
  - `Usuarios_ins.html` - Modal para criar novo usuário
  - `Usuarios_upd.html` - Modal para editar usuário existente
- **JavaScript** (`Script_Usuarios.js`):
  - Paginação e busca (client-side)
  - Gerenciamento de modal INSERT
  - Gerenciamento de modal UPDATE
  - AJAX para carregamento de dados de edição

---

## 2. FLUXO DE DADOS - INSERT (Novo Usuário)

### Sequência de operações:

```
1. Usuário clica "Cadastrar" → Modal INSERT abre
   ↓
2. Cliente solicita GET /usuario_ins/
   ↓
3. Views.Usuario_ins() (GET) chama:
   - cl_gdf.get_usuario_ins(cod_cliente)
   ↓
4. Gdf.get_usuario_ins() retorna:
   {
       "Todas_Empresas": [
           {"cod_empresa": "E001", "fantasia": "Empresa 1", "razao": "Razão Social 1"},
           ...
       ],
       "Todos_Grupos": [
           {"id": 1, "name": "Gerente"},
           ...
       ]
   }
   ↓
5. JavaScript preenche os <select> com dados recebidos
   ↓
6. Usuário seleciona empresas e grupos (via botão "Adicionar")
   ↓
7. JavaScript adiciona itens aos arrays:
   - usuariosState.empresasSelecionadas
   - usuariosState.gruposSelecionados
   ↓
8. Usuário clica "Salvar" → Form faz POST
   ↓
9. Views.Usuario_ins() (POST) recebe:
   - username, email, password, first_name, last_name
   - ls_empresas (string de IDs separados por vírgula)
   - ls_grupos (string de IDs separados por vírgula)
   ↓
10. Chama cl_gdf.ins_usuario(...) que:
    - Cria usuário no User
    - Cria registros UserEmpresas
    - Adiciona usuário aos grupos
    ↓
11. Retorna para Dm_Usuarios_view() com tabela atualizada
```

---

## 3. FLUXO DE DADOS - UPDATE (Editar Usuário)

### Sequência de operações:

```
1. Usuário clica em uma linha da tabela → Modal UPDATE abre
   ↓
2. JavaScript faz AJAX GET /usuario/{user_id}/
   ↓
3. Views.Usuario_upd() (GET) chama:
   - cl_gdf.get_usuario_upd(user_id, cod_cliente)
   - Retorna (user_data, empresas_disponiveis, grupos_disponiveis)
   ↓
4. Gdf.get_usuario_upd() retorna:
   {
       "id": 1,
       "username": "joão",
       "email": "joao@email.com",
       "first_name": "João",
       "last_name": "Silva",
       "is_active": true,
       "empresas": [
           {"cod_empresa": "E001", "fantasia": "Empresa 1", "razao": "Razão Social 1"}
       ],
       "grupos": [
           {"id": 1, "name": "Gerente"}
       ],
       // ❌ PROBLEMA: Não retorna empresas_disponiveis e grupos_disponiveis
   }
   ↓
5. JavaScript preenche formulário com dados do usuário
   ↓
6. JavaScript deveria preencher <select> com itens disponíveis:
   - select#upd_empresas_select (apenas empresas NÃO atribuídas)
   - select#upd_grupos_select (apenas grupos NÃO atribuídos)
   ↓
7. Usuário pode adicionar/remover empresas e grupos
   ↓
8. Usuário clica "Salvar Alterações" → Form faz POST
   ↓
9. Views.Usuario_upd() (POST) recebe dados e chama:
   - cl_gdf.upd_usuario(...)
   ↓
10. Retorna para Dm_Usuarios_view() com tabela atualizada
```

---

## 4. ESTRUTURA DO BANCO DE DADOS RELEVANTE

### Modelos Principais (em `app/db_GDF/Public/models.py`):

```
User (Django Auth)
├── id (PK)
├── username
├── email
├── first_name
├── last_name
├── is_active
└── groups (M2M → Group)

Group (Django Auth)
├── id (PK)
└── name

Clientes
├── cod_cliente (PK)
├── razao
├── cnpj
└── is_active

Empresas
├── cod_empresa (PK)
├── fantasia
├── razao
├── cnpj
└── cliente (FK → Clientes)

UserEmpresas (Tabela de Junção)
├── id (PK)
├── user (FK → User)
└── empresas (FK → Empresas)
[unique_together: (user, empresas)]

GrupoCliente (Tabela de Junção)
├── id (PK)
├── group (FK → Group)
└── cliente (FK → Clientes)
```

---

## 5. COMPONENTES DO JAVASCRIPT - `Script_Usuarios.js`

### Estado Global:
```javascript
const usuariosState = {
    allUsers: [],                    // Todos os usuários carregados
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    empresasSelecionadas: [],        // Para INSERT
    gruposSelecionados: [],          // Para INSERT
    todasEmpresas: [],               // ❌ Não está sendo utilizado
    todosGrupos: []                  // ❌ Não está sendo utilizado
};
```

### Funções Principais:

#### **Para INSERT:**
- `initUsuarioIns()` - Inicializa modal INSERT
- `adicionarEmpresaIns()` - Adiciona empresa selecionada ao array
- `removerEmpresaIns()` - Remove empresa do array
- `renderizarEmpresasSelecionadasIns()` - Atualiza tabela e hidden input
- `adicionarGrupoIns()` - Adiciona grupo selecionado ao array
- `removerGrupoIns()` - Remove grupo do array
- `renderizarGruposSelecionadosIns()` - Atualiza tabela e hidden input

#### **Para UPDATE:**
- `initUsuarioUpd()` - Inicializa modal UPDATE e escuta clicks em linhas
- `loadUser(userId)` - Faz AJAX GET para carregar dados do usuário
- `fillUserModal(user)` - Preenche formulário com dados do usuário
- `preencherSelectEmpresas(empresas)` - Preenche dropdown de empresas
- `preencherSelectGrupos(grupos)` - Preenche dropdown de grupos
- `adicionarEmpresa()` - Adiciona empresa ao array (UPDATE)
- `removerEmpresa()` - Remove empresa do array (UPDATE)
- `renderizarEmpresasSelecionadas()` - Atualiza tabela (UPDATE)
- `adicionarGrupo()` - Adiciona grupo ao array (UPDATE)
- `removerGrupo()` - Remove grupo do array (UPDATE)
- `renderizarGruposSelecionados()` - Atualiza tabela (UPDATE)

#### **Para Paginação/Busca:**
- `extrairUsuariosDoHTML()` - Carrega dados da tabela para memória
- `initBusca()` - Inicializa busca client-side
- `filtrarUsuarios()` - Filtra usuários por query
- `calcularPaginacao()` - Calcula páginas
- `atualizarTabelaFiltrada()` - Re-renderiza tabela
- `initPaginacao()` - Inicializa paginação

---

## 6. PROBLEMAS IDENTIFICADOS E SOLUÇÕES

### ❌ **PROBLEMA #1: Modal INSERT - Dropdowns Vazios**

**Localização**: `app/templates/Usuarios/Usuarios_ins.html` linhas 69-74, 99-104

**Sintoma**: 
- Select de empresas tem `<option>` vazio
- Select de grupos tem `<option>` vazio

**Causa Raiz**: 
- O modal INSERT espera `{% for emp in t_empresas %}` e `{% for grp in t_auth_groups %}`
- MAS: `app/views.py` linha 99-100 tem essas linhas comentadas!
- `Dm_Usuarios_view()` não passa `t_empresas` nem `t_auth_groups` para o template

**Código Problemático** (`app/views.py` linhas 99-100):
```python
return render(request, 'usuarios/Usuarios.html', {
    't_user': t_user,
    #'t_empresas': t_empresas,           # ❌ COMENTADO
    #'t_auth_groups': t_auth_groups,     # ❌ COMENTADO
})
```

**Solução Necessária**:
1. Modificar `Dm_Usuarios_view()` para chamar `get_usuario_ins(cod_cliente)`
2. Descomementar linhas 99-100
3. Passar dados corretamente ao template

```python
# CORRETO:
cl_gdf = Cl_Gdf()
t_user = cl_gdf.get_usuarios(i_cod_Cliente=cod_cliente)
usuario_ins_data = cl_gdf.get_usuario_ins(cod_cliente)

return render(request, 'usuarios/Usuarios.html', {
    't_user': t_user,
    't_empresas': usuario_ins_data.get('Todas_Empresas', []),
    't_auth_groups': usuario_ins_data.get('Todos_Grupos', []),
})
```

---

### ❌ **PROBLEMA #2: Modal UPDATE - Dropdowns de Itens Disponíveis**

**Localização**: `app/static/js/Script_Usuarios.js` linhas 320-325

**Sintoma**:
- Dropdown de empresas/grupos no UPDATE modal fica vazio
- Não há itens para adicionar

**Causa Raiz**:
- `fillUserModal(user)` tenta chamar `preencherSelectEmpresas(user.empresas_disponiveis)`
- MAS: `get_usuario_upd()` não retorna `empresas_disponiveis` e `grupos_disponiveis` no JSON!
- Função `loadUser()` recebe JSON com campos incorretos

**Código Problemático** (`app/classes/Gdf.py` linha 809):
```python
def get_usuario_upd(self, user_id, cod_cliente):
    # ... código ...
    return self.Retorn, empresas_disponiveis, grupos_disponiveis  # Retorna TUPLE, não JSON!
```

**Problema**: A função retorna uma tupla Python, mas a view precisa de um `JsonResponse`!

**Código Problemático** (`app/views.py` linhas 170-171):
```python
User, Empresas_Disponiveis, Grupos_Disponiveis = cl_gdf.get_usuario_upd(...)
# ❌ Mas depois faz JsonResponse de quem? User.get('erro')?
```

**Solução Necessária**:
1. Modificar `get_usuario_upd()` para retornar JSON com campos `empresas_disponiveis` e `grupos_disponiveis`
2. Modificar `views.Usuario_upd()` para extrair os dados corretamente
3. Garantir que `fillUserModal()` receba os dados esperados

```python
# CORRETO:
def get_usuario_upd(self, user_id, cod_cliente):
    # ... código ...
    return {
        "id": q_user.id,
        "username": q_user.username,
        # ... outros campos ...
        "empresas": list(q_empresas.values('cod_empresa', 'fantasia', 'razao')),
        "grupos": list(q_groups.values('id', 'name')),
        "empresas_disponiveis": list(empresas_disponiveis.values('cod_empresa', 'fantasia', 'razao')),
        "grupos_disponiveis": list(grupos_disponiveis.values('id', 'name'))
    }
```

---

### ⚠️ **PROBLEMA #3: Inconsistência de Nomes de IDs**

**Localização**: Múltiplos arquivos

**Sintoma**:
- Template usa `{{ emp.cod_empresa }}` e `{{ emp.fantasia }}`
- JavaScript tenta acessar `emp.id` e `emp.nome`
- Mismatch entre estrutura esperada e enviada

**Problema**:
```python
# get_usuario_ins retorna:
{"Todas_Empresas": [
    {"cod_empresa": "E001", "fantasia": "Empresa 1", "razao": "..."}
]}

# Mas fillUserModal faz:
preencherSelectEmpresas(user.empresas_disponiveis);
// Esperando: {id, nome}
```

**Solução**: Normalizar estrutura em JavaScript para aceitar variações:
```javascript
const option = document.createElement("option");
option.value = emp.cod_empresa || emp.id;
option.textContent = emp.fantasia || emp.nome || emp.razao;
```

---

## 7. FLUXO CORRETO - COMO DEVERIA FUNCIONAR

### **Inicialização da Página (GET /usuarios/)**

```python
# views.py
@login_required
def Dm_Usuarios_view(request):
    cod_cliente = request.session.get('cod_cliente')
    cl_gdf = Cl_Gdf()
    
    # Dados para a tabela
    t_user = cl_gdf.get_usuarios(cod_cliente)
    
    # Dados para o modal INSERT
    usuario_ins_data = cl_gdf.get_usuario_ins(cod_cliente)
    
    return render(request, 'usuarios/Usuarios.html', {
        't_user': t_user,
        't_empresas': usuario_ins_data.get('Todas_Empresas', []),
        't_auth_groups': usuario_ins_data.get('Todos_Grupos', []),
    })
```

### **Carregamento de Usuário para Edição (GET /usuario/{id}/)**

```python
# views.py
@login_required
def Usuario_upd(request, user_id):
    cod_cliente = request.session.get('cod_cliente')
    cl_gdf = Cl_Gdf()
    
    if request.method == "GET":
        user_data = cl_gdf.get_usuario_upd(user_id, cod_cliente)
        if user_data.get('erro'):
            return JsonResponse({"erro": user_data['erro']}, status=404)
        
        # user_data já tem todos os campos necessários
        return JsonResponse(user_data)
```

---

## 8. CHECKLIST DE CORREÇÕES NECESSÁRIAS

- [ ] **Corrigir `Dm_Usuarios_view()`**: Adicionar chamada para `get_usuario_ins()`
- [ ] **Descomementar context**: Linhas 99-100 em `views.py`
- [ ] **Modificar `get_usuario_upd()`**: Retornar JSON com `empresas_disponiveis` e `grupos_disponiveis`
- [ ] **Verificar `Usuario_upd()` GET**: Garantir que retorna JsonResponse correto
- [ ] **Testar modal INSERT**: Verificar se dropdowns preenchem corretamente
- [ ] **Testar modal UPDATE**: Verificar se dados carregam e dropdowns funcionam
- [ ] **Normalizar nomes de campos**: Considerar usar `id` e `nome` em toda a estrutura

---

## 9. ESTRUTURA DOS DADOS ESPERADOS

### **Dados para Modal INSERT** (de `get_usuario_ins()`):
```json
{
  "Todas_Empresas": [
    {
      "cod_empresa": "E001",
      "fantasia": "Empresa São Paulo",
      "razao": "Empresa LTDA"
    }
  ],
  "Todos_Grupos": [
    {
      "id": 1,
      "name": "Gerente"
    }
  ]
}
```

### **Dados para Modal UPDATE** (de `get_usuario_upd()`, via AJAX):
```json
{
  "id": 5,
  "username": "joao.silva",
  "email": "joao@email.com",
  "first_name": "João",
  "last_name": "Silva",
  "is_active": true,
  "empresas": [
    {
      "cod_empresa": "E001",
      "fantasia": "Empresa São Paulo",
      "razao": "Empresa LTDA"
    }
  ],
  "grupos": [
    {
      "id": 1,
      "name": "Gerente"
    }
  ],
  "empresas_disponiveis": [
    {
      "cod_empresa": "E002",
      "fantasia": "Empresa Rio",
      "razao": "Empresa RJ LTDA"
    }
  ],
  "grupos_disponiveis": [
    {
      "id": 2,
      "name": "Vendedor"
    }
  ]
}
```

---

## 10. RESUMO EXECUTIVO

O sistema está **70% implementado**:

✅ **Funcionando**:
- Tabela de usuários com paginação e busca (client-side)
- Estrutura de modelos e banco de dados corretos
- Lógica de negócio em `Gdf.py` implementada
- Templates com estrutura HTML/CSS correta
- Funções JavaScript para manipulação de seleções

❌ **NÃO Funcionando**:
- Modal INSERT: Dropdowns vazios (dados não passados pelo view)
- Modal UPDATE: Dropdowns vazios (dados não retornados pela API)
- Fluxo de dados incompleto entre view e template para INSERT
- Fluxo de dados incompleto entre API e JavaScript para UPDATE

🔧 **Próximos Passos**:
1. Descomementar context em `views.py` linha 99-100
2. Adicionar chamada a `get_usuario_ins()` em `Dm_Usuarios_view()`
3. Modificar `get_usuario_upd()` para retornar `empresas_disponiveis` e `grupos_disponiveis`
4. Testar fluxo completo de INSERT
5. Testar fluxo completo de UPDATE

