# 📝 Implementação: Insert Usuário com Empresas e Grupos

## 🔄 Fluxo Completo

### 1️⃣ **Frontend - Modal INSERT (HTML)**
Arquivo: [app/templates/Usuarios/Usuarios_ins.html](app/templates/Usuarios/Usuarios_ins.html)

**Estrutura**:
- **TAB 1 - Dados**: Username, Email, Senha (campos obrigatórios)
- **TAB 2 - Empresas**: Select + botão "Adicionar" → Tabela de selecionadas
- **TAB 3 - Grupos**: Select + botão "Adicionar" → Tabela de selecionadas
- **Hidden Inputs**: 
  - `ls_empresas` = "1,2,3" (IDs separados por vírgula)
  - `ls_grupos` = "4,5,6" (IDs separados por vírgula)

### 2️⃣ **Frontend - JavaScript (JS)**
Arquivo: [app/static/js/Script_Usuarios.js](app/static/js/Script_Usuarios.js)

**Funções principais**:

```javascript
// ✅ Validação do formulário antes de submit
validarFormularioIns(event)
  └─ Valida: username, email, senha, empresas, grupos
  └─ Se falhar: mostra alertas
  └─ Se passar: envia formulário

// ✅ Preenche select de empresas (GET /usuario/inserir/)
preencherSelectInsEmpresas(empresas)
  └─ Recebe array: [{id: 1, fantasia: "Empresa A"}, ...]
  └─ Popula select com options

// ✅ Adiciona empresa ao estado
adicionarEmpresaIns()
  └─ Lê select value
  └─ Valida duplicatas
  └─ Adiciona ao usuariosState.empresasSelecionadas
  └─ Renderiza tabela + atualiza hidden input

// ✅ Remove empresa do estado
removerEmpresaIns(empId)
  └─ Filtra out do array
  └─ Renderiza tabela atualizada

// ✅ Idem para grupos
adicionarGrupoIns()
removerGrupoIns(grupoId)
```

**Estado em Memória**:
```javascript
usuariosState = {
    empresasSelecionadas: [
        { id: 1, nome: "Empresa A" },
        { id: 2, nome: "Empresa B" }
    ],
    gruposSelecionados: [
        { id: 4, nome: "Admin" },
        { id: 5, nome: "User" }
    ]
}
```

### 3️⃣ **Backend - View (Django)**
Arquivo: [app/views.py - Usuario_ins](app/views.py#L123)

**GET Request** (Carregar dados do modal):
```python
GET /usuario/inserir/
↓
return JsonResponse({
    "todas_empresas": [...],
    "todos_grupos": [...]
})
```

**POST Request** (Submeter novo usuário):
```python
POST /usuario/inserir/
DATA:
{
    "username": "joao",
    "email": "joao@example.com",
    "password": "senha123",
    "password_confirm": "senha123",
    "first_name": "João",
    "last_name": "Silva",
    "ls_empresas": "1,2,3",      # ← Vem do hidden input
    "ls_grupos": "4,5"            # ← Vem do hidden input
}

↓ VALIDAÇÕES:
  1. username não vazio
  2. email válido e não existe
  3. senha ≥ 8 caracteres (opcional, mas recomendado)
  4. senhas conferem
  5. empresas_str não vazio
  6. grupos_str não vazio

↓ CALL Cl_Gdf().Usuario_ins(...)
  └─ Cria usuário Django
  └─ Vincula empresas via UserEmpresas
  └─ Vincula grupos via Group.set()

↓ RESPONSE:
  Sucesso → Redireciona para lista com mensagem
  Erro → Redireciona com error_message
```

### 4️⃣ **Backend - Classe Gdf.py**
Arquivo: [app/classes/Gdf.py - Usuario_ins](app/classes/Gdf.py#L570)

**Novo método** (totalmente reescrito):

```python
def Usuario_ins(
    username,           # str
    email,             # str
    password,          # str (será hasheada)
    first_name,        # str (opcional)
    last_name,         # str (opcional)
    empresas_ids,      # str "1,2,3" ou list [1,2,3]
    grupos_ids,        # str "4,5" ou list [4,5]
    cod_cliente        # int (para validação multi-tenant)
) → Dict {success, message, user_id}
```

**Lógica**:
1. ✅ Validação de parâmetros obrigatórios
2. ✅ Conversão de string para list (se necessário)
3. ✅ Validação: empresas pertencem ao cliente
4. ✅ Validação: grupos pertencem ao cliente
5. ✅ Criar User Django (com hash de senha)
6. ✅ Criar registros UserEmpresas (M2M)
7. ✅ Associar grupos (set groups)
8. ✅ Registrar log de sucesso
9. ✅ Retornar status + mensagem

**Tratamento de Erros**:
- `ValueError`: Validação falhou → 400
- `IntegrityError`: Username/email já existe → 400
- `Exception`: Erro inesperado → 500

---

## 🧪 Teste Manual

### Pré-requisitos
```bash
# 1. Database com dados de teste
python manage.py migrate

# 2. Inserir dados mínimos
python manage.py shell
>>> from app.db_GDF.Public.models import Clientes, Empresas, GrupoCliente
>>> from django.contrib.auth.models import Group
>>>
>>> # Criar cliente
>>> cli = Clientes.objects.create(cod_cliente=1, razao_social="Teste")
>>>
>>> # Criar empresa
>>> emp1 = Empresas.objects.create(cod_empresa=1, cliente=cli, fantasia="Emp1", razao="Empresa 1")
>>> emp2 = Empresas.objects.create(cod_empresa=2, cliente=cli, fantasia="Emp2", razao="Empresa 2")
>>>
>>> # Criar grupos
>>> grp1 = Group.objects.create(name="Admin")
>>> grp2 = Group.objects.create(name="User")
>>>
>>> # Vincular grupos ao cliente
>>> GrupoCliente.objects.create(cliente=cli, group=grp1)
>>> GrupoCliente.objects.create(cliente=cli, group=grp2)
```

### Teste 1: GET (Carregar dados do modal)
```bash
curl -X GET http://localhost:8000/usuario/inserir/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Esperado:
{
    "todas_empresas": [
        {"cod_empresa": 1, "fantasia": "Emp1", "razao": "Empresa 1"},
        {"cod_empresa": 2, "fantasia": "Emp2", "razao": "Empresa 2"}
    ],
    "todos_grupos": [
        {"id": 1, "name": "Admin"},
        {"id": 2, "name": "User"}
    ]
}
```

### Teste 2: POST (Criar novo usuário)
```bash
curl -X POST http://localhost:8000/usuario/inserir/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d "username=joao&email=joao@test.com&password=senha123&password_confirm=senha123&first_name=João&last_name=Silva&ls_empresas=1,2&ls_grupos=1,2&csrfmiddlewaretoken=YOUR_CSRF"

# Esperado (sucesso):
- Status 200
- Redireciona para /usuarios/
- Novo usuário visível na lista

# Esperado (erro - sem empresas):
- Status 200 (renderiza com erro)
- error_message exibida
- Usuário NÃO criado
```

### Teste 3: Frontend - Validação JS
1. Abrir modal INSERT
2. Preencher dados básicos APENAS
3. NÃO adicionar empresas/grupos
4. Clicar "Salvar"
5. ❌ Alert: "Selecione pelo menos 1 empresa"

### Teste 4: Verificar vinculações no BD
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.get(username="joao")
>>>
>>> # Verificar empresas
>>> from app.db_GDF.Public.models import UserEmpresas
>>> UserEmpresas.objects.filter(user=u).values_list('empresa__cod_empresa', flat=True)
[1, 2]  # ✅
>>>
>>> # Verificar grupos
>>> u.groups.all().values_list('id', 'name')
[(1, 'Admin'), (2, 'User')]  # ✅
```

---

## 🔍 Checklist de Implementação

- [x] Método `Usuario_ins` reescrito em Gdf.py
- [x] View `Usuario_ins` POST atualizada
- [x] Validação de empresas e grupos
- [x] Conversão de string para list
- [x] Criação de UserEmpresas (M2M)
- [x] Atribuição de grupos (Group.set)
- [x] Tratamento de erros (ValueError, IntegrityError)
- [x] Logging de operações
- [x] Validação JS frontend
- [x] Feedback visual no console
- [x] Hidden inputs atualizados (ls_empresas, ls_grupos)
- [x] Confirmação de senha no formulário

---

## ⚠️ Pontos de Atenção

### 1. **UserEmpresas vs Empresas.user**
O modelo antigo usava `Empresas.user.add()` (ManyToMany).
Novo usa `UserEmpresas.objects.create()` (ForeignKey explicit).

**⚠️ Verificar**: Qual é a estrutura do modelo em `app/db_GDF/Public/models.py`?

Se for ManyToMany, modificar:
```python
# De:
for empresa in empresas_obj:
    UserEmpresas.objects.create(user=user_instance, empresa=empresa)

# Para:
user_instance.empresas.set(empresas_obj)
```

### 2. **Validação de Email Duplicado**
O `create_user` do Django já valida, mas podemos adicionar check:
```python
if User.objects.filter(email=email).exists():
    raise ValueError("Email já existe")
```

### 3. **Senha Mínima**
Adicionar validação de força de senha:
```python
if len(password) < 8:
    raise ValueError("Senha deve ter pelo menos 8 caracteres")
```

### 4. **Transações**
Considerar usar `@transaction.atomic()` para rollback em caso de erro:
```python
from django.db import transaction

@transaction.atomic
def Usuario_ins(...):
    # código aqui
```

---

## 📊 Dados Esperados em Produção

| Campo | Exemplo | Validação |
|-------|---------|-----------|
| username | `joao.silva` | Único, alfanumérico + `._-` |
| email | `joao@empresa.com` | Formato válido, único |
| password | `Sen@123abc` | ≥8 chars, misturado |
| empresas | `1,2,3` | Existem e pertencem ao cliente |
| grupos | `4,5` | Existem e pertencem ao cliente |
| first_name | `João` | Opcional |
| last_name | `Silva` | Opcional |

