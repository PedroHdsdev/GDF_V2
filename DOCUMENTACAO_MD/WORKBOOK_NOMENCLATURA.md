# 📘 WORKBOOK – Boas Práticas de Nomenclatura de Código
## Projeto GDF_V2 | Sistema Multi-Tenant ERP

---

## 🎯 PRINCÍPIOS FUNDAMENTAIS

### 1. **CLAREZA > BREVIDADE**
- Nomes longos e descritivos são preferíveis a abreviações obscuras
- O nome deve comunicar imediatamente o propósito e contexto
- Evitar siglas não universalmente conhecidas

### 2. **CONSISTÊNCIA OBRIGATÓRIA**
- Uma vez definido um padrão, ele deve ser aplicado em TODO o código
- Violações devem ser corrigidas imediatamente via refatoração
- Novos desenvolvedores devem seguir rigorosamente este workbook

### 3. **PREFIXOS SEMPRE PRESENTES**
- NUNCA criar identificadores sem prefixo de escopo + tipo
- Exceções: classes Django (models, views base), constantes de framework

---

## 📐 ESTRUTURA DE NOMENCLATURA

### **Formato Geral**
```
[Escopo]_[Tipo]_[Nome_Descritivo]
```

### **Exemplo Completo**
```python
# ❌ ERRADO
def usuarios():
    data = get_data()
    return data

# ✅ CORRETO
def fn_view_listar_usuarios(i_request):
    lsl_dados_usuarios = cl_gdf_instance.get_usuarios(i_v_cod_cliente=gv_cod_cliente)
    return render(i_request, 'usuarios/Index_Usuarios.html', {'t_user': lsl_dados_usuarios})
```

---

## 🔤 PREFIXOS DE ESCOPO

### **Global (`g`)**
- Variáveis/objetos acessíveis em todo o módulo ou aplicação
- Usado para configurações, constantes globais, singletons

```python
# Configuração global
gv_database_timeout = 30
gv_max_upload_size = 5242880  # 5MB

# Objeto global
g_ol_cache_manager = CacheManager()
```

### **Local (`l`)**
- Variáveis/objetos com escopo de função/método
- 95% das variáveis devem ser locais

```python
def fn_processar_nota_fiscal(i_v_xml_path: str):
    lv_arquivo_validado = fn_validar_xml(i_v_xml_path)
    lol_nfe_instance = NFe.objects.create(...)
    return r_ol_nfe_instance
```

### **Session (`s`)**
- Dados armazenados em sessão HTTP (Django)
- Usado para autenticação, contexto do usuário

```python
sv_cod_cliente = request.session.get('cod_cliente')
sls_solucoes_ativas = request.session.get('t_solucoes', [])
```

---

## 🏷️ PREFIXOS DE TIPO

### **Variáveis Primitivas**

#### `v` - Variável (string, int, float, bool, date)
```python
lv_nome_usuario = "Pedro Silva"
lv_idade = 35
lv_salario = Decimal('15000.00')
lv_ativo = True
lv_data_contratacao = datetime.now()
```

### **Coleções**

#### `lsl` - Lista Local
```python
lsl_usuarios_ativos = User.objects.filter(is_active=True)
lsl_cnpjs_validos = ['12345678000190', '98765432000101']
lsl_notas_fiscais = []
```

#### `lsg` - Lista Global
```python
# settings.py ou configurações globais
lsg_databases_replicadas = ['GDF_DEV', 'REPROCESSAMENTO_DEV']
lsg_extensoes_permitidas = ['.xml', '.pdf', '.zip']
```

#### `dict` / `ld` - Dicionário Local
```python
ld_dados_empresa = {
    'cnpj': '12345678000190',
    'razao': 'Empresa XYZ Ltda',
    'matriz': True
}

ld_filtros_query = {
    'is_active': True,
    'tipo': 'M'
}
```

#### `dg` - Dicionário Global
```python
# Mapeamento de códigos de erro
dg_erros_nfe = {
    '100': 'Autorizado o uso da NF-e',
    '101': 'Cancelamento de NF-e homologado',
    '135': 'Evento registrado e vinculado a NF-e'
}
```

### **Objetos**

#### `ol` - Objeto Local (instância de classe)
```python
lol_gdf_instance = ClGdf()
lol_usuario = User.objects.get(id=user_id)
lol_empresa = Empresas.objects.filter(cnpj=lv_cnpj).first()
```

#### `og` - Objeto Global (singleton, manager)
```python
# Em settings ou módulos principais
g_ol_logger = logging.getLogger('gdf_app')
g_ol_db_router = GDFRouter()
```

#### `cl` - Classe
```python
class ClGdf:
    """Classe de negócio principal do sistema GDF"""
    pass

class ClCargaXml:
    """Classe para processamento de arquivos XML de NF-e"""
    pass
```

### **Funções e Métodos**

#### Métodos CRUD (operações de dados)
```python
# get_ - Consulta/leitura de dados
def get_usuarios(i_v_cod_cliente: str) -> List[Dict]:
    """Retorna lista de usuários do cliente"""
    pass

def get_dados(i_ol_user: User) -> bool:
    """Carrega dados iniciais do usuário"""
    pass

# set_ - Criação/inserção de dados
def set_usuario(i_v_username: str, i_v_email: str) -> User:
    """Cria novo usuário no sistema"""
    pass

def set_empresa(i_ld_dados: Dict) -> Empresas:
    """Insere nova empresa"""
    pass

# upd_ - Atualização de dados
def upd_usuario(i_v_user_id: int, i_ld_dados: Dict) -> User:
    """Atualiza dados do usuário"""
    pass

def upd_empresa_certificado(i_v_cod_empresa: str, i_file) -> bool:
    """Atualiza certificado digital da empresa"""
    pass

# del_ - Exclusão de dados
def del_usuario(i_v_user_id: int) -> bool:
    """Exclusão lógica do usuário"""
    pass

def del_empresa(i_v_cod_empresa: str) -> bool:
    """Remove empresa do sistema"""
    pass
```

#### `fn_` - Funções auxiliares/lógica de negócio
```python
# Validações
def fn_validar_cnpj(i_v_cnpj: str) -> bool:
    """Valida formato e dígitos verificadores do CNPJ"""
    pass

def fn_validar_xml_schema(i_v_xml_path: str) -> bool:
    """Valida XML contra schema XSD"""
    pass

# Processamento/Transformação
def fn_gerar_token_jwt(i_ol_user: User) -> str:
    """Gera token JWT para autenticação"""
    pass

def fn_processar_xml_nfe(i_file) -> Dict:
    """Pipeline de processamento de NF-e"""
    pass

# Cálculos/Utilities
def fn_calcular_digito_cnpj(i_v_cnpj_base: str) -> str:
    """Calcula dígitos verificadores do CNPJ"""
    pass
```

#### `fn_view_` - View Django (controller)
```python
@login_required(login_url='Login')
def fn_view_listar_usuarios(i_request):
    """Lista usuários do cliente logado com paginação"""
    # View chama métodos get_ da classe de negócio
    lsl_usuarios = cl_gdf.get_usuarios(i_v_cod_cliente=sv_cod_cliente)
    pass

def fn_view_inserir_empresa(i_request):
    """Modal de inserção de nova empresa"""
    # View chama método set_ para criação
    lol_empresa = cl_gdf.set_empresa(i_ld_dados=ld_form_data)
    pass
```

#### `fn_api` - Endpoint de API (JSON response)
```python
@require_http_methods(['POST'])
def fn_api_processar_xml(i_request):
    """API para upload e processamento de XML de NF-e"""
    return JsonResponse({'status': 'success', 'nfe_id': lv_nfe_id})
```

### **Métodos Privados e Auxiliares**

#### `_get_`, `_set_`, `_upd_`, `_del_` - Métodos privados CRUD
```python
class ClGdf:
    def _get_empresas_cache(self, i_v_cod_cliente: str) -> List[Empresas]:
        """Busca empresas do cache interno (privado)"""
        pass
    
    def _set_cache_usuario(self, i_ol_user: User, i_ld_dados: Dict):
        """Armazena dados do usuário em cache (privado)"""
        pass
```

#### `_fn_` - Funções auxiliares privadas
```python
class ClCargaXml:
    def _fn_get_text(self, i_element, i_v_path, i_v_default=''):
        """Extrai texto de elemento XML com fallback para namespace"""
        pass
    
    def _fn_to_decimal(self, i_v_value, i_v_default=0):
        """Converte string para Decimal com tratamento de erro"""
        pass
    
    def _fn_validar_schema(self, i_v_xml_path: str) -> bool:
        """Valida XML contra schema (auxiliar privado)"""
        pass
```

---

## � DIFERENCIAÇÃO: MÉTODOS vs FUNÇÕES

### **Quando usar `get_`, `set_`, `upd_`, `del_` (Métodos CRUD)**
Operações que **manipulam dados** diretamente (banco, cache, sessão):

```python
class ClGdf:
    # ✅ MÉTODOS - Interagem com dados
    def get_usuarios(self, i_v_cod_cliente: str) -> List[Dict]:
        """Query no banco"""
        return User.objects.filter(...)
    
    def set_empresa(self, i_ld_dados: Dict) -> Empresas:
        """Cria registro no banco"""
        return Empresas.objects.create(...)
    
    def upd_certificado(self, i_v_cod_empresa: str, i_file) -> bool:
        """Atualiza registro existente"""
        empresa.cert = i_file
        empresa.save()
    
    def del_usuario(self, i_v_user_id: int) -> bool:
        """Remove/desativa registro"""
        user.is_active = False
        user.save()
```

### **Quando usar `fn_` (Funções Auxiliares/Lógica)**
Operações que **processam/transformam/validam** sem tocar dados diretamente:

```python
class ClGdf:
    # ✅ FUNÇÕES - Lógica de negócio/auxiliar
    def fn_validar_cnpj(self, i_v_cnpj: str) -> bool:
        """Valida formato (não acessa banco)"""
        return len(i_v_cnpj) == 14 and fn_calcular_digito(i_v_cnpj)
    
    def fn_gerar_token_jwt(self, i_ol_user: User) -> str:
        """Cria token (não persiste)"""
        return jwt.encode(payload, SECRET_KEY)
    
    def fn_formatar_relatorio(self, i_lsl_dados: List) -> Dict:
        """Transforma dados (não consulta)"""
        return {"total": len(i_lsl_dados), "items": i_lsl_dados}
    
    def _fn_parse_xml(self, i_element) -> Dict:
        """Auxiliar privado de parsing"""
        return {"data": element.text}
```

### **Regra de Ouro**
```
Método CRUD → Verbo de dados (get/set/upd/del) → Acessa persistência
Função Auxiliar → Prefixo fn_ → Lógica pura sem I/O de dados
```

**Exemplo Prático - View com ambos:**
```python
def fn_view_inserir_empresa(i_request):
    """View de criação de empresa"""
    
    # 1. Extrai dados do form
    lv_cnpj = i_request.POST.get('cnpj')
    
    # 2. FUNÇÃO - Valida (lógica pura)
    if not fn_validar_cnpj(lv_cnpj):
        return JsonResponse({'error': 'CNPJ inválido'})
    
    # 3. FUNÇÃO - Gera código (lógica)
    lv_cod_empresa = fn_gerar_codigo_empresa(i_v_cnpj=lv_cnpj)
    
    # 4. MÉTODO - Cria no banco (dados)
    lol_empresa = cl_gdf.set_empresa(i_ld_dados={
        'cod_empresa': lv_cod_empresa,
        'cnpj': lv_cnpj,
        'razao': i_request.POST.get('razao')
    })
    
    return JsonResponse({'success': True, 'id': lol_empresa.cod_empresa})
```

---

## �🔄 PREFIXOS DE FLUXO (Input/Output)

### **Input (`i_`)**
- Parâmetros de entrada de função/método
- Sempre prefixar argumentos recebidos

```python
def set_usuario(
    i_request,
    i_v_username: str,
    i_v_email: str,
    i_lsl_empresas: List[int],
    i_v_cod_cliente: str
) -> User:
    """
    Insere novo usuário no sistema (método CRUD)
    
    Args:
        i_request: Objeto de requisição Django
        i_v_username: Nome de usuário único
        i_v_email: Email do usuário
        i_lsl_empresas: Lista de IDs de empresas vinculadas
        i_v_cod_cliente: Código do cliente (multi-tenant)
    
    Returns:
        r_ol_user: Instância do usuário criado
    """
    lol_user = User.objects.create_user(
        username=i_v_username,
        email=i_v_email
    )
    
    # Vincular empresas
    for lv_empresa_id in i_lsl_empresas:
        UserEmpresas.objects.create(
            user=lol_user,
            empresa_id=lv_empresa_id
        )
    
    return lol_user  # Torna-se r_ol_user no retorno
```

### **Retorno (`r_`)**
- Variável que será retornada pela função
- Facilita identificação do valor de retorno na leitura

```python
def fn_get_empresas_usuario(i_ol_user: User) -> List[Empresas]:
    """Retorna lista de empresas vinculadas ao usuário"""
    
    r_lsl_empresas = Empresas.objects.filter(
        userempresas__user=i_ol_user
    ).distinct()
    
    return r_lsl_empresas

# Uso
lsl_minhas_empresas = fn_get_empresas_usuario(i_ol_user=lol_usuario_atual)
```

### **Retorno Múltiplo**
```python
def fn_processar_xml_completo(i_v_xml_path: str) -> tuple:
    """Valida XML e retorna dados estruturados (função auxiliar)"""
    
    lv_xml_valido = fn_validar_schema(i_v_xml_path)
    
    if not lv_xml_valido:
        r_v_sucesso = False
        r_v_mensagem = "XML inválido"
        r_ld_dados = {}
        return r_v_sucesso, r_v_mensagem, r_ld_dados
    
    ld_dados_nfe = fn_parse_xml(i_v_xml_path)
    
    r_v_sucesso = True
    r_v_mensagem = "Processado com sucesso"
    r_ld_dados = ld_dados_nfe
    
    return r_v_sucesso, r_v_mensagem, r_ld_dados
```

---

## 🗂️ NOMENCLATURA POR CONTEXTO

### **Models Django**

#### Classes de Modelo (PascalCase + Contexto)
```python
# ✅ CORRETO - Sufixo indica contexto de domínio
class NFe_Emitente(models.Model):
    """Dados do emitente da NF-e"""
    id_emitente = models.AutoField(primary_key=True)
    cnpj = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=120)

class NFe_Produto(models.Model):
    """Produtos/Serviços da NF-e"""
    id_produto = models.AutoField(primary_key=True)
    nfe = models.ForeignKey(NFe, on_delete=models.CASCADE)

# Modelos públicos (sem prefixo de domínio)
class Clientes(models.Model):
    cod_cliente = models.CharField(primary_key=True, max_length=10)
    razao = models.CharField(max_length=120)

class Empresas(models.Model):
    cod_empresa = models.CharField(primary_key=True, max_length=10)
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE)
```

#### Campos de Modelo (snake_case descritivo)
```python
class NFe_Destinatario(models.Model):
    # IDs técnicos
    id_destinatario = models.AutoField(primary_key=True)
    
    # Identificação fiscal
    cnpj_cpf = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=120)
    nome_fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    
    # Timestamps
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # Relacionamentos
    endereco = models.OneToOneField(NFe_Endereco, on_delete=models.SET_NULL, null=True)
    nfe = models.ForeignKey(NFe, on_delete=models.CASCADE)
```

### **Views Django**

#### Padrão: `fn_view_[ação]_[recurso]`
```python
# CRUD básico
def fn_view_listar_usuarios(i_request):
    """Lista usuários com busca e paginação"""
    pass

def fn_view_inserir_usuario(i_request):
    """Modal/Form de inserção de usuário"""
    pass

def fn_view_atualizar_usuario(i_request, i_v_user_id):
    """GET: retorna dados JSON | POST: atualiza usuário"""
    pass

def fn_view_excluir_usuario(i_request, i_v_user_id):
    """Exclusão lógica ou física de usuário"""
    pass

# Views específicas
def fn_view_dashboard_vendas(i_request):
    """Dashboard analítico de vendas com iframe Streamlit"""
    pass

def fn_view_atualizar_certificado(i_request):
    """Upload e validação de certificado digital"""
    pass

# Views de autenticação
def fn_view_login(i_request):
    """Autenticação de usuário e criação de sessão"""
    pass

def fn_view_sair(i_request):
    """Logout e destruição de sessão"""
    pass
```

#### APIs JSON: `fn_api_[ação]_[recurso]`
```python
@require_http_methods(['POST'])
@login_required
def fn_api_processar_xml(i_request):
    """Endpoint para processamento assíncrono de XML"""
    
    try:
        lv_xml_file = i_request.FILES.get('xml_file')
        
        if not lv_xml_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Arquivo XML não enviado'
            }, status=400)
        
        lol_carga_xml = ClCargaXml()
        r_ld_resultado = lol_carga_xml.fn_processar_nfe(i_file=lv_xml_file)
        
        return JsonResponse({
            'status': 'success',
            'data': r_ld_resultado
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

### **Classes de Negócio**

#### Padrão: `Cl[NomeDescritivo]`
```python
class ClGdf:
    """
    Classe central de negócios do GDF
    Gerencia autenticação, sessão e controle de acesso
    """
    
    def __init__(self):
        self.Cliente: int = None
        self.Empresas: List[Dict] = []
        self.Groups: List[str] = []
        self.solucoes_acesso: List[Dict] = []
        self.subsolucoes_acesso: List[Dict] = []
    
    def get_dados(self, i_ol_user: User):
        """Carrega dados iniciais do usuário na sessão"""
        pass
    
    def get_solucoes(self) -> List[Dict]:
        """Retorna soluções e subsoluções autorizadas"""
        pass
    
    def get_usuarios(self, i_v_cod_cliente: str) -> List[Dict]:
        """Consulta usuários do cliente"""
        pass
    
    def set_usuario(self, i_ld_dados: Dict) -> User:
        """Cria novo usuário"""
        pass
    
    def upd_usuario(self, i_v_user_id: int, i_ld_dados: Dict) -> User:
        """Atualiza dados do usuário"""
        pass
    
    @staticmethod
    def fn_gerar_token_jwt(i_request, i_ol_user: User, i_v_tipo_relatorio: str = 'Vendas') -> str:
        """Gera token JWT para autenticação no Streamlit (lógica auxiliar)"""
        pass


class ClCargaXml:
    """
    Processamento de arquivos XML de NF-e
    Valida schema, extrai dados e persiste no banco
    """
    
    def __init__(self):
        self.ns = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'cte': 'http://www.portalfiscal.inf.br/cte',
        }
    
    # MÉTODOS CRUD
    def set_nfe_completa(self, i_ld_dados_xml: Dict) -> NFe:
        """Persiste NF-e completa no banco"""
        pass
    
    def get_nfe_por_chave(self, i_v_chave_acesso: str) -> NFe:
        """Consulta NF-e pela chave de acesso"""
        pass
    
    # FUNÇÕES AUXILIARES
    def fn_processar_nfe(self, i_file) -> Dict:
        """Pipeline completo de processamento de NF-e (orquestra CRUD + validações)"""
        pass
    
    def fn_validar_xml_schema(self, i_v_xml_path: str) -> bool:
        """Valida XML contra schema XSD"""
        pass
    
    def _fn_get_text(self, i_element, i_v_path: str, i_v_default: str = '') -> str:
        """Método auxiliar privado para extração de texto XML"""
        pass
```

### **Templates HTML**

#### Arquivos: `[Contexto]_[Recurso].html` ou `Index_[Recurso].html`
```
app/templates/
├── Index_Base.html          # Template base com navbar e scripts
├── Index_Home.html          # Dashboard principal
├── Index_Login.html         # Página de autenticação
│
├── Usuarios/
│   ├── Index_Usuarios.html  # Listagem de usuários
│   ├── Usuarios_ins.html    # Modal de inserção
│   └── Usuarios_upd.html    # Modal de atualização
│
├── Empresas/
│   ├── Index_Empresas.html
│   ├── Empresas_ins.html
│   └── Empresas_upd.html
│
├── Dashboard/
│   ├── Index_Compras.html   # Analytics de compras
│   └── Index_Vendas.html    # Analytics de vendas
│
└── Processamento/
    ├── index_CargaXml.html
    └── index_Reprocessamento.html
```

#### IDs e Classes CSS
```html
<!-- IDs: contexto-acao-elemento -->
<div id="usuarios-modal-inserir">
    <form id="usuarios-form-inserir" method="POST">
        <input id="usuarios-input-username" name="username" />
        <input id="usuarios-input-email" name="email" />
        <button id="usuarios-btn-salvar" type="submit">Salvar</button>
    </form>
</div>

<!-- Classes: funcional ou descritivo -->
<table class="table-usuarios table-striped">
    <thead>
        <tr class="usuarios-header">
            <th>Username</th>
            <th>Email</th>
            <th class="col-acoes">Ações</th>
        </tr>
    </thead>
</table>
```

### **Arquivos Estáticos**

#### CSS: `Style_[Modulo].css`
```
app/static/css/
├── Style_Base.css          # Estilos globais e layout
├── Style_Login.css         # Específico da tela de login
├── Style_Usuarios.css      # Específico do módulo Usuários
├── Style_Empresas.css
├── Style_Dashboard.css
└── Style_CargaXml.css
```

#### JavaScript: `Script_[Modulo].js`
```
app/static/js/
├── Script_Base.js          # Funções globais e helpers
├── Script_Login.js         # Lógica de autenticação
├── Script_Usuarios.js      # CRUD e interações de usuários
├── Script_Empresas.js
├── Script_Dashboard.js
└── Script_CargaXml.js
```

#### Funções JavaScript: `fn_[ação]_[recurso]`
```javascript
// Script_Usuarios.js

/**
 * Carrega dados do usuário para edição
 * @param {string} i_v_user_id - ID do usuário
 */
function fn_carregar_usuario(i_v_user_id) {
    fetch(`/usuarios/${i_v_user_id}/`)
        .then(response => response.json())
        .then(data => fn_preencher_modal(data));
}

/**
 * Preenche modal com dados do usuário
 * @param {Object} i_ld_dados - Dados do usuário
 */
function fn_preencher_modal(i_ld_dados) {
    document.getElementById('usuarios-input-username').value = i_ld_dados.username;
    document.getElementById('usuarios-input-email').value = i_ld_dados.email;
}

/**
 * Valida formulário antes do submit
 * @returns {boolean} r_v_valido - True se válido
 */
function fn_validar_form_usuario() {
    const lv_username = document.getElementById('usuarios-input-username').value;
    const lv_email = document.getElementById('usuarios-input-email').value;
    
    let r_v_valido = true;
    
    if (!lv_username || lv_username.length < 3) {
        fn_exibir_erro('Username deve ter no mínimo 3 caracteres');
        r_v_valido = false;
    }
    
    if (!fn_validar_email(lv_email)) {
        fn_exibir_erro('Email inválido');
        r_v_valido = false;
    }
    
    return r_v_valido;
}
```

---

## 🔐 NOMENCLATURA SENSÍVEL À SEGURANÇA

### **Variáveis de Controle de Acesso**
```python
# Session
sv_cod_cliente = request.session.get('cod_cliente')  # Multi-tenant isolation
sv_user_id = request.session.get('user_id')
sls_solucoes = request.session.get('t_solucoes', [])

# Validação SEMPRE presente
def fn_view_listar_notas_fiscais(i_request):
    sv_cod_cliente = i_request.session.get('cod_cliente')
    
    if not sv_cod_cliente:
        return HttpResponseForbidden('Acesso negado: cliente não identificado')
    
    # Query SEMPRE filtrada por cliente (multi-tenant)
    lsl_notas = NFe.objects.filter(
        empresa__cliente__cod_cliente=sv_cod_cliente
    )
    
    return render(i_request, 'nfe/Index_NFe.html', {'t_notas': lsl_notas})
```

### **Parâmetros Sensíveis (sempre validados)**
```python
def fn_view_atualizar_empresa(i_request, i_v_cod_empresa: str):
    """
    SEGURANÇA: Valida propriedade da empresa pelo cliente
    """
    sv_cod_cliente = i_request.session.get('cod_cliente')
    
    # ✅ IDOR Protection - Verifica propriedade do recurso
    lol_empresa = get_object_or_404(
        Empresas,
        cod_empresa=i_v_cod_empresa,
        cliente__cod_cliente=sv_cod_cliente  # CRÍTICO: filtro multi-tenant
    )
    
    if i_request.method == 'POST':
        # Sanitização de inputs
        lv_razao = i_request.POST.get('razao', '').strip()
        lv_cnpj = re.sub(r'\D', '', i_request.POST.get('cnpj', ''))  # Remove não-dígitos
        
        # Validação
        if not fn_validar_cnpj(lv_cnpj):
            return JsonResponse({'error': 'CNPJ inválido'}, status=400)
        
        # Atualização segura
        lol_empresa.razao = lv_razao
        lol_empresa.cnpj = lv_cnpj
        lol_empresa.save()
        
        return JsonResponse({'status': 'success'})
```

---

## ⚡ NOMENCLATURA ORIENTADA A PERFORMANCE

### **Queries Otimizadas (prefixos indicam otimização)**
```python
def fn_get_usuarios_otimizado(i_v_cod_cliente: str):
    """
    Query otimizada com select_related e prefetch_related
    Reduz N+1 queries
    """
    
    r_lsl_usuarios = User.objects.filter(
        userempresas__empresa__cliente__cod_cliente=i_v_cod_cliente
    ).select_related(
        # 1-to-1 ou ForeignKey direto
        'profile',
    ).prefetch_related(
        # Many-to-Many ou Reverse ForeignKey
        'groups',
        'userempresas_set__empresa',
        'userempresas_set__empresa__cliente'
    ).distinct()
    
    return r_lsl_usuarios


def fn_get_nfe_completa_otimizada(i_v_nfe_id: int):
    """
    Carrega NF-e com TODOS os relacionamentos em 1 query
    """
    
    r_ol_nfe = NFe.objects.select_related(
        'identificacao',
        'total',
        'emitente',
        'destinatario',
        'emitente__endereco',
        'destinatario__endereco',
        'empresa',
        'empresa__cliente'
    ).prefetch_related(
        'nfe_produto_set__icms',
        'nfe_produto_set__ipi',
        'nfe_produto_set__pis',
        'nfe_produto_set__cofins',
        'nfe_pagamento_set',
        'nfe_parcela_set'
    ).get(id=i_v_nfe_id)
    
    return r_ol_nfe
```

### **Paginação (sempre presente em listagens)**
```python
def fn_view_listar_empresas(i_request):
    """Listagem paginada para evitar sobrecarga"""
    
    sv_cod_cliente = i_request.session.get('cod_cliente')
    lv_busca = i_request.GET.get('Buscar', '').strip()
    
    # Query base
    lsl_empresas = Empresas.objects.filter(
        cliente__cod_cliente=sv_cod_cliente
    ).select_related('cliente', 'grp_empresa')
    
    # Filtro de busca
    if lv_busca:
        lsl_empresas = lsl_empresas.filter(
            models.Q(razao__icontains=lv_busca) |
            models.Q(fantasia__icontains=lv_busca) |
            models.Q(cnpj__icontains=lv_busca)
        )
    
    # Paginação (30 itens por página)
    lol_paginator = Paginator(lsl_empresas, 30)
    lv_page_number = i_request.GET.get('page', 1)
    r_ol_page_obj = lol_paginator.get_page(lv_page_number)
    
    return render(i_request, 'empresas/Index_Empresas.html', {
        'page_obj': r_ol_page_obj,
        'buscar': lv_busca
    })
```

---

## 🧪 NOMENCLATURA EM TESTES

### **Arquivos de Teste: `test_[modulo].py`**
```
tests/
├── __init__.py
├── test_models_nfe.py
├── test_views_usuarios.py
├── test_classes_gdf.py
├── test_carga_xml.py
└── test_autenticacao.py
```

### **Funções de Teste: `test_[funcionalidade]_[cenario]`**
```python
# test_views_usuarios.py

class TestUsuariosViews(TestCase):
    def setUp(self):
        """Setup: cria dados de teste"""
        self.lol_cliente = Clientes.objects.create(
            cod_cliente='CLI001',
            razao='Cliente Teste',
            cnpj='12345678000190',
            is_active=True
        )
        
        self.lol_user = User.objects.create_user(
            username='test_user',
            password='test_pass_123'
        )
    
    def test_fn_view_listar_usuarios_sem_autenticacao(self):
        """Deve redirecionar para login se não autenticado"""
        lol_response = self.client.get('/usuarios/')
        
        self.assertEqual(lol_response.status_code, 302)
        self.assertIn('/Login/', lol_response.url)
    
    def test_fn_view_listar_usuarios_com_autenticacao(self):
        """Deve listar usuários do cliente logado"""
        self.client.login(username='test_user', password='test_pass_123')
        
        # Simula sessão
        lol_session = self.client.session
        lol_session['cod_cliente'] = 'CLI001'
        lol_session.save()
        
        lol_response = self.client.get('/usuarios/')
        
        self.assertEqual(lol_response.status_code, 200)
        self.assertIn('t_user', lol_response.context)
    
    def test_fn_view_inserir_usuario_valido(self):
        """Deve criar usuário com dados válidos"""
        self.client.login(username='test_user', password='test_pass_123')
        
        ld_dados_post = {
            'username': 'novo_usuario',
            'email': 'novo@teste.com',
            'first_name': 'Novo',
            'last_name': 'Usuário'
        }
        
        lol_response = self.client.post('/usuario_ins/', ld_dados_post)
        
        self.assertEqual(lol_response.status_code, 302)  # Redirect após sucesso
        self.assertTrue(User.objects.filter(username='novo_usuario').exists())
    
    def test_fn_view_inserir_usuario_duplicado(self):
        """Deve rejeitar username duplicado"""
        User.objects.create_user(username='existente', password='pass123')
        
        self.client.login(username='test_user', password='test_pass_123')
        
        ld_dados_post = {
            'username': 'existente',  # Já existe
            'email': 'outro@teste.com',
        }
        
        lol_response = self.client.post('/usuario_ins/', ld_dados_post)
        
        # Deve retornar erro
        self.assertIn('error', lol_response.context)
```

---

## 📊 NOMENCLATURA EM QUERIES COMPLEXAS

### **Agregações e Anotações**
```python
from django.db.models import Count, Sum, Avg, Q, F

def fn_get_estatisticas_nfe_por_empresa(i_v_cod_cliente: str):
    """
    Retorna estatísticas agregadas de NF-e por empresa
    Performance: 1 query com GROUP BY
    """
    
    r_lsl_stats = Empresas.objects.filter(
        cliente__cod_cliente=i_v_cod_cliente
    ).annotate(
        # Contadores
        total_nfe=Count('nfe', distinct=True),
        total_nfe_entrada=Count('nfe', filter=Q(nfe__identificacao__tipo_nf=0)),
        total_nfe_saida=Count('nfe', filter=Q(nfe__identificacao__tipo_nf=1)),
        
        # Valores monetários
        valor_total_entradas=Sum(
            'nfe__total__valor_nf',
            filter=Q(nfe__identificacao__tipo_nf=0)
        ),
        valor_total_saidas=Sum(
            'nfe__total__valor_nf',
            filter=Q(nfe__identificacao__tipo_nf=1)
        ),
        
        # Médias
        valor_medio_nfe=Avg('nfe__total__valor_nf'),
    ).values(
        'cod_empresa',
        'razao',
        'fantasia',
        'total_nfe',
        'total_nfe_entrada',
        'total_nfe_saida',
        'valor_total_entradas',
        'valor_total_saidas',
        'valor_medio_nfe'
    )
    
    return r_lsl_stats
```

---

## 🎨 CASOS ESPECIAIS E EXCEÇÕES

### **Django Framework (manter convenções originais)**
```python
# ✅ CORRETO - Convenções Django
class Meta:
    managed = True
    db_table = '"nfe"."nfe_emitente"'
    ordering = ['-data_criacao']

def __str__(self):
    return f"{self.cod_empresa} - {self.razao}"

def save(self, *args, **kwargs):
    # Custom save logic
    super().save(*args, **kwargs)

# ✅ CORRETO - Métodos especiais Python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

def __repr__(self):
    return f"<ClGdf(cliente={self.Cliente})>"
```

### **Constants (uppercase snake_case)**
```python
# settings.py ou constantes de módulo
DATABASE_TIMEOUT = 30
MAX_UPLOAD_SIZE_MB = 50
XML_ALLOWED_EXTENSIONS = ('.xml', '.zip')

# Em classes
class StatusNFe:
    AUTORIZADA = '100'
    CANCELADA = '101'
    DENEGADA = '302'
    
    CHOICES = [
        (AUTORIZADA, 'Autorizada'),
        (CANCELADA, 'Cancelada'),
        (DENEGADA, 'Denegada'),
    ]
```

### **Enums e Choices**
```python
from django.db import models

class TipoNFe(models.TextChoices):
    ENTRADA = '0', 'Entrada'
    SAIDA = '1', 'Saída'

class ModalidadeFreteNFe(models.TextChoices):
    EMITENTE = '0', 'Por conta do emitente'
    DESTINATARIO = '1', 'Por conta do destinatário'
    TERCEIROS = '2', 'Por conta de terceiros'
    SEM_FRETE = '9', 'Sem frete'

# Uso nos models
class NFe_Identificacao(models.Model):
    tipo_nf = models.CharField(
        max_length=1,
        choices=TipoNFe.choices,
        default=TipoNFe.SAIDA
    )
```

---

## ✅ CHECKLIST DE AUTOCORREÇÃO

Antes de commitar código, validar:

### **1. Variáveis**
- [ ] Todas as variáveis têm prefixo de escopo (`g`, `l`, `s`)?
- [ ] Todas as variáveis têm prefixo de tipo (`v`, `lsl`, `ol`, `ld`)?
- [ ] Parâmetros de função têm prefixo `i_`?
- [ ] Variáveis de retorno têm prefixo `r_`?

### **2. Funções e Métodos**
- [ ] Funções têm prefixo `fn_`?
- [ ] Views Django têm prefixo `fn_view_`?
- [ ] APIs têm prefixo `fn_api_`?
- [ ] Métodos privados têm prefixo `_fn_`?

### **3. Classes**
- [ ] Classes de negócio têm prefixo `Cl`?
- [ ] Models Django seguem convenção PascalCase?
- [ ] Classes têm docstrings descritivas?

### **4. Segurança**
- [ ] Toda query multi-tenant filtra por `cod_cliente`?
- [ ] Inputs do usuário são validados e sanitizados?
- [ ] CSRF protection está ativo em forms?
- [ ] Queries usam `select_related`/`prefetch_related` quando aplicável?

### **5. Performance**
- [ ] Listagens têm paginação?
- [ ] Queries complexas usam `.only()` ou `.defer()` quando aplicável?
- [ ] Evitado N+1 queries?
- [ ] Índices criados para campos frequentemente filtrados?

---

## 📚 EXEMPLOS COMPLETOS

### **Exemplo 1: View CRUD Completo**
```python
# views.py

@login_required(login_url='Login')
def fn_view_listar_empresas(i_request):
    """
    Lista empresas do cliente com busca e paginação
    
    GET Params:
        - Buscar: Termo de busca (razão, fantasia, CNPJ)
        - page: Número da página
    """
    sv_cod_cliente = i_request.session.get('cod_cliente')
    
    if not sv_cod_cliente:
        return HttpResponseForbidden('Acesso negado')
    
    lv_busca = i_request.GET.get('Buscar', '').strip()
    
    # Query otimizada
    lsl_empresas = Empresas.objects.filter(
        cliente__cod_cliente=sv_cod_cliente
    ).select_related('cliente', 'grp_empresa', 'cert')
    
    if lv_busca:
        lsl_empresas = lsl_empresas.filter(
            models.Q(razao__icontains=lv_busca) |
            models.Q(fantasia__icontains=lv_busca) |
            models.Q(cnpj__icontains=lv_busca)
        )
    
    # Paginação
    lol_paginator = Paginator(lsl_empresas, 30)
    lv_page_number = i_request.GET.get('page', 1)
    r_ol_page_obj = lol_paginator.get_page(lv_page_number)
    
    return render(i_request, 'empresas/Index_Empresas.html', {
        'page_obj': r_ol_page_obj,
        'buscar': lv_busca
    })


@login_required(login_url='Login')
@require_http_methods(['POST'])
def fn_view_inserir_empresa(i_request):
    """Insere nova empresa via modal"""
    
    sv_cod_cliente = i_request.session.get('cod_cliente')
    
    if not sv_cod_cliente:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    try:
        # Extração e sanitização
        lv_razao = i_request.POST.get('razao', '').strip()
        lv_fantasia = i_request.POST.get('fantasia', '').strip()
        lv_cnpj = re.sub(r'\D', '', i_request.POST.get('cnpj', ''))
        lv_ie = i_request.POST.get('ie', '').strip()
        lv_tipo = i_request.POST.get('tipo', 'F')
        
        # Validações
        if not lv_razao or len(lv_razao) < 3:
            return JsonResponse({'error': 'Razão social inválida'}, status=400)
        
        if not fn_validar_cnpj(lv_cnpj):
            return JsonResponse({'error': 'CNPJ inválido'}, status=400)
        
        # Verifica duplicidade
        if Empresas.objects.filter(cnpj=lv_cnpj).exists():
            return JsonResponse({'error': 'CNPJ já cadastrado'}, status=400)
        
        # Geração de código único
        lv_cod_empresa = fn_gerar_codigo_empresa(i_v_cod_cliente=sv_cod_cliente)
        
        # Busca cliente
        lol_cliente = get_object_or_404(Clientes, cod_cliente=sv_cod_cliente)
        
        # Criação com transaction
        with transaction.atomic():
            lol_empresa = Empresas.objects.create(
                cod_empresa=lv_cod_empresa,
                razao=lv_razao,
                fantasia=lv_fantasia,
                cnpj=lv_cnpj,
                ie=lv_ie,
                tipo=lv_tipo,
                cliente=lol_cliente
            )
        
        return JsonResponse({
            'status': 'success',
            'empresa_id': lol_empresa.cod_empresa,
            'message': 'Empresa criada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao criar empresa: {str(e)}'
        }, status=500)


@login_required(login_url='Login')
def fn_view_atualizar_empresa(i_request, i_v_cod_empresa: str):
    """
    GET: Retorna dados da empresa em JSON
    POST: Atualiza empresa
    """
    sv_cod_cliente = i_request.session.get('cod_cliente')
    
    # IDOR Protection
    lol_empresa = get_object_or_404(
        Empresas,
        cod_empresa=i_v_cod_empresa,
        cliente__cod_cliente=sv_cod_cliente
    )
    
    if i_request.method == 'GET':
        # Serialização manual (ou usar DRF serializer)
        r_ld_empresa = {
            'cod_empresa': lol_empresa.cod_empresa,
            'razao': lol_empresa.razao,
            'fantasia': lol_empresa.fantasia,
            'cnpj': lol_empresa.cnpj,
            'ie': lol_empresa.ie,
            'tipo': lol_empresa.tipo,
            'matriz': lol_empresa.matriz,
        }
        return JsonResponse(r_ld_empresa)
    
    elif i_request.method == 'POST':
        try:
            # Atualização
            lol_empresa.razao = i_request.POST.get('razao', '').strip()
            lol_empresa.fantasia = i_request.POST.get('fantasia', '').strip()
            lol_empresa.ie = i_request.POST.get('ie', '').strip()
            lol_empresa.tipo = i_request.POST.get('tipo', 'F')
            
            lol_empresa.save()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
```

### **Exemplo 2: Classe de Negócio Completa**
```python
# app/classes/gdf.py

from typing import List, Dict, Optional
from django.contrib.auth.models import User
import jwt

class ClGdf:
    """
    Classe central de negócios do sistema GDF
    
    Responsabilidades:
        - Gerenciamento de sessão e autenticação
        - Controle de acesso (soluções e subsoluções)
        - Geração de tokens JWT para dashboards
        - Queries de dados filtradas por multi-tenancy
    """
    
    def __init__(self):
        self.Cliente: Optional[Clientes] = None
        self.Empresas: List[Empresas] = []
        self.Groups: List[Group] = []
        self.solucoes_acesso: List[SolucoesAcesso] = []
        self.subsolucoes_acesso: List[SubsolucoesAcesso] = []
    
    def get_dados(self, i_ol_user: User) -> bool:
        """
        Carrega dados iniciais do usuário na instância
        
        Args:
            i_ol_user: Objeto User Django autenticado
        
        Returns:
            r_v_sucesso: True se dados carregados, False se erro
        """
        try:
            # Empresas do usuário (via UserEmpresas)
            self.Empresas = Empresas.objects.filter(
                userempresas__user=i_ol_user
            ).select_related('cliente', 'grp_empresa').distinct()
            
            # Grupos de permissão
            self.Groups = Group.objects.filter(user=i_ol_user)
            
            # Cliente (assumindo 1 cliente por usuário)
            self.Cliente = Clientes.objects.filter(
                empresas__in=self.Empresas
            ).distinct().first()
            
            if not self.Cliente:
                return False
            
            # Soluções autorizadas para o cliente
            self.solucoes_acesso = SolucoesAcesso.objects.filter(
                cliente=self.Cliente,
                is_active=True
            ).select_related('solucao')
            
            # Subsoluções autorizadas via grupo do usuário
            self.subsolucoes_acesso = SubsolucoesAcesso.objects.filter(
                group__in=self.Groups
            ).select_related('subsolucao', 'subsolucao__solucao')
            
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            return False
    
    def get_solucoes(self) -> List[Dict]:
        """
        Retorna estrutura hierárquica de soluções e subsoluções autorizadas
        
        Returns:
            r_lsl_solucoes: Lista com dicionários {solucao, sub_solucoes[]}
        """
        if not self.solucoes_acesso or not self.subsolucoes_acesso:
            return []
        
        r_lsl_solucoes = []
        
        # Itera soluções autorizadas
        for lol_solucao_acesso in self.solucoes_acesso:
            lol_solucao = lol_solucao_acesso.solucao
            
            # Busca subsoluções desta solução
            lsl_subsolucoes_filtradas = [
                {
                    'cod_subsolucao': sub.subsolucao.cod_subsolucao,
                    'descricao': sub.subsolucao.descricao,
                    'url': sub.subsolucao.url,
                    'icon': sub.subsolucao.icon,
                }
                for sub in self.subsolucoes_acesso
                if sub.subsolucao.solucao == lol_solucao
            ]
            
            if lsl_subsolucoes_filtradas:
                r_lsl_solucoes.append({
                    'cod_solucao': lol_solucao.cod_solucao,
                    'descricao': lol_solucao.descricao,
                    'sub_solucoes': lsl_subsolucoes_filtradas
                })
        
        return r_lsl_solucoes
    
    @staticmethod
    def fn_gerar_token_jwt(
        i_request,
        i_ol_user: User,
        i_v_tipo_relatorio: str = 'Vendas'
    ) -> Optional[str]:
        """
        Gera token JWT para autenticação em dashboards Streamlit
        
        Args:
            i_request: Requisição Django (para extrair session)
            i_ol_user: Usuário autenticado
            i_v_tipo_relatorio: Tipo do dashboard ('Vendas' ou 'Compras')
        
        Returns:
            r_v_token: Token JWT codificado (válido por 30 minutos)
        """
        if not i_ol_user.is_active:
            return None
        
        ld_payload = {
            'user_id': i_ol_user.id,
            'username': i_ol_user.username,
            'tipo_relatorio': i_v_tipo_relatorio,
            'iat': timezone.now(),
            'exp': timezone.now() + timedelta(minutes=30),
        }
        
        r_v_token = jwt.encode(
            ld_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        return r_v_token
    
    def get_usuarios(self, i_v_cod_cliente: str) -> List[Dict]:
        """
        Retorna usuários do cliente com empresas vinculadas
        
        Args:
            i_v_cod_cliente: Código do cliente (multi-tenant filter)
        
        Returns:
            r_lsl_usuarios: Lista de dicionários com dados serializados
        """
        # Query otimizada
        lsl_users = User.objects.filter(
            userempresas__empresa__cliente__cod_cliente=i_v_cod_cliente
        ).select_related(
            'userempresas__empresa'
        ).prefetch_related(
            'groups',
            'userempresas_set__empresa__cliente'
        ).distinct()
        
        # Serialização manual
        r_lsl_usuarios = []
        for lol_user in lsl_users:
            lsl_empresas_vinculadas = [
                emp.empresa.fantasia or emp.empresa.razao
                for emp in lol_user.userempresas_set.all()
            ]
            
            lsl_grupos = [grp.name for grp in lol_user.groups.all()]
            
            r_lsl_usuarios.append({
                'id': lol_user.id,
                'username': lol_user.username,
                'email': lol_user.email,
                'first_name': lol_user.first_name,
                'last_name': lol_user.last_name,
                'is_active': lol_user.is_active,
                'empresas': ', '.join(lsl_empresas_vinculadas),
                'grupos': ', '.join(lsl_grupos),
                'date_joined': lol_user.date_joined.strftime('%d/%m/%Y %H:%M')
            })
        
        return r_lsl_usuarios
```

---

## 🚀 CONCLUSÃO

Este workbook define o **padrão oficial de nomenclatura do projeto GDF_V2**. Toda refatoração, nova feature ou correção deve seguir estas diretrizes.

### **Benefícios Imediatos**
1. **Legibilidade**: Qualquer desenvolvedor identifica escopo e tipo de variável instantaneamente
2. **Segurança**: Prefixos obrigam validação explícita de inputs (`i_`) e outputs (`r_`)
3. **Performance**: Nomenclatura de queries evidencia otimizações (ou falta delas)
4. **Manutenibilidade**: Código autodocumentado reduz necessidade de comentários excessivos
5. **Debugging**: Rastreamento de fluxo facilitado pelos prefixos de input/retorno

### **Comando para Validação Automática**
```bash
# TODO: Criar script de linting customizado
python manage.py validate_nomenclature --fix
```

---

**Última Atualização**: 30/01/2026  
**Versão**: 1.0  
**Responsável**: Arquitetura de Software GDF_V2
