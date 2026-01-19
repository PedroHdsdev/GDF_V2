from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts               import get_object_or_404, render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http   import require_http_methods
from django.conf                    import settings
from app.classes.Gdf                import Cl_Gdf
from django.core.paginator          import Paginator
from pyexpat.errors import messages
#from django.http import JsonResponse

def Login_view(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password') 

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            ClGdf = Cl_Gdf()
            ClGdf.get_dados(request.user) 

            if not ClGdf.Retorn:
                #buscar solucoes que tem acessos 
                solucoes = ClGdf.get_solucoes()
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
                if str(sub.get('cod_subsolucoes')) == str(cod_sub):
                    return redirect(sub.get('cod_subsolucoes'))

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
    query = request.GET.get('q', '').strip()
    
    # Validar se usuário tem acesso a cliente
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Acesso negado: cliente não identificado'})
    
    # Buscar dados APENAS uma vez - carregamento inicial da página
    cl_gdf = Cl_Gdf()
    t_user, t_empresas, t_auth_groups = cl_gdf.get_usuarios(i_cod_Cliente=cod_cliente)

    # ✅ Passar dados brutos para o template
    # Paginação e busca serão feitas em JavaScript no cliente
    return render(
        request,
        'usuarios/Usuarios.html',
        {
            't_user': t_user,
            't_empresas': t_empresas,
            't_auth_groups': t_auth_groups,            
        }
    )

# Empresas
@login_required(login_url='Login')
def Dm_Empresas_view(request): 
    ClPublic = Cl_Gdf()
    return render(request, 'Index_Login.html')

# Clientes
@login_required(login_url='Login')
def Dm_Clientes_view(request): 
    ClPublic = Cl_Gdf()
    return render(request, 'Index_Login.html')

#--------------------------------------------------------------------
#       Sub-soluções Views ( Implementação )
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Im_Projetos_view(request): 
    return render(request, 'Index_Login.html')

#--------------------------------------------------------------------
#       Modais Views
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Usuario_ins(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    if request.method == "POST":
        # ✅ Validações de campos obrigatórios
        username    = request.POST.get("username", "").strip()
        first_name  = request.POST.get("first_name", "").strip()
        last_name   = request.POST.get("last_name", "").strip()
        email       = request.POST.get("email", "").strip()
        password    = request.POST.get("password", "").strip()
        empresa_id  = request.POST.get("ls_empresas", "").strip()
        
        # ✅ Validar campos obrigatórios
        if not all([username, email, password, empresa_id]):
            cl_gdf = Cl_Gdf()
            t_user, t_empresas, t_auth_groups = cl_gdf.get_usuarios(i_cod_Cliente=cod_cliente)
            return render(request, 'usuarios/Usuarios.html', {
                't_user': t_user,
                't_empresas': t_empresas,
                't_auth_groups': t_auth_groups,
                'error_message': 'Username, email, senha e empresa são obrigatórios.'
            })
        
        # ✅ Processar grupos: vêm como string separada por vírgula do hidden input
        grupos_str = request.POST.get("ls_grupos", "")
        grupo_ids = [int(g.strip()) for g in grupos_str.split(",") if g.strip()]

        cl_gdf = Cl_Gdf()
        result = cl_gdf.ins_usuario(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            empresa_id=empresa_id,
            grupo_ids=grupo_ids,
            cod_cliente=cod_cliente
        )
        
        # ✅ Verificar resultado
        if result is True:
            return redirect('Dm_Usuarios')
        else:
            t_user, t_empresas, t_auth_groups = cl_gdf.get_usuarios(i_cod_Cliente=cod_cliente)
            return render(request, 'usuarios/Usuarios.html', {
                't_user': t_user,
                't_empresas': t_empresas,
                't_auth_groups': t_auth_groups,
                'error_message': 'Erro ao criar usuário. Verifique os dados.'
            })

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def Usuario_upd(request, user_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    cl_gdf = Cl_Gdf()
    
    if request.method == "GET":
        # Retornar dados do usuário em JSON (para modal)
        user = cl_gdf.get_usuario_id(user_id=user_id, cod_cliente=cod_cliente)
        if not user or user.get('erro'):
            return JsonResponse({"erro": "Usuário não encontrado"}, status=404)
        return JsonResponse(user)
    
    elif request.method == "POST":
        # ✅ Validações de campos obrigatórios
        first_name  = request.POST.get("first_name", "").strip()
        last_name   = request.POST.get("last_name", "").strip()
        email       = request.POST.get("email", "").strip()
        is_active   = request.POST.get("is_active") == "on"
        empresa_id  = request.POST.get("ls_empresas", "").strip()
        
        # ✅ Validar campos obrigatórios
        if not all([email, empresa_id]):
            return JsonResponse({"erro": "Email e empresa são obrigatórios"}, status=400)
        
        # ✅ Processar grupos: podem vir como string separada por vírgula do hidden input
        grupos_str = request.POST.get("ls_grupos", "")
        grupo_ids = [int(g.strip()) for g in grupos_str.split(",") if g.strip()]

        cl_gdf.upd_usuario(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active,
            empresa_id=empresa_id,
            grupo_ids=grupo_ids,
            cod_cliente=cod_cliente
        )
        
        # ✅ Verificar se houve erro
        if cl_gdf.Retorn and isinstance(cl_gdf.Retorn, list) and cl_gdf.Retorn[0].get('erro'):
            return JsonResponse(cl_gdf.Retorn[0], status=400)

        return redirect('Dm_Usuarios')
    
    return JsonResponse({"erro": "Método não permitido"}, status=405)
    
#--------------------------------------------------------------------
#       Sub-soluções Views (Dashboard)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Dashboard_view(request):   
    token = Cl_Gdf.Gerar_token(request, request.user)
    if not token:
        return render(request, 'Index_Login.html', {'error_message': 'Erro ao gerar token de acesso'})
    return render(request, "Index_Dashboard.html", {"token": token})


