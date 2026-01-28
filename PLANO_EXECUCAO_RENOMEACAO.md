# ⚠️ PLANO DE EXECUÇÃO - RENOMEAÇÃO SEGURA

## 🎯 OBJETIVO
Executar renomeações seguindo o Workbook de Nomenclatura SEM quebrar o projeto.

---

## 🔴 AVISOS CRÍTICOS

1. **NÃO RENOMEIE TUDO DE UMA VEZ** - Isso quebrará 100% do projeto
2. **CRIE BRANCH SEPARADA** antes de qualquer alteração
3. **TESTE APÓS CADA BLOCO** de renomeações
4. **FAÇA BACKUP** do banco de dados antes

---

## 📋 ORDEM DE EXECUÇÃO RECOMENDADA

### FASE 1: PREPARAÇÃO (0 riscos)
- [x] Documentar mapeamento completo
- [ ] Criar branch `refactor/nomenclatura-workbook`
- [ ] Backup do banco de dados
- [ ] Commit inicial com estado atual

---

### FASE 2: VARIÁVEIS LOCAIS (Baixo risco)

**Por quê primeiro?** Variáveis locais têm escopo limitado - não afetam outras partes do código.

**Arquivos**:
- `app/classes/Gdf.py` - métodos individuais
- `app/views.py` - views individuais

**Exemplo**:
```python
# ANTES
def Get_Clientes(self):
    clientes_data = []
    q_clientes = Clientes.objects.all()
    
# DEPOIS
def Get_Clientes(self):
    lsl_dados_clientes = []
    l_v_query_clientes = Clientes.objects.all()
```

**Teste**: Executar `python manage.py runserver` e verificar página /clientes/

---

### FASE 3: PARÂMETROS DE FUNÇÕES (Médio risco)

**Arquivos**:
- `app/classes/Gdf.py`
- `app/views.py`

**Estratégia**: Manter parâmetros que JÁ têm `i_` inalterados.

**Exemplo**:
```python
# ANTES
def Cliente_ins(self, i_cliente, i_razao, i_cnpj):  # ✅ Já correto!
    
# ANTES (views)
def Cliente_upd(request, cod_cliente):  # ❌ Falta i_
    
# DEPOIS (views)
def Cliente_upd(request, i_v_cod_cliente):  # ✅ Correto
```

**Teste**: Testar INSERT e UPDATE de clientes

---

### FASE 4: MÉTODOS DA CLASSE Cl_Gdf (ALTO RISCO) 🔴

**Por quê?** Métodos são chamados em TODA a aplicação (views, templates).

**Estratégia**: Renomear um método por vez + todos os locais que o chamam.

#### 4.1 Exemplo: Get_Clientes → fn_obter_clientes

**Passo 1**: Buscar TODAS as referências
```bash
grep -r "Get_Clientes" app/
```

**Passo 2**: Renomear método na classe
```python
# app/classes/Gdf.py
def fn_obter_clientes(self):  # ANTES: Get_Clientes
    pass
```

**Passo 3**: Atualizar TODAS as chamadas
```python
# app/views.py
t_clientes = cl_gdf.fn_obter_clientes()  # ANTES: Get_Clientes()
```

**Passo 4**: Testar
```bash
python manage.py runserver
# Testar página /clientes/
```

**Repetir para cada método** (20 métodos no total).

---

### FASE 5: VIEWS (CRÍTICO) 🔴🔴

**Por quê?** Views são referenciadas em:
- `urls.py` (name=...)
- Templates ({% url 'nome' %})
- JavaScript (fetch('/url/'))

#### Exemplo: Login_view → fn_view_login

**Passo 1**: Renomear função em views.py
```python
# app/views.py
def fn_view_login(request):  # ANTES: Login_view
    pass
```

**Passo 2**: Atualizar urls.py
```python
# GDF_PJT/urls.py
path('Login/', views.fn_view_login, name='Login'),  # name NÃO muda!
```

**Passo 3**: Verificar templates
```html
<!-- NÃO precisa mudar - usa 'name' do urls.py -->
<a href="{% url 'Login' %}">Login</a>
```

**Passo 4**: Verificar JavaScript
```js
// Usa URL direta - NÃO afetado
fetch('/Login/')
```

**Repetir para cada view** (16 views no total).

---

### FASE 6: JAVASCRIPT (Médio risco)

**Arquivos**:
- `app/static/js/Script_Clientes.js`
- `app/static/js/Script_Usuarios.js`
- `app/static/js/Script_Empresas.js`

**Estratégia**: Usar busca/substituição global por arquivo.

**Exemplo**:
```js
// ANTES
const clientesState = { ... };
function loadCliente(id) { ... }

// DEPOIS
const og_estado_clientes = { ... };
function fn_carregar_cliente(i_v_id) { ... }
```

**Teste**: Abrir página, verificar console do navegador (F12).

---

### FASE 7: CLASSE Cl_Gdf → ClGdf (CRÍTICO) 🔴🔴🔴

**Por quê último?** Classe é instanciada em TODOS os lugares.

**Passo 1**: Buscar TODAS as instanciações
```bash
grep -r "Cl_Gdf" app/
```

**Passo 2**: Renomear classe
```python
# app/classes/Gdf.py
class ClGdf():  # ANTES: Cl_Gdf
    pass
```

**Passo 3**: Atualizar TODOS os imports e instanciações
```python
# app/views.py
from app.classes.Gdf import ClGdf  # ANTES: Cl_Gdf

cl_gdf = ClGdf()  # ANTES: Cl_Gdf()
```

**Passo 4**: Teste completo
```bash
python manage.py test
python manage.py runserver
# Testar TODAS as páginas
```

---

## 🧪 ESTRATÉGIA DE TESTES

### Após cada fase:
1. ✅ `python manage.py check` - Verificar erros Django
2. ✅ `python manage.py runserver` - Iniciar servidor
3. ✅ Abrir cada página principal:
   - `/Login/`
   - `/Home/`
   - `/usuarios/`
   - `/empresas/`
   - `/clientes/`
4. ✅ Testar CRUD completo:
   - INSERT
   - UPDATE
   - DELETE (se existir)
5. ✅ Verificar console do navegador (F12) - erros JS

---

## 🔄 ROLLBACK PLAN

Se algo quebrar:

```bash
# Voltar para commit anterior
git reset --hard HEAD~1

# Ou restaurar branch main
git checkout main
```

---

## 📊 PROGRESSO ESTIMADO

| Fase | Tempo Estimado | Risco |
|------|----------------|-------|
| 1. Preparação | 10 min | ✅ Zero |
| 2. Variáveis locais | 2-3 horas | 🟡 Baixo |
| 3. Parâmetros | 1-2 horas | 🟠 Médio |
| 4. Métodos Cl_Gdf | 4-6 horas | 🔴 Alto |
| 5. Views | 3-4 horas | 🔴 Crítico |
| 6. JavaScript | 2-3 horas | 🟠 Médio |
| 7. Classe Cl_Gdf | 1-2 horas | 🔴 Crítico |
| **TOTAL** | **15-25 horas** | - |

---

## ✅ CHECKLIST FINAL

Antes de fazer merge para main:

- [ ] Todas as páginas carregam sem erro
- [ ] CRUD de usuários funciona
- [ ] CRUD de empresas funciona
- [ ] CRUD de clientes funciona
- [ ] Certificados carregam/salvam
- [ ] Login/Logout funcionam
- [ ] Direitos de acesso funcionam
- [ ] Dashboards carregam
- [ ] Console do navegador sem erros
- [ ] `python manage.py check` sem warnings
- [ ] Testes automatizados passam (se existirem)

---

## 🎯 RECOMENDAÇÃO FINAL

**OPÇÃO 1 - CONSERVADORA** (Recomendada):
- Aplicar apenas PARTE das regras:
  - ✅ Variáveis locais novas
  - ✅ Funções JavaScript novas
  - ❌ NÃO renomear código existente

**OPÇÃO 2 - PROGRESSIVA**:
- Renomear apenas 1 módulo por vez:
  - Semana 1: Apenas Clientes
  - Semana 2: Apenas Empresas
  - Semana 3: Apenas Usuários

**OPÇÃO 3 - COMPLETA** (Alto risco):
- Seguir TODAS as fases acima
- Dedicar sprint inteiro
- Testar exaustivamente
- Ter plano de rollback pronto

---

📅 **Criado**: 2026-01-28
📝 **Versão**: 1.0
⚠️ **Status**: AGUARDANDO DECISÃO DO TIME

