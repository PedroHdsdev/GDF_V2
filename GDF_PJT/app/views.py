from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts               import get_object_or_404, render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from app.decorators                 import validate_idor_empresa, validate_idor_usuario, validate_session_required
from django.views.decorators.http   import require_http_methods
from django.conf                    import settings
from django.contrib                 import messages
from app.classes.gdf                import ClGdf
from app.classes.CargaXml           import Carga_xml
from django.core.paginator          import Paginator
from app.db_GDF.Public.models       import UserEmpresas, Empresas
import re

def fn_view_login(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password') 

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            cl_gdf_instance = ClGdf()
            cl_gdf_instance.get_dados(request.user) 

            if not cl_gdf_instance.Retorn:
                #buscar solucoes que tem acessos 
                solucoes = cl_gdf_instance.get_solucoes()
                if solucoes:
                    request.session['t_solucoes']  = solucoes
                    request.session['cod_cliente'] = cl_gdf_instance.Cliente.cod_cliente

                    return render(request, 'Index_Home.html')
                else:
                    return render(request, 'Index_Login.html', {'error_message': 'Problema de Acesso.'})  
            return redirect('Home')   
        else:
            return render(request, 'Index_Login.html', {'error_message': 'Usuário ou senha inválidos.'})

    return render(request, 'Index_Login.html')

def fn_view_obter_subsolucao(request, cod_sub): 
    if request.user.is_authenticated:

        solucoes = request.session.get('t_solucoes', [])

        for sol in solucoes:
            for sub in sol.get('sub_solucoes', []):
                if str(sub.get('cod_subsolucao')) == str(cod_sub):
                    return redirect(sub.get('cod_subsolucao'))

        return render(request, 'index_home.html')

    return render(request, 'index_login.html')

@login_required(login_url='Login')
def fn_view_home(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            codigo = request.POST.get('codigo')
            
            if codigo:
                return redirect(codigo)
            
        return render(request, "Index_Home.html")
    return render(request, 'Index_Login.html')

@login_required
def fn_view_sair(request):   
    logout(request)
    return redirect('Login')

#--------------------------------------------------------------------
#       Sub-soluções Views (Administração)
#--------------------------------------------------------------------
# Usuarios
@login_required(login_url='Login')
def fn_view_listar_usuarios(request):
    cod_cliente = request.session.get('cod_cliente', None)
    
    # Validar se usuário tem acesso a cliente
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Acesso negado: cliente não identificado'})
    
    # Buscar dados APENAS uma vez - carregamento inicial da página
    cl_gdf = ClGdf()
    t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)

    # ✅ Passar dados brutos para o template
    # Paginação e busca serão feitas em JavaScript no cliente
    return render(
        request,
        'usuarios/Index_Usuarios.html',
        {
            't_user': t_user,         
        }
    )

# Empresas
@login_required(login_url='Login')
def fn_view_listar_empresas(request): 
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return redirect('Login')
    
    cl_gdf = ClGdf()

    # Buscar todas as empresas - paginação será feita em JavaScript
    t_empresas = cl_gdf.get_empresas(i_v_cod_cliente=cod_cliente)
    
    return render(
        request,
        'Empresas/Index_Empresas.html',
        {
            't_empresas': t_empresas
        }
    )

# Clientes
@login_required(login_url='Login')
def fn_view_listar_clientes(request): 
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return redirect('Login')
    
    cl_gdf = ClGdf()
    
    t_clientes = cl_gdf.get_clientes()

    return render(
        request,
        'Clientes/Index_Clientes.html',
        {
            't_clientes': t_clientes
        }
    )

#--------------------------------------------------------------------
#       Modais Views
#--------------------------------------------------------------------
@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_inserir_usuario(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        # ✅ Retorna dados para preencher o modal
        return JsonResponse(cl_gdf.get_usuario_dados_ins(i_v_cod_cliente=cod_cliente))

    if request.method == "POST":
        # ✅ Extrair dados do formulário
        username        = request.POST.get("username", "").strip()
        first_name      = request.POST.get("first_name", "").strip()
        last_name       = request.POST.get("last_name", "").strip()
        email           = request.POST.get("email", "").strip()
        password        = request.POST.get("password", "").strip()
        password_conf   = request.POST.get("password_confirm", "").strip()
        empresas_str    = request.POST.get("ls_empresas", "").strip()
        grupos_str      = request.POST.get("ls_grupos", "").strip()

        # ✅ Validações básicas (frontend já valida, mas revalidamos no backend)
        errors = []
        
        if not username:
            errors.append("Username é obrigatório")
        if not email:
            errors.append("Email é obrigatório")
        if not password:
            errors.append("Senha é obrigatória")
        if password != password_conf:
            errors.append("Senhas não conferem")
        if not empresas_str:
            errors.append("Selecione pelo menos 1 empresa")
        if not grupos_str:
            errors.append("Selecione pelo menos 1 grupo")
        
        if errors:
            t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
            return render(request, 'Usuarios/Index_Usuarios.html', {
                't_user': t_user,
                'error_message': ' | '.join(errors)
            })
        
        # ✅ Chamar método de inserção na classe
        resultado = cl_gdf.set_usuario(
            i_v_username=username,
            i_v_email=email,
            i_v_password=password,
            i_v_first_name=first_name,
            i_v_last_name=last_name,
            i_lsl_empresas_ids=empresas_str,  # "1,2,3"
            i_lsl_grupos_ids=grupos_str,      # "4,5,6"
            i_v_cod_cliente=cod_cliente
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
            return render(request, 'Usuarios/Index_Usuarios.html', {
                't_user': t_user,
                'error_message': resultado.get("message", "Erro ao criar usuário")
            })
        
        # ✅ Sucesso! Redirecionar com mensagem
        return redirect('Dm_Usuarios')

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_usuario(request, user_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    # ✅ VALIDAR IDOR: User só pode editar usuários de suas empresas
    user_belongs_to_client = UserEmpresas.objects.filter(
        user_id=user_id,
        empresa__cliente__cod_cliente=cod_cliente
    ).exists()
    
    if not user_belongs_to_client:
        return JsonResponse({"erro": "Acesso negado: usuário não pertence ao seu cliente"}, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        # Retornar dados do usuário em JSON (para modal)
        data = cl_gdf.get_usuario_upd(i_v_user_id=int(user_id), i_v_cod_cliente=cod_cliente)
        if not data or data.get('erro'):
            return JsonResponse({"erro": "Usuário não encontrado"}, status=404)

        return JsonResponse(data)

    elif request.method == "POST":
        # ✅ Validações de campos obrigatórios
        first_name  = request.POST.get("upd_first_name", "").strip()
        last_name   = request.POST.get("upd_last_name", "").strip()
        email       = request.POST.get("upd_email", "").strip()
        is_active   = request.POST.get("upd_is_active") == "on"

        empresas_str = request.POST.get("ls_empresas", "")
        empresa_ids = [e.strip() for e in empresas_str.split(",") if e.strip()]

        # ✅ Processar grupos: podem vir como string separada por vírgula do hidden input
        grupos_str = request.POST.get("ls_grupos", "")
        grupo_ids = [int(g.strip()) for g in grupos_str.split(",") if g.strip()]

        # ✅ Validações básicas antes de chamar método
        if not email:
            return JsonResponse({"erro": "Email obrigatório"}, status=400)
        if not empresa_ids:
            return JsonResponse({"erro": "Selecione pelo menos 1 empresa"}, status=400)
        if not grupo_ids:
            return JsonResponse({"erro": "Selecione pelo menos 1 grupo"}, status=400)

        resultado = cl_gdf.upd_usuario(
            i_v_user_id=int(user_id),
            i_v_first_name=first_name,
            i_v_last_name=last_name,
            i_v_email=email,
            i_v_is_active=is_active,
            i_lsl_empresa_ids=empresa_ids,
            i_lsl_grupo_ids=grupo_ids,
            i_v_cod_cliente=cod_cliente
        )
        
        # ✅ Detectar se é requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            mensagem = resultado.get("message", "Erro ao atualizar")
            if is_ajax:
                return JsonResponse({"success": False, "message": mensagem}, status=400)
            else:
                messages.error(request, mensagem, extra_tags='MODAL_UPD')
                return redirect('Dm_Usuarios')
        
        mensagem = resultado.get("message", "Usuário atualizado com sucesso!")
        if is_ajax:
            return JsonResponse({"success": True, "message": mensagem}, status=200)
        else:
            messages.success(request, mensagem, extra_tags='MODAL_UPD')
            return redirect('Dm_Usuarios')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)
    
#--------------------------------------------------------------------
#       Sub-soluções Views (Dashboard)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def fn_view_dashboard_vendas(request):   
    token = ClGdf.gerar_token(request, request.user, tipo_relatorio='Vendas')
    if not token:
        return render(request, 'Index_Login.html', {'error_message': 'Erro ao gerar token de acesso'})
    return render(request, "Dashboard/Index_Vendas.html", {"token": token })

@login_required(login_url='Login')
def fn_view_dashboard_compras(request):   
    token = ClGdf.gerar_token(request, request.user, tipo_relatorio='Compras')
    if not token:
        return render(request, 'Index_Login.html', {'error_message': 'Erro ao gerar token de acesso'})
    return render(request, "Dashboard/Index_Compras.html", {"token": token })

#--------------------------------------------------------------------
#       Sub-soluções Views (Manifesto)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def fn_view_manifesto_painel(request):
    manifesto_data = {
        "notas": [
            {
                "id": "NFE-2026-0001",
                "tipo": "NFe",
                "numero": "15432",
                "serie": "001",
                "emissao": "2026-02-10 09:22",
                "emitente": "Industrias Atlas",
                "destinatario": "Supermercado Central",
                "valor": "152340.80",
                "status": "AUTORIZADA",
                "documentos": [
                    {
                        "tipo": "COMPRA",
                        "numero": "4500012391",
                        "data": "2026-02-10",
                        "status": "CRIADO",
                        "itens": [
                            {"seq": 10, "nfe_item_seq": 1, "material": "MAT-1001", "descricao": "Acucar cristal", "qtd": "100", "un": "KG", "valor": "3400.00"},
                            {"seq": 20, "nfe_item_seq": 2, "material": "MAT-2004", "descricao": "Leite integral", "qtd": "220", "un": "CX", "valor": "6600.00"},
                        ],
                    },
                    {
                        "tipo": "MIRO",
                        "numero": "5100004890",
                        "data": "2026-02-10",
                        "status": "PENDENTE",
                        "itens": [
                            {"seq": 10, "nfe_item_seq": 1, "material": "MAT-1001", "descricao": "Acucar cristal", "qtd": "100", "un": "KG", "valor": "3400.00"},
                        ],
                    },
                ],
                "itens": [
                    {"seq": 1, "codigo": "7891001", "descricao": "Acucar cristal 5kg", "qtd": "100", "un": "KG", "valor": "3400.00"},
                    {"seq": 2, "codigo": "7892004", "descricao": "Leite integral 1L", "qtd": "220", "un": "CX", "valor": "6600.00"},
                    {"seq": 3, "codigo": "7893011", "descricao": "Cafe torrado 500g", "qtd": "80", "un": "CX", "valor": "4200.00"},
                ],
            },
            {
                "id": "CTE-2026-0102",
                "tipo": "CTe",
                "numero": "8851",
                "serie": "002",
                "emissao": "2026-02-09 16:08",
                "emitente": "Logistica Norte",
                "destinatario": "Farmacia Vida",
                "valor": "19800.00",
                "status": "EM_ANALISE",
                "documentos": [
                    {
                        "tipo": "MIGO",
                        "numero": "4900007712",
                        "data": "2026-02-09",
                        "status": "CRIADO",
                        "itens": [
                            {"seq": 10, "nfe_item_seq": 1, "material": "FRETE", "descricao": "Servico de transporte", "qtd": "1", "un": "SV", "valor": "19800.00"},
                        ],
                    }
                ],
                "itens": [
                    {"seq": 1, "codigo": "FRETE", "descricao": "Servico de transporte", "qtd": "1", "un": "SV", "valor": "19800.00"},
                ],
            },
            {
                "id": "NFSE-2026-0431",
                "tipo": "NFSe",
                "numero": "431",
                "serie": "A1",
                "emissao": "2026-02-08 11:45",
                "emitente": "Tech Servicios",
                "destinatario": "Industria Nova",
                "valor": "4520.50",
                "status": "PENDENTE",
                "documentos": [],
                "itens": [
                    {"seq": 1, "codigo": "SVC-100", "descricao": "Suporte mensal", "qtd": "1", "un": "SV", "valor": "4520.50"},
                ],
            },
        ]
    }

    return render(request, "Manifesto/Index_Manifesto.html", {"manifesto_data": manifesto_data})

#--------------------------------------------------------------------
#       Empresas - Modais
#--------------------------------------------------------------------
@login_required(login_url='Login')
@require_http_methods(["GET","POST"])
def fn_view_inserir_empresa(request):
    """Inserir nova empresa"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        data = cl_gdf.get_empresa_dados_ins(i_v_cod_cliente=cod_cliente)
        return JsonResponse(data)  
    
    elif request.method == "POST":
        # ✅ Extrair dados do formulário
        cod_empresa = request.POST.get("m_codempresa", "").strip()
        razao = request.POST.get("m_razao", "").strip()
        cnpj = request.POST.get("m_cnpj", "").strip()
        cnpj = re.sub(r"\D", "", cnpj)
        fantasia = request.POST.get("m_fantasia", "").strip()
        grp_empresa = request.POST.get("ls_grpempresas", "").strip()
        matriz = request.POST.get("m_matriz") == "on"
        ie = request.POST.get("m_ie", "").strip()
        im = request.POST.get("m_im", "").strip()
        iest = request.POST.get("m_iest", "").strip()
        crt = request.POST.get("m_crt", "").strip()
        cnae = request.POST.get("m_cnae", "").strip()
        suframa = request.POST.get("m_suframa", "").strip()
        chave_acesso = request.POST.get("m_chave_acesso", "").strip()

        # ✅ Validações básicas (frontend já valida, mas revalidamos no backend)
        errors = []
        
        if not cod_empresa:
            errors.append("Código da empresa é obrigatório")
        if not razao:
            errors.append("Razão social é obrigatória")
        if not cnpj:
            errors.append("CNPJ é obrigatório")
        if not fantasia:
            errors.append("Fantasia é obrigatória")
        if not grp_empresa:
            errors.append("Grupo de empresa é obrigatório")
        
        if errors:
            return JsonResponse({"erro": " | ".join(errors)}, status=400)
        
        # ✅ Chamar método de inserção na classe com cod_cliente para validação IDOR
        resultado = cl_gdf.set_empresa(
            i_v_cod_empresa=cod_empresa,
            i_v_razao=razao,
            i_v_cnpj=cnpj,
            i_v_fantasia=fantasia,
            i_v_grp_empresa=grp_empresa,
            i_v_cod_cliente=cod_cliente,
            i_b_matriz=matriz,
            i_v_ie=ie,
            i_v_im=im,
            i_v_iest=iest,
            i_v_crt=crt,
            i_v_cnae=cnae,
            i_v_suframa=suframa,
            i_v_chave_acesso=chave_acesso
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            return JsonResponse({"erro": resultado.get("message")}, status=400)

        return redirect('Dm_Empresas')

@login_required(login_url='Login')
@validate_idor_empresa
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_empresa(request, cod_empresa):
    """Atualizar empresa existente"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        # Retornar dados da empresa para popular o modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            empresa_data = cl_gdf.get_empresa_upd(
                i_v_cod_empresa=cod_empresa,
                i_v_cod_cliente=cod_cliente
            )
            return JsonResponse(empresa_data)
        else:
            return JsonResponse({"erro": "Requisição inválida"}, status=400)
    
    elif request.method == "POST":  
        # Atualizar dados da empresa
        razao = request.POST.get("m_razao", "").strip()
        fantasia = request.POST.get("m_fantasia", "").strip()
        ie = request.POST.get("m_ie", "").strip()
        im = request.POST.get("m_im", "").strip()
        iest = request.POST.get("m_iest", "").strip()
        crt = request.POST.get("m_crt", "").strip()
        cnae = request.POST.get("m_cnae", "").strip()
        suframa = request.POST.get("m_suframa", "").strip()
        grp_empresa = request.POST.get("m_grpEmpresa_id", "").strip()
        chave_acesso = request.POST.get("m_chave_acesso", "").strip()
        matriz = request.POST.get("m_matriz") == "on"
        
        resultado = cl_gdf.upd_empresa(
            i_v_cod_empresa=cod_empresa,
            i_v_razao=razao,
            i_v_fantasia=fantasia,
            i_v_ie=ie,
            i_v_im=im,
            i_v_iest=iest,
            i_v_crt=crt,
            i_v_cnae=cnae,
            i_v_suframa=suframa,
            i_v_grp_empresa=grp_empresa,
            i_v_chave_acesso=chave_acesso,
            i_b_matriz=matriz,
            i_v_cod_cliente=cod_cliente
        )
        
        # ✅ Detectar se é requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not resultado.get("success"):
            mensagem = resultado.get("message", "Erro ao atualizar")
            if is_ajax:
                return JsonResponse({"success": False, "message": mensagem}, status=400)
            else:
                messages.error(request, mensagem, extra_tags='MODAL_UPD')
                return redirect('Dm_Empresas')
        else:
            mensagem = resultado.get("message", "Empresa atualizada com sucesso!")
            if is_ajax:
                return JsonResponse({"success": True, "message": mensagem}, status=200)
            else:
                messages.success(request, mensagem, extra_tags='MODAL_UPD')
                return redirect('Dm_Empresas')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)

@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_view_atualizar_certificado(request):
    """Atualizar certificado digital da empresa"""
    
    cl_gdf = ClGdf()
    
    cod_empresa = request.POST.get('m_codempresa', '').strip()

    # ✅ Pegar arquivo (OPCIONAL - pode atualizar só metadados)
    cert_file = request.FILES.get('m_file')
    
    # ✅ Validar extensão só se arquivo foi enviado
    if cert_file and not cert_file.name.endswith(('.crt', '.txt')):
        messages.error(request, "Formato inválido. Use .crt ou .txt", extra_tags='MODAL_UPD')
        return redirect('Dm_Empresas')
    
    # ✅ Extrair dados adicionais do certificado
    emissor = request.POST.get('m_emissor', '').strip()
    cnpj = request.POST.get('m_cnpj', '').strip()
    dt_inicial = request.POST.get('m_dt_inicial', '').strip()
    dt_fim = request.POST.get('m_dt_fim', '').strip()
    
    # ✅ Se nenhum dado foi enviado, erro
    if not cert_file and not (emissor or cnpj or dt_inicial or dt_fim):
        messages.error(request, "Selecione um arquivo ou preencha os dados do certificado", extra_tags='MODAL_UPD')
        return redirect('Dm_Empresas')
    
    # Chamar método de atualização de certificado
    resultado = cl_gdf.upd_certificado(
        i_v_arquivo_cert=cert_file,
        i_v_emissor=emissor,
        i_v_cpf_cnpj=cnpj,
        i_v_ini_validade=dt_inicial,
        i_v_fim_validade=dt_fim,
        i_v_cod_empresa=cod_empresa
    )
    
    if resultado.get("success"):
        messages.success(request, resultado.get("message", "Certificado atualizado!"), extra_tags='MODAL_UPD')
    else:
        messages.error(request, resultado.get("message", "Erro ao atualizar certificado"), extra_tags='MODAL_UPD')
    
    return redirect('Dm_Empresas')
#--------------------------------------------------------------------
#       Clientes - Modais
#--------------------------------------------------------------------
@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_inserir_cliente(request):
    """Inserir novo cliente - seguindo padrão Usuario_ins"""
    cl_gdf = ClGdf()
    if request.method == "GET":
        # Retornar dados para preencher o modal (opcionalmente listas de soluções, etc)
        return JsonResponse({"success": True})

    elif request.method == "POST":
        # ✅ Extrair dados do formulário
        cliente_id = request.POST.get("m_cliente_id", "").strip()
        razao = request.POST.get("m_razao", "").strip()
        cnpj = request.POST.get("m_cnpj", "").strip()
        cnpj = re.sub(r"\D", "", cnpj)

        # ✅ Validações básicas
        if not cliente_id:
            return JsonResponse({"erro": "Código do cliente é obrigatório"}, status=400)
        if not razao:
            return JsonResponse({"erro": "Razão social é obrigatória"}, status=400)
        if not cnpj:
            return JsonResponse({"erro": "CNPJ é obrigatório"}, status=400)
        
        # ✅ Chamar método de inserção na classe
        resultado = cl_gdf.set_cliente(
            i_cliente=cliente_id,
            i_razao=razao,
            i_cnpj=cnpj
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            messages.error(request, resultado.get("message", "Erro ao criar cliente"), extra_tags='MODAL_INS')
        else:
            messages.success(request, resultado.get("message", "Cliente cadastrado!"), extra_tags='MODAL_INS')

        return redirect('Dm_Clientes')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_cliente(request, cod_cliente):
    """Atualizar cliente existente - seguindo padrão Usuario_upd"""
    cod_cliente_sessao = request.session.get('cod_cliente', None)
    if not cod_cliente_sessao:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    # ✅ VALIDAÇÃO IDOR: cliente só pode atualizar a si mesmo
    if str(cod_cliente) != str(cod_cliente_sessao):
        return JsonResponse({
            "erro": "Acesso negado: você não pode editar outro cliente"
        }, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        # Retornar dados do cliente em JSON (para modal)
        data = cl_gdf.get_cliente_upd(i_v_cliente_id=cod_cliente)
        if not data or data.get('erro'):
            return JsonResponse({"erro": "Cliente não encontrado"}, status=404)

        return JsonResponse(data)

    elif request.method == "POST":
        cod_cliente_id = request.POST.get("upd_cliente_id", "").strip()
        
        # ✅ Extrair dados do formulário
        razao = request.POST.get("upd_razao", "").strip()
        cnpj = request.POST.get("upd_cnpj", "").strip()
        cnpj = re.sub(r"\D", "", cnpj)
        is_active = request.POST.get("upd_is_active") == "on"
        
        # ✅ Validações básicas
        if not razao:
            return JsonResponse({"erro": "Razão social é obrigatória"}, status=400)
        if not cnpj:
            return JsonResponse({"erro": "CNPJ é obrigatório"}, status=400)

        resultado = cl_gdf.upd_cliente(
            i_cliente=cod_cliente_id,
            i_razao=razao,
            i_cnpj=cnpj,
            i_is_active=is_active
        )
        
        # ✅ Detectar se é requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not resultado.get("success"):
            mensagem = resultado.get("message", "Erro ao atualizar")
            if is_ajax:
                return JsonResponse({"success": False, "message": mensagem}, status=400)
            else:
                messages.error(request, mensagem, extra_tags='MODAL_UPD')
        else:
            mensagem = resultado.get("message", "Cliente atualizado com sucesso!")
            if is_ajax:
                return JsonResponse({"success": True, "message": mensagem}, status=200)
            else:
                messages.success(request, mensagem, extra_tags='MODAL_UPD')

        if not is_ajax:
            return redirect('Dm_Clientes')

@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_view_atualizar_acesso_cliente(request):
    """Atualizar acessos do cliente existente"""
    cod_cliente_sessao = request.session.get('cod_cliente', None)
    if not cod_cliente_sessao:
        return JsonResponse({"erro": "Cliente não identificado na sessão"}, status=403)
    
    # ✅ Obter o cod_cliente do formulário (cliente sendo editado)
    cod_cliente = request.POST.get("Acesso_cliente_id", "").strip()
    if not cod_cliente:
        messages.error(request, "Cliente não identificado no formulário", extra_tags='MODAL_UPD')
        return redirect('Dm_Clientes')
    
    cl_gdf = ClGdf()
    ls_solucoes = request.POST.get("ls_solucoes", "").strip()  # Formato: "COD1:1,COD2:0"
    
    print(f"[Cliente_acesso_upd] cod_cliente: {cod_cliente}")
    print(f"[Cliente_acesso_upd] ls_solucoes: {ls_solucoes}")
    
    resultado = cl_gdf.set_cliente_solucoes(
        i_v_cod_cliente=cod_cliente,
        ls_solucoes=ls_solucoes
    )

    print(f"[Cliente_acesso_upd] resultado: {resultado}")

    # ✅ Detectar se é requisição AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not resultado.get("success"):
        mensagem = resultado.get("message", "Erro ao atualizar acessos")
        if is_ajax:
            return JsonResponse({"success": False, "message": mensagem}, status=400)
        else:
            messages.error(request, mensagem, extra_tags='MODAL_UPD')
    else:
        mensagem = resultado.get("message", "Acessos atualizados com sucesso!")
        if is_ajax:
            return JsonResponse({"success": True, "message": mensagem}, status=200)
        else:
            messages.success(request, mensagem, extra_tags='MODAL_UPD')

    if not is_ajax:
        return redirect('Dm_Clientes')

@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_view_CargaXml(request):
    """View para carregamento de XML"""
    cod_cliente = request.session.get('cod_cliente', None)
    
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Cliente não identificado'})
    
    context = {
        'cod_cliente': cod_cliente,
    }
    return render(request, 'Processamento/index_CargaXml.html', context)

@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_processar_xml(request):
    """API para processar upload de XMLs"""
    cod_cliente = request.session.get('cod_cliente', None)
    
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    
    try:
        # Processar upload de XML aqui
        cl_xml = Carga_xml()

        lsl_Xml          = request.FILES.getlist('arquivo')
        l_v_type_xml     = request.POST.get('type_xml', 'NFe')
        l_v_origem_dados = request.POST.get('origem_dados', 'LOCAL')

        if not lsl_Xml:
            return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum arquivo selecionado'}, status=400)

        upload_result = cl_xml.set_upload_xml(lsl_Xml, l_v_type_xml, l_v_origem_dados, request.user.username)
        
        return JsonResponse({
            'sucesso': len(upload_result['errors']) == 0,
            'mensagem': f"{len(upload_result['success'])} arquivo(s) processado(s), {len(upload_result['errors'])} erro(s)",
            'detalhes': upload_result
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao processar: {str(e)}'}, status=500)

@login_required(login_url='Login')
def fn_view_Reprocessamento(request):
    """View para reprocessamento de dados"""
    cod_cliente = request.session.get('cod_cliente', None)
    
    context = {
        'cod_cliente': cod_cliente,
    }
    return render(request, 'Processamento/index_Reprocessamento.html', context)