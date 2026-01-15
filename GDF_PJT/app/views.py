from django.shortcuts               import render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
            ClPublic = Cl_Gdf()
            ClPublic.get_dados(request.user) 

            if not ClPublic.Retorn:
                #buscar solucoes que tem acessos 
                solucoes = ClPublic.get_solucoes()
                if solucoes:
                    request.session['t_solucoes']  = solucoes
                    request.session['cod_cliente'] = ClPublic.Cliente.cod_cliente

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
    ClPublic = Cl_Gdf()
    Cod_cliente = request.session.get('cod_cliente', None)

    # Busca de usuários com filtro
    Query = request.GET.get('Buscar', '').strip().lower()


    t_User,t_Empresas,t_AuthGroups = ClPublic.get_usuarios(i_cod_Cliente=Cod_cliente)

    if Query:
        t_User = [
            u for u in t_User
            if Query in str(u.get('id', '')).lower()
            or Query in str(u.get('username', '')).lower()
            or Query in str(u.get('first_name', '')).lower()
            or Query in str(u.get('last_name', '')).lower()
            or Query in str(u.get('email', '')).lower()
            or Query in str(u.get('empresa_id', '')).lower()
        ]

    #if ClPublic.Retorn:
        #messages.error(
        #    request,
        #    ClPublic.Retorn[0] if ClPublic.Retorn else "Erro ao obter usuários."
        #)
        #return render(request, 'index_home.html')

    paginator = Paginator(t_User, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'usuarios/Usuarios.html',
        {
            'page_obj': page_obj,        
            't_user': t_User,
            't_empresas': t_Empresas,
            't_AuthGroup': t_AuthGroups,            
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
def Usuario_ins(request):
    if request.method == "POST":
        # Processar os dados do formulário aqui
        pass

    return render(request, 'usuarios/Usuarios_ins.html')

def Usuario_upd(request):
    if request.method == "POST":
        # Processar os dados do formulário aqui
        pass

    return render(request, 'usuarios/Usuarios_upd.html')


    
#--------------------------------------------------------------------
#       Sub-soluções Views (Dashboard)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Dashboard_view(request):   
    #token = Gerar_token(request, request.user)
    token = "teste12345"
    return render(request, "Index_Dashboard.html", {"token": token})

