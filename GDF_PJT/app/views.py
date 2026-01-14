from pyexpat.errors import messages
from django.shortcuts               import render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf                    import settings
from app.classes.gdf                import cl_Gdf
from django.core.paginator          import Paginator
from datetime                       import timedelta
from django.utils                   import timezone
import jwt

cl_GdfBase = cl_Gdf()
def Gerar_token(request, user): 
    if not user.is_active:
        return None 
    else:
        payload = {
            "user_id": user.id,
            "username": user.username,
            "iat": timezone.now(),
            "exp": timezone.now() + timedelta(minutes=30),
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def Login_view(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password')

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            #cl_GdfBase = cl_Gdf()

            #buscar dados do usuario
            cl_GdfBase.get_dados(request.user)

            if not cl_GdfBase.Retorn:
                #buscar solucoes que tem acessos 
                solucoes = cl_GdfBase.get_solucoes()

                if solucoes:
                    request.session['t_solucoes'] = solucoes
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
        #if sub_solucao:
        #    return redirect(sub_solucao['cod_subsolucoes']) #CODIGO DA SUB-SOLUÇÃO NOME DA FUNÇÃO

        #else:
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
def Dm_Usuarios_view(request): # Usuários
    if request.user.is_authenticated:
        #query = request.GET.get('Buscar', '').strip().lower()
        #t_user, t_empresa_id, t_grpacessos  = cl_GdfBase.get_usuarios()

        
        #if cl_GdfBase.Retorn:
        #    messages.error(request, cl_GdfBase.Retorn[0] if cl_GdfBase.Retorn else "Erro ao obter usuários.")
        #    return render(request, 'index_home.html')
        """""
        if query:
            t_user = [
                user for user in t_user
                if query in str(user.get('id', '')).lower()
                or query in str(user.get('username', '')).lower()
                or query in str(user.get('first_name', '')).lower()
                or query in str(user.get('last_name', '')).lower()
                or query in str(user.get('email', '')).lower()
                or query in str(user.get('date_joined', '')).lower()
                or query in str(user.get('empresa_id', '')).lower()
            ]
        """
        #paginator = Paginator(t_user, 30)  # Numero página (Paginator)
        #page_number = request.GET.get('page')
        #page_obj = paginator.get_page(page_number)

        #return render(request, 'index_usuarios.html',{  'page_obj': page_obj,
        #                                                't_user':t_user,
        #                                                't_empresa_id': t_empresa_id,
        #                                                't_grpacesso':  t_grpacessos})
        return render(request, 'Index_Usuarios.html')
    return render(request, 'Index_Login.html')

def Dm_Empresas_view(request): # Empresas
    if request.user.is_authenticated:
        query = request.GET.get('Buscar', '').strip().lower() 
        t_empresas, t_grpempresas = cl_GdfBase.get_empresas()

        if cl_GdfBase.Retorn:
            messages.error(request,  cl_GdfBase.Retorn[0] if cl_GdfBase.Retorn else "Erro ao obter empresas.")
            return render(request, 'Index_Home.html')
        
        if query:
            t_empresas = [
                emp for emp in t_empresas
                if query in str(emp.get('cod_empresa', '')).lower()
                or query in str(emp.get('razao', '')).lower()
                or query in str(emp.get('cnpj', '')).lower()
                or query in str(emp.get('fantasia', '')).lower()
            ]

        paginator = Paginator(t_empresas, 50)  # 50 usuários por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'index_empresas.html',{  'page_obj': page_obj,
                                                        't_empresas':t_empresas,
                                                        't_grpempresas':t_grpempresas,
                                                        'query': query })
    return render(request, 'Index_Login.html')

def Dm_Clientes_view(request): # Clientes
    if request.user.is_authenticated:
        query = request.GET.get('Buscar', '').strip() 
        t_Clientes, T_Soluçoes = cl_GdfBase.get_clientes()

        if cl_GdfBase.Retorn:
            messages.error(request,  cl_GdfBase.Retorn[0] if cl_GdfBase.Retorn else "Erro ao obter clientes.")
            return render(request, 'index_home.html')

        if query:
            t_Clientes = [
                clie for clie in t_Clientes
                if query in str(clie.get('cod_cliente','')).lower()
                or query in str(clie.get('cnpj')).lower()
                or query in str(clie.get('razao')).lower()
                or query in str(clie.get('date_joined')).lower()
            ]

        paginator   = Paginator(t_Clientes, 50)  # 50 usuários por página
        page_number = request.GET.get('page')
        page_obj    = paginator.get_page(page_number)

        return render(request, 'index_clientes.html',{  'page_obj': page_obj,
                                                        'T_Clientes':t_Clientes,
                                                        'T_Soluçoes':T_Soluçoes,
                                                        })
    return render(request, 'Index_Login.html')
#--------------------------------------------------------------------
#       Sub-soluções Views (Manifesto)
#--------------------------------------------------------------------

#--------------------------------------------------------------------
#       Sub-soluções Views (Reinf)
#--------------------------------------------------------------------

#--------------------------------------------------------------------
#       Modais Views
#--------------------------------------------------------------------



#--------------------------------------------------------------------
#       Sub-soluções Views (Dashboard)
#--------------------------------------------------------------------
@login_required(login_url='Login')
def Dashboard_view(request):   
    #token = Gerar_token(request, request.user)
    token = "teste12345"
    return render(request, "Index_Dashboard.html", {"token": token})

