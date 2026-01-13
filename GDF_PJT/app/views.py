from pyexpat.errors import messages
from django.shortcuts               import render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf                    import settings
from app.static.classes.gdf         import cl_Gdf

cl_GdfBase = cl_Gdf()
def Login_view(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password')

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            cl_GdfBase.get_dados(request.user)
            if not cl_GdfBase.Retorn:
                solucoes = cl_GdfBase.get_solucoes()
                if solucoes:
                    request.session['solucoes'] = solucoes
                    return render(request, 'Index_Home.html')
                else:
                    return render(request, 'Index_Login.html', {'error_message': 'Problema de Acesso.'})  
            return redirect('Home')   
        else:
            return render(request, 'Index_Login.html', {'error_message': 'Usuário ou senha inválidos.'})

    return render(request, 'Index_Login.html')


def Home_view(request):
    return render(request, "Index_Home.html")

@login_required(login_url='Login')
def Dashboard_View(request):
    #token = cl_GdfBase.gerar_(request.user)
    #return render(request, "Index_Dashboard.html", {"token": token})
    return render(request, "Index_Home.html")

@login_required
def Sair_View(request):   
    logout(request)
    return redirect('Login')
