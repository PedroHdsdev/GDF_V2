from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts               import get_object_or_404, render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http   import require_http_methods
from django.conf                    import settings
from django.contrib                 import messages
from app.classes.Gdf                import Cl_Gdf
from django.core.paginator          import Paginator
from app.db_GDF.Public.models       import UserEmpresas, Empresas
import re

def Login_view(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password') 

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            ClGdf = Cl_Gdf()
            ClGdf.Get_Dados(request.user) 

            if not ClGdf.Retorn:
                #buscar solucoes que tem acessos 
                solucoes = ClGdf.Get_Solucoes()
                if solucoes:
                    request.session['t_solucoes']  = solucoes
                    request.session['cod_cliente'] = ClGdf.Cliente.cod_cliente

                    return render(request, 'Index_Home.html')
                else:
                    return render(request, 'Index_Login.html', {'error_message': 'Problema de Acesso.'})  
            return redirect('Home')   
        else:
            return render(request, 'Index_Login.html', {'error_message': 'Usuário ou senha inválidos.'})

    return render(request, 'Index_Login.html')

def get_subsolucao_view(request, cod_sub): 
    if request.user.is_authenticated:

        solucoes = request.session.get('t_solucoes', [])

        for sol in solucoes:
            for sub in sol.get('sub_solucoes', []):
                if str(sub.get('cod_subsolucao')) == str(cod_sub):
                    return redirect(sub.get('cod_subsolucao'))

        return render(request, 'index_home.html')

    return render(request, 'index_login.html')

@login_required(login_url='Login')
def Home_view(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            codigo = request.POST.get('codigo')
            
            if codigo:
                return redirect(codigo)
            
        return render(request, "Index_Home.html")
    return render(request, 'Index_Login.html')

@login_required
def Sair_View(request):   
    logout(request)
    return redirect('Login')

#--------------------------------------------------------------------
#       Sub-soluções Views (Administração)
#--------------------------------------------------------------------
# Usuarios
@login_required(login_url='Login')
def Dm_Usuarios_view(request):
    cod_cliente = request.session.get('cod_cliente', None)
    
    # Validar se usuário tem acesso a cliente
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Acesso negado: cliente não identificado'})
    
    # Buscar dados APENAS uma vez - carregamento inicial da página
    cl_gdf = Cl_Gdf()
    t_user = cl_gdf.Get_Usuarios(i_cod_Cliente=cod_cliente)

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
def Dm_Empresas_view(request): 
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return redirect('Login')
    
    cl_gdf = Cl_Gdf()

    # Buscar todas as empresas - paginação será feita em JavaScript
    t_empresas = cl_gdf.Get_Empresas(i_cod_Cliente=cod_cliente)
    
    return render(
        request,
        'Empresas/Index_Empresas.html',
        {
            't_empresas': t_empresas
        }
    )

# Clientes
@login_required(login_url='Login')
def Dm_Clientes_view(request): 
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return redirect('Login')
    
    cl_gdf = Cl_Gdf()
    
    t_clientes = cl_gdf.Get_Clientes()

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
def Usuario_ins(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
    if request.method == "GET":
        # ✅ Retorna dados para preencher o modal
        return JsonResponse(cl_gdf.Get_Usuario_ins(cod_cliente=cod_cliente))

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
            t_user = cl_gdf.Get_Usuarios(i_cod_Cliente=cod_cliente)
            return render(request, 'usuarios/Usuarios.html', {
                't_user': t_user,
                'error_message': ' | '.join(errors)
            })
        
        # ✅ Chamar método de inserção na classe
        resultado = cl_gdf.Usuario_ins(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            empresas_ids=empresas_str,  # "1,2,3"
            grupos_ids=grupos_str,      # "4,5,6"
            cod_cliente=cod_cliente
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            t_user = cl_gdf.Get_Usuarios(i_cod_Cliente=cod_cliente)
            return render(request, 'usuarios/Usuarios.html', {
                't_user': t_user,
                'error_message': resultado.get("message", "Erro ao criar usuário")
            })
        
        # ✅ Sucesso! Redirecionar com mensagem
        t_user = cl_gdf.Get_Usuarios(i_cod_Cliente=cod_cliente)
        return render(request, 'usuarios/Usuarios.html', {
            't_user': t_user,
            'success_message': resultado.get("message")
        })

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def Usuario_upd(request, user_id):
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
    
    cl_gdf = Cl_Gdf()
    if request.method == "GET":
        # Retornar dados do usuário em JSON (para modal)
        data = cl_gdf.Get_Usuario_upd(user_id=int(user_id), cod_cliente=cod_cliente)
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

        resultado = cl_gdf.Usuario_upd(
            user_id=int(user_id),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active,
            empresa_ids=empresa_ids,
            grupo_ids=grupo_ids,
            cod_cliente=cod_cliente
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            return JsonResponse({"erro": resultado.get("message")}, status=400)

        return redirect('Dm_Usuarios')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)
    
#--------------------------------------------------------------------
#       Sub-soluções Views (Dashboard)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Dashboard_view(request):   
    token = Cl_Gdf.Gerar_Token(request, request.user)
    if not token:
        return render(request, 'Index_Login.html', {'error_message': 'Erro ao gerar token de acesso'})
    return render(request, "Index_Dashboard.html", {"token": token })

#--------------------------------------------------------------------
#       Empresas - Modais
#--------------------------------------------------------------------
@login_required(login_url='Login')
@require_http_methods(["GET","POST"])
def Empresa_ins(request):
    """Inserir nova empresa"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
    if request.method == "GET":
        data = cl_gdf.Get_Empresas_ins(cod_cliente=cod_cliente)
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
        resultado = cl_gdf.Empresa_ins(
            cod_empresa=cod_empresa,
            razao=razao,
            cnpj=cnpj,
            fantasia=fantasia,
            grp_empresa=grp_empresa,
            cod_cliente=cod_cliente,
            matriz=matriz,
            ie=ie,
            im=im,
            iest=iest,
            crt=crt,
            cnae=cnae,
            suframa=suframa,
            chave_acesso=chave_acesso
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            return JsonResponse({"erro": resultado.get("message")}, status=400)

        return redirect('Dm_Empresas')

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def Empresa_upd(request, cod_empresa):
    """Atualizar empresa existente"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
    if request.method == "GET":
        # Retornar dados da empresa para popular o modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            empresa_data = cl_gdf.Get_Empresas_upd(
                i_Cod_empresas=cod_empresa,
                cod_cliente=cod_cliente
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
        
        resultado = cl_gdf.Empresa_upd(
            cod_empresa=cod_empresa,
            razao=razao,
            fantasia=fantasia,
            ie=ie,
            im=im,
            iest=iest,
            crt=crt,
            cnae=cnae,
            suframa=suframa,
            grp_empresa=grp_empresa,
            chave_acesso=chave_acesso,
            matriz=matriz,
            cod_cliente=cod_cliente
        )
        
        if resultado.get("success"):
            messages.success(request, resultado.get("message", "Empresa atualizada!"), extra_tags='MODAL_UPD')
        else:
            messages.error(request, resultado.get("message", "Erro ao atualizar"), extra_tags='MODAL_UPD')
        
        return redirect('Dm_Empresas')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)

@login_required(login_url='Login')
@require_http_methods(["POST"])
def Cert_upd(request):
    """Atualizar certificado digital da empresa"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
    
    # Pegar arquivo do certificado
    cert_file = request.FILES.get('m_file')
    if not cert_file:
        messages.error(request, "Nenhum arquivo selecionado", extra_tags='MODAL_UPD')
        return redirect('Dm_Empresas')
    
    # Validar extensão
    if not cert_file.name.endswith(('.pfx', '.p12')):
        messages.error(request, "Formato inválido. Use .pfx ou .p12", extra_tags='MODAL_UPD')
        return redirect('Dm_Empresas')
    
    # Chamar método de atualização de certificado
    resultado = cl_gdf.Cert_upd(
        cert_file=cert_file,
        cod_cliente=cod_cliente
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
def Cliente_ins(request):
    """Inserir novo cliente - seguindo padrão Usuario_ins"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
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
        resultado = cl_gdf.Cliente_ins(
            i_cliente=cliente_id,
            i_razao=razao,
            i_cnpj=cnpj
        )
        
        # ✅ Verificar resultado
        if not resultado.get("success"):
            return JsonResponse({"erro": resultado.get("message")}, status=400)

        return redirect('Dm_Clientes')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def Cliente_upd(request, cod_cliente):
    """Atualizar cliente existente - seguindo padrão Usuario_upd"""
    cod_cliente_sessao = request.session.get('cod_cliente', None)
    if not cod_cliente_sessao:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
 
    cl_gdf = Cl_Gdf()
    if request.method == "GET":
        # Retornar dados do cliente em JSON (para modal)
        data = cl_gdf.Get_Clientes_upd(cliente_id=cod_cliente)
        if not data or data.get('erro'):
            return JsonResponse({"erro": "Cliente não encontrado"}, status=404)

        return JsonResponse(data)

    elif request.method == "POST":
        modal_upd = request.POST.get("modal_upd", "").strip()
        cod_cliente_id = request.POST.get("upd_cliente_id", "").strip()
        
        if not cod_cliente_id:
            cod_cliente_id = request.POST.get("Acesso_cliente_id", "").strip()

        # Atualização dos dados do cliente (aba Dados)
        if modal_upd == "C" or modal_upd == "":
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

            resultado = cl_gdf.Cliente_upd(
                i_cliente=cod_cliente_id,
                i_razao=razao,
                i_cnpj=cnpj,
                i_is_active=is_active
            )
            if not resultado.get("success"):
                return JsonResponse({"erro": resultado.get("message")}, status=400)

        # Atualização dos acessos (aba Direitos de Acesso)
        if modal_upd == "S" or modal_upd == "":
            ls_solucoes = request.POST.get("ls_solucoes", "").strip()  # Formato: "COD1:1,COD2:0"
            resultado = cl_gdf.Cliente_solucao(
                i_Cod_cliente=cod_cliente_id,
                ls_solucoes=ls_solucoes
            )
            if not resultado.get("success"):
                return JsonResponse({"erro": resultado.get("message")}, status=400)
        
        return redirect('Dm_Clientes')
    return JsonResponse({"erro": "Método não permitido"}, status=405)