import json
import os
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts               import get_object_or_404, render
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from app.decorators                 import validate_idor_empresa, validate_idor_usuario, validate_session_required
from django.views.decorators.http   import require_http_methods
from django.conf                    import settings
from django.contrib                 import messages

# Dicionário tipo de pagamento (código XML → descrição) para relatório fiscal e exibição
_path_tipo_pagamento = getattr(settings, 'BASE_DIR', None)
if _path_tipo_pagamento is not None:
    _path_tipo_pagamento = os.path.join(str(_path_tipo_pagamento), 'json', 'Tipo_pagamento.json')
    try:
        with open(_path_tipo_pagamento, 'r', encoding='utf-8') as _f:
            TIPO_PAGAMENTO_DESC = json.load(_f)
    except Exception:
        TIPO_PAGAMENTO_DESC = {}
else:
    TIPO_PAGAMENTO_DESC = {}

def _descricao_tipo_pagamento(codigo):
    """Retorna a descrição do tipo de pagamento pelo código (XML). Usado no relatório fiscal."""
    if codigo is None or codigo == '':
        return 'Não informado'
    return TIPO_PAGAMENTO_DESC.get(str(codigo).strip(), None)  # None = usar display do model depois
from app.classes.gdf                import ClGdf
from app.classes.CargaXml           import Carga_xml
from django.core.paginator          import Paginator
from django.db.models               import Q, Count
from app.db_GDF.Public.models       import (
    UserEmpresas, Empresas, Clientes, GrpEmpresas,
    CargaXmlParam, CargaXmlJob,
    CargaSpedParam, CargaSpedJob,
)
from app.classes.CargaSped          import Carga_sped
from app.db_GDF.NFe.models          import (
    NFe, NFe_Identificacao, NFe_Emitente, NFe_Destinatario, NFe_Endereco,
    NFe_Produto, NFe_Total, NFe_Cobranca, NFe_Parcela, NFe_Pagamento,
    NFe_Transporte, NFe_Informacoes_Adicionais,
)
from app.db_GDF.CTe.models         import (
    CTe, CTe_Identificacao, CTe_Emitente, CTe_Destinatario, CTe_Valor,
    CTe_Transporte, CTe_Carga, CTe_Servico, CTe_Veiculo, CTe_Motorista,
    CTe_Percurso, CTe_Fiscal,
)
from app.db_GDF.NFSe.models        import (
    NFSe, NFSe_Identificacao, NFSe_Prestador, NFSe_Tomador, NFSe_Endereco,
    NFSe_RPS, NFSe_Retencao, NFSe_Pagamento, NFSe_Servico,
)
from app.db_GDF.Sped.models        import Sped_Arquivo, Sped_Fiscal, Sped_Contribuicao
from app.db_Reprocessamento.models import ReprocessamentoLote, Divergencia, ReprocessamentoJob
from django.utils import timezone
import re

# Cliente ao qual superusuários têm acesso total ao painel (todos os clientes)
COD_CLIENTE_SUPERUSER_PAINEL = '1000'


def _superuser_acesso_total_painel(request):
    """Retorna True se o superuser tem acesso total ao painel (todos os clientes).
    Superusers vinculados ao cliente 1000 (session superuser_cliente_1000) têm sempre acesso total.
    Outros superusers têm seletor de cliente apenas quando cod_cliente é None ou 1000."""
    if not request.session.get('is_superuser', False):
        return False
    if request.session.get('superuser_cliente_1000', False):
        return True
    cod = request.session.get('cod_cliente') or ''
    return cod == '' or str(cod).strip() == COD_CLIENTE_SUPERUSER_PAINEL
import json
import zipfile
from pathlib import Path
from datetime import datetime

def fn_view_login(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password') 

        user = authenticate(username=Username, password=password)
        
        if user is not None:
            if not getattr(user, 'is_active', True):
                return render(request, 'Index_Login.html', {'error_message': 'Usuário inativo.'})
            login(request, user)
            cl_gdf_instance = ClGdf()
            cl_gdf_instance.get_dados(request.user)

            request.session['is_superuser'] = getattr(user, 'is_superuser', False)
            request.session['is_staff'] = getattr(user, 'is_staff', False)
            # Superuser vinculado ao cliente 1000 tem acesso total ao painel (todos os clientes)
            _cliente = getattr(cl_gdf_instance, 'Cliente', None)
            _cod = getattr(_cliente, 'cod_cliente', None) if _cliente else None
            request.session['superuser_cliente_1000'] = (
                getattr(user, 'is_superuser', False) and _cod is not None and str(_cod).strip() == COD_CLIENTE_SUPERUSER_PAINEL
            )

            if not cl_gdf_instance.Retorn:
                solucoes = cl_gdf_instance.get_solucoes()
                cod_cliente = (
                    cl_gdf_instance.Cliente.cod_cliente
                    if getattr(cl_gdf_instance, 'Cliente', None) else None
                )
                if solucoes or getattr(user, 'is_superuser', False):
                    request.session['t_solucoes'] = solucoes or []
                    request.session['cod_cliente'] = cod_cliente
                    # Contexto para Index_Home (evita erro de is_superuser/lista_clientes indefinidos)
                    context = {'cod_cliente': cod_cliente}
                    if getattr(user, 'is_superuser', False):
                        context['is_superuser'] = True
                        if not cod_cliente or str(cod_cliente).strip() == COD_CLIENTE_SUPERUSER_PAINEL:
                            context['lista_clientes'] = cl_gdf_instance.get_clientes()
                    return render(request, 'Index_Home.html', context)
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
    if not request.user.is_authenticated:
        return redirect('Login')
    is_superuser = request.session.get('is_superuser', False)
    cod_cliente = request.session.get('cod_cliente')
    # Superuser (cliente 1000): permitir trocar cliente por POST; opcionalmente redirecionar para "next"
    _REDIRECT_NAMES = ('Home', 'Dm_Empresas', 'Dm_Usuarios', 'Dm_Clientes')
    if request.method == "POST":
        codigo = request.POST.get('codigo')
        novo_cliente = request.POST.get('cod_cliente', '').strip()
        next_name = (request.POST.get('next') or '').strip()
        if is_superuser and novo_cliente:
            request.session['cod_cliente'] = novo_cliente
            if next_name in _REDIRECT_NAMES:
                return redirect(next_name)
            return redirect('Home')
        if codigo:
            return redirect(codigo)
    context = {'cod_cliente': cod_cliente}
    if is_superuser:
        context['is_superuser'] = True
        if _superuser_acesso_total_painel(request):
            cl_gdf = ClGdf()
            context['lista_clientes'] = cl_gdf.get_clientes()
    return render(request, "Index_Home.html", context)

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
    is_superuser = request.session.get('is_superuser', False)
    if not cod_cliente:
        if is_superuser:
            messages.info(request, 'Selecione um cliente na Home para gerenciar usuários.')
            return redirect('Home')
        return render(request, 'Index_Login.html', {'error_message': 'Acesso negado: cliente não identificado'})
    
    cl_gdf = ClGdf()
    t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
    is_superuser = request.session.get('is_superuser', False)
    context = {
        't_user': t_user,
        'cod_cliente': cod_cliente,
        'is_superuser': is_superuser,
    }
    if is_superuser and _superuser_acesso_total_painel(request):
        context['lista_clientes'] = cl_gdf.get_clientes()
    return render(request, 'Usuarios/Index_Usuarios.html', context)

# Empresas
@login_required(login_url='Login')
def fn_view_listar_empresas(request):
    cod_cliente = request.session.get('cod_cliente', None)
    is_superuser = request.session.get('is_superuser', False)
    if not cod_cliente:
        if is_superuser:
            messages.info(request, 'Selecione um cliente na Home para gerenciar empresas.')
            return redirect('Home')
        return redirect('Login')
    
    cl_gdf = ClGdf()
    t_empresas = cl_gdf.get_empresas(i_v_cod_cliente=cod_cliente)
    context = {
        't_empresas': t_empresas,
        'cod_cliente': cod_cliente,
        'is_superuser': is_superuser,
    }
    if is_superuser and _superuser_acesso_total_painel(request):
        context['lista_clientes'] = cl_gdf.get_clientes()
    return render(request, 'Empresas/Index_Empresas.html', context)

# Clientes
@login_required(login_url='Login')
def fn_view_listar_clientes(request):
    cod_cliente = request.session.get('cod_cliente', None)
    is_superuser = request.session.get('is_superuser', False)
    if not cod_cliente and not is_superuser:
        return redirect('Login')
    cl_gdf = ClGdf()
    t_clientes = cl_gdf.get_clientes()
    context = {'t_clientes': t_clientes, 'cod_cliente': cod_cliente}
    if is_superuser and _superuser_acesso_total_painel(request):
        context['is_superuser'] = True
        context['lista_clientes'] = t_clientes  # mesma lista para o seletor de contexto
    return render(request, 'Clientes/Index_Clientes.html', context)

#--------------------------------------------------------------------
#       Modais Views
#--------------------------------------------------------------------
@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_inserir_usuario(request):
    """Inserir usuário. Superuser pode informar o cliente no formulário."""
    is_superuser = request.session.get('is_superuser', False)
    cod_cliente = request.session.get('cod_cliente', None)
    if request.method == "GET":
        if is_superuser and request.GET.get('cod_cliente'):
            cod_cliente = request.GET.get('cod_cliente', '').strip() or cod_cliente
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        cl_gdf = ClGdf()
        return JsonResponse(cl_gdf.get_usuario_dados_ins(i_v_cod_cliente=cod_cliente))

    if request.method == "POST":
        if is_superuser and request.POST.get("m_cod_cliente"):
            cod_cliente = request.POST.get("m_cod_cliente", "").strip() or cod_cliente
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        cl_gdf = ClGdf()
        username        = request.POST.get("username", "").strip()
        first_name      = request.POST.get("first_name", "").strip()
        last_name       = request.POST.get("last_name", "").strip()
        email           = request.POST.get("email", "").strip()
        password        = request.POST.get("password", "").strip()
        password_conf   = request.POST.get("password_confirm", "").strip()
        empresas_str    = request.POST.get("ls_empresas", "").strip()
        grupos_str      = request.POST.get("ls_grupos", "").strip()

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
            ctx = {'t_user': t_user, 'error_message': ' | '.join(errors), 'cod_cliente': cod_cliente, 'is_superuser': is_superuser}
            if is_superuser and _superuser_acesso_total_painel(request):
                ctx['lista_clientes'] = cl_gdf.get_clientes()
            return render(request, 'Usuarios/Index_Usuarios.html', ctx)

        resultado = cl_gdf.set_usuario(
            i_v_username=username,
            i_v_email=email,
            i_v_password=password,
            i_v_first_name=first_name,
            i_v_last_name=last_name,
            i_lsl_empresas_ids=empresas_str,
            i_lsl_grupos_ids=grupos_str,
            i_v_cod_cliente=cod_cliente
        )
        if not resultado.get("success"):
            t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
            ctx = {'t_user': t_user, 'error_message': resultado.get("message", "Erro ao criar usuário"), 'cod_cliente': cod_cliente, 'is_superuser': is_superuser}
            if is_superuser and _superuser_acesso_total_painel(request):
                ctx['lista_clientes'] = cl_gdf.get_clientes()
            return render(request, 'Usuarios/Index_Usuarios.html', ctx)
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
    """Inserir nova empresa. Superuser pode informar o cliente no formulário."""
    is_superuser = request.session.get('is_superuser', False)
    cod_cliente = request.session.get('cod_cliente', None)
    if request.method == "GET":
        if is_superuser and request.GET.get('cod_cliente'):
            cod_cliente = request.GET.get('cod_cliente', '').strip() or cod_cliente
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        cl_gdf = ClGdf()
        data = cl_gdf.get_empresa_dados_ins(i_v_cod_cliente=cod_cliente)
        return JsonResponse(data)  
    
    elif request.method == "POST":
        if is_superuser and request.POST.get("m_cod_cliente"):
            cod_cliente = request.POST.get("m_cod_cliente", "").strip() or cod_cliente
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        cl_gdf = ClGdf()
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

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": resultado.get("message", "Empresa cadastrada com sucesso")})
        return redirect('Dm_Empresas')


@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_inserir_grp_empresa(request):
    """Criar grupo de empresas. Superuser pode informar o cliente no formulário."""
    is_superuser = request.session.get('is_superuser', False)
    cod_cliente = request.session.get('cod_cliente', None)
    if request.method == "GET":
        return redirect('Dm_Empresas')
    if is_superuser and request.POST.get("m_cod_cliente"):
        cod_cliente = request.POST.get("m_cod_cliente", "").strip() or cod_cliente
    if not cod_cliente:
        messages.error(request, "Cliente não identificado.", extra_tags="MODAL_GRP_INS")
        return redirect('Dm_Empresas')

    grp_empresa = request.POST.get("m_grp_empresa", "").strip()[:5]
    descricao = (request.POST.get("m_descricao", "").strip() or "")[:80]
    if not grp_empresa:
        messages.error(request, "Código do grupo é obrigatório.", extra_tags="MODAL_GRP_INS")
        return redirect('Dm_Empresas')

    try:
        cliente = Clientes.objects.get(cod_cliente=cod_cliente)
    except Clientes.DoesNotExist:
        return JsonResponse({"erro": "Cliente não encontrado"}, status=403)

    if GrpEmpresas.objects.filter(grp_empresa=grp_empresa).exists():
        messages.error(request, f"Já existe um grupo com o código '{grp_empresa}'.", extra_tags="MODAL_GRP_INS")
        return redirect('Dm_Empresas')

    GrpEmpresas.objects.create(grp_empresa=grp_empresa, descricao=descricao or None, cliente=cliente)
    messages.success(request, f"Grupo '{grp_empresa}' criado com sucesso.", extra_tags="MODAL_GRP_INS")
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
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"erro": resultado.get("message", "Erro ao criar cliente")}, status=400)
            messages.error(request, resultado.get("message", "Erro ao criar cliente"), extra_tags='MODAL_INS')
            return redirect('Dm_Clientes')
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": resultado.get("message", "Cliente cadastrado!")})
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
    
    # Buscar jobs do cliente (todos os registros)
    try:
        cliente = Clientes.objects.get(cod_cliente=cod_cliente)
        jobs = CargaXmlJob.objects.filter(cliente=cliente).order_by('-started_at')
        parametros = CargaXmlParam.objects.filter(cliente=cliente).order_by('-data_criacao')
        # Empresas disponíveis para o usuário dentro deste cliente
        empresas_usuario = Empresas.objects.filter(
            cliente=cliente,
            userempresas__user=request.user
        ).order_by('fantasia', 'razao', 'cod_empresa').distinct()
    except Clientes.DoesNotExist:
        jobs = []
        parametros = []
        empresas_usuario = []
    
    context = {
        'cod_cliente': cod_cliente,
        'jobs': jobs,
        'parametros': parametros,
        'empresas_usuario': empresas_usuario,
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
        l_v_empresa_id   = (request.POST.get('empresa_id') or '').strip()

        if not lsl_Xml:
            return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum arquivo selecionado'}, status=400)

        # validação básica de cada arquivo
        for f in lsl_Xml:
            if not f.name.lower().endswith('.xml'):
                return JsonResponse({'sucesso': False, 'mensagem': f'Arquivo inválido: {f.name}'}, status=400)
            if f.size > 50 * 1024 * 1024:
                return JsonResponse({'sucesso': False, 'mensagem': f'Arquivo muito grande: {f.name}'}, status=400)

        upload_result = cl_xml.set_upload_xml(
            lsl_Xml,
            l_v_type_xml,
            l_v_origem_dados,
            request.user.username,
            cod_cliente
        )
        
        # registrar job manual para histórico com detalhes de cada arquivo
        try:
            from django.utils import timezone
            mensagem_lines = []
            for name in upload_result.get('success', []):
                mensagem_lines.append(f"OK: {name}")
            for err in upload_result.get('errors', []):
                mensagem_lines.append(f"ERRO: {err.get('file','')} - {err.get('error','')}")
            for p in upload_result.get('pendentes', []):
                mensagem_lines.append(f"PENDENTES (empresa não cadastrada): {p.get('file','')} - {p.get('motivo','')}")
            resumo = '\n'.join(mensagem_lines)[:5000]

            # Montar prefixo com empresa (se enviada e válida)
            empresa_prefixo = ''
            if l_v_empresa_id:
                try:
                    empresa = Empresas.objects.get(
                        cod_empresa=l_v_empresa_id,
                        cliente__cod_cliente=cod_cliente
                    )
                    nome_emp = empresa.fantasia or empresa.razao or empresa.cod_empresa
                    empresa_prefixo = f"EMPRESA: {empresa.cod_empresa} - {nome_emp}\n"
                except Empresas.DoesNotExist:
                    empresa_prefixo = f"EMPRESA: {l_v_empresa_id} (não encontrada)\n"

            total_arquivos = len(upload_result['success']) + len(upload_result['errors']) + len(upload_result.get('pendentes', []))
            CargaXmlJob.objects.create(
                cliente=get_object_or_404(Clientes, cod_cliente=cod_cliente),
                parametro=None,
                status='SUCCESS' if len(upload_result['errors']) == 0 else 'ERROR',
                total_arquivos=total_arquivos,
                total_sucesso=len(upload_result['success']),
                total_erro=len(upload_result['errors']),
                mensagem=(empresa_prefixo + resumo)[:5000],
                started_at=timezone.localtime(),
                finished_at=timezone.localtime(),
                usuario_execucao=request.user
            )
        except Exception:
            pass

        pendentes_count = len(upload_result.get('pendentes', []))
        msg = f"{len(upload_result['success'])} arquivo(s) registrado(s), {len(upload_result['errors'])} erro(s)"
        if pendentes_count:
            msg += f", {pendentes_count} enviado(s) para pendentes (empresa não cadastrada no GDF - não registrado)"
        return JsonResponse({
            'sucesso': len(upload_result['errors']) == 0,
            'mensagem': msg,
            'detalhes': upload_result
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao processar: {str(e)}'}, status=500)


@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_api_cargaxml_parametros(request):
    cod_cliente = request.session.get('cod_cliente', None)

    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)

    if request.method == "GET":
        apenas_ativos = request.GET.get('ativo')
        parametros = CargaXmlParam.objects.filter(cliente=cliente)

        if apenas_ativos in ['1', 'true', 'True', 'yes', 'sim']:
            parametros = parametros.filter(ativo=True)

        items = []
        for param in parametros.order_by('-data_criacao'):
            items.append({
                'id': param.id,
                'ativo': param.ativo,
                'horario': param.horario.strftime('%H:%M'),
                'origem_dados': param.origem_dados,
                'diretorio': param.diretorio,
                'empresa_id': param.empresa.cod_empresa if param.empresa else None,
                'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
                'ultima_execucao': param.ultima_execucao.isoformat() if param.ultima_execucao else None,
            })

        return JsonResponse({'sucesso': True, 'items': items}, status=200)
    
    elif request.method == "POST":
        # Processar criação de novo parâmetro
        payload = None
        if request.content_type and 'application/json' in request.content_type:
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST

        horario_raw = (payload.get('horario') or '').strip()
        origem_dados = (payload.get('origem_dados') or 'LOCAL').strip().upper()
        diretorio = (payload.get('diretorio') or '').strip()
        empresa_id = (payload.get('empresa_id') or '').strip()
        ativo_raw = payload.get('ativo', True)

        if not horario_raw or not diretorio:
            return JsonResponse({'sucesso': False, 'mensagem': 'Horario e diretorio sao obrigatorios'}, status=400)

        try:
            horario = datetime.strptime(horario_raw, '%H:%M').time()
        except ValueError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Horario invalido. Use HH:MM'}, status=400)

        ativo = True
        if isinstance(ativo_raw, str):
            ativo = ativo_raw.lower() in ['1', 'true', 'yes', 'sim', 'on']
        else:
            ativo = bool(ativo_raw)

        empresa = None
        if empresa_id:
            try:
                empresa = Empresas.objects.get(cod_empresa=empresa_id, cliente=cliente)
            except Empresas.DoesNotExist:
                return JsonResponse({'sucesso': False, 'mensagem': 'Empresa nao encontrada'}, status=404)

        param = CargaXmlParam.objects.create(
            cliente=cliente,
            empresa=empresa,
            ativo=ativo,
            horario=horario,
            origem_dados=origem_dados,
            diretorio=diretorio,
            usuario_criacao=request.user,
            data_atualizacao=timezone.localtime(),
        )

        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Parametro salvo com sucesso',
            'item': {
                'id': param.id,
                'ativo': param.ativo,
                'horario': param.horario.strftime('%H:%M'),
                'origem_dados': param.origem_dados,
                'diretorio': param.diretorio,
                'empresa_id': param.empresa.cod_empresa if param.empresa else None,
                'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
            }
        }, status=201)


@login_required(login_url='Login')
@require_http_methods(["GET", "PUT"])
def fn_api_cargaxml_parametro_detail(request, param_id):
    """Endpoint para obter ou atualizar um parâmetro específico (GET / PUT)."""
    cod_cliente = request.session.get('cod_cliente', None)

    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)
    param = get_object_or_404(CargaXmlParam, id=param_id, cliente=cliente)

    if request.method == 'GET':
        param_data = {
            'id': param.id,
            'ativo': param.ativo,
            'horario': param.horario.strftime('%H:%M'),
            'origem_dados': param.origem_dados,
            'diretorio': param.diretorio,
            'empresa_id': param.empresa.cod_empresa if param.empresa else None,
            'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
            'ultima_execucao': param.ultima_execucao.isoformat() if param.ultima_execucao else None,
        }
        return JsonResponse({'sucesso': True, 'parametro': param_data}, status=200)

    # PUT -> atualizar parâmetro
    payload = None
    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'sucesso': False, 'mensagem': 'Payload JSON invalido'}, status=400)
    else:
        payload = request.POST

    horario_raw = (payload.get('horario') or '').strip()
    origem_dados = (payload.get('origem_dados') or param.origem_dados).strip().upper()
    diretorio = (payload.get('diretorio') or param.diretorio).strip()
    empresa_id = (payload.get('empresa_id') or (param.empresa.cod_empresa if param.empresa else '')).strip()
    ativo_raw = payload.get('ativo', param.ativo)

    if not horario_raw or not diretorio:
        return JsonResponse({'sucesso': False, 'mensagem': 'Horario e diretorio sao obrigatorios'}, status=400)

    try:
        horario = datetime.strptime(horario_raw, '%H:%M').time()
    except ValueError:
        return JsonResponse({'sucesso': False, 'mensagem': 'Horario invalido. Use HH:MM'}, status=400)

    ativo = True
    if isinstance(ativo_raw, str):
        ativo = ativo_raw.lower() in ['1', 'true', 'yes', 'sim', 'on']
    else:
        ativo = bool(ativo_raw)

    if empresa_id:
        try:
            param.empresa = Empresas.objects.get(cod_empresa=empresa_id, cliente=cliente)
        except Empresas.DoesNotExist:
            return JsonResponse({'sucesso': False, 'mensagem': 'Empresa nao encontrada'}, status=404)
    else:
        param.empresa = None

    # Aplicar alterações
    param.horario = horario
    param.origem_dados = origem_dados
    param.diretorio = diretorio
    param.ativo = ativo
    param.data_atualizacao = timezone.localtime()
    param.save(update_fields=['horario', 'origem_dados', 'diretorio', 'empresa', 'ativo', 'data_atualizacao'])

    return JsonResponse({'sucesso': True, 'mensagem': 'Parametro atualizado com sucesso'}, status=200)


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_cargaxml_upload_zip(request, param_id):
    """Envia um arquivo ZIP para a pasta do parâmetro; extrai apenas .xml para o diretório do job."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)
    param = get_object_or_404(CargaXmlParam, id=param_id, cliente=cliente)

    arquivo_zip = request.FILES.get('arquivo_zip')
    if not arquivo_zip:
        return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum arquivo ZIP enviado'}, status=400)
    if not (arquivo_zip.name or '').lower().endswith('.zip'):
        return JsonResponse({'sucesso': False, 'mensagem': 'Arquivo deve ser .zip'}, status=400)
    if arquivo_zip.size > 100 * 1024 * 1024:
        return JsonResponse({'sucesso': False, 'mensagem': 'ZIP muito grande (max 100MB)'}, status=400)

    base_dir = Path(param.diretorio)
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        base_dir = base_dir.resolve()
    except OSError as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Diretorio invalido ou inacessivel: {e}'}, status=400)

    extraidos = 0
    try:
        with zipfile.ZipFile(arquivo_zip, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('/') or not name.lower().endswith('.xml'):
                    continue
                # Evitar path traversal: extrair apenas o nome do arquivo na pasta base
                safe_name = Path(name).name
                if not safe_name or '..' in safe_name:
                    continue
                dest_path = base_dir / safe_name
                try:
                    dest_path = dest_path.resolve()
                    if not str(dest_path).startswith(str(base_dir)):
                        continue
                except Exception:
                    continue
                try:
                    with zf.open(name, 'r') as src:
                        dest_path.write_bytes(src.read())
                    extraidos += 1
                except Exception:
                    pass
    except zipfile.BadZipFile:
        return JsonResponse({'sucesso': False, 'mensagem': 'Arquivo ZIP invalido ou corrompido'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao extrair ZIP: {str(e)}'}, status=500)

    return JsonResponse({
        'sucesso': True,
        'mensagem': f'ZIP processado: {extraidos} arquivo(s) XML extraido(s) para a pasta do job.',
        'extraidos': extraidos
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargaxml_relatorio(request):
    """Relatório de ajuste para parâmetros de carga (diretório existe, último job)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)
    parametros = CargaXmlParam.objects.filter(cliente=cliente)
    items = []

    import os
    for param in parametros.order_by('horario'):
        dir_exists = os.path.isdir(param.diretorio)
        last_job = CargaXmlJob.objects.filter(parametro=param).order_by('-started_at').first()
        items.append({
            'id': param.id,
            'ativo': param.ativo,
            'horario': param.horario.strftime('%H:%M'),
            'origem_dados': param.origem_dados,
            'diretorio': param.diretorio,
            'empresa_id': param.empresa.cod_empresa if param.empresa else None,
            'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
            'dir_exists': dir_exists,
            'ultima_execucao': param.ultima_execucao.isoformat() if param.ultima_execucao else None,
            'last_job_status': last_job.status if last_job else None,
            'last_job_total': last_job.total_arquivos if last_job else None,
            'last_job_success': last_job.total_sucesso if last_job else None,
            'last_job_error': last_job.total_erro if last_job else None,
            'last_job_msg': last_job.mensagem if last_job else None,
            'last_job_started': last_job.started_at.isoformat() if last_job and last_job.started_at else None,
            'last_job_finished': last_job.finished_at.isoformat() if last_job and last_job.finished_at else None,
        })

    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_cargaxml_param_toggle(request, param_id):
    cod_cliente = request.session.get('cod_cliente', None)

    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)
    param = get_object_or_404(CargaXmlParam, id=param_id, cliente=cliente)

    ativo_raw = None
    if request.content_type and 'application/json' in request.content_type:
        body = json.loads(request.body.decode('utf-8'))
        ativo_raw = body.get('ativo')
    else:
        ativo_raw = request.POST.get('ativo')

    if ativo_raw is None:
        param.ativo = not param.ativo
    else:
        if isinstance(ativo_raw, str):
            param.ativo = ativo_raw.lower() in ['1', 'true', 'yes', 'sim', 'on']
        else:
            param.ativo = bool(ativo_raw)

    param.save(update_fields=['ativo', 'data_atualizacao'])

    return JsonResponse({
        'sucesso': True,
        'id': param.id,
        'ativo': param.ativo,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_sessao_cliente(request):
    """Define o cliente ativo na sessão (apenas superuser). Uso: troca de contexto multi-cliente."""
    if not request.session.get('is_superuser', False):
        return JsonResponse({'sucesso': False, 'erro': 'Acesso negado'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
        cod_cliente = (body.get('cod_cliente') or request.POST.get('cod_cliente') or '').strip()
        if not cod_cliente:
            return JsonResponse({'sucesso': False, 'erro': 'cod_cliente obrigatório'}, status=400)
        if not Clientes.objects.filter(cod_cliente=cod_cliente, is_active=True).exists():
            return JsonResponse({'sucesso': False, 'erro': 'Cliente não encontrado ou inativo'}, status=400)
        request.session['cod_cliente'] = cod_cliente
        return JsonResponse({'sucesso': True, 'cod_cliente': cod_cliente}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'JSON inválido'}, status=400)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_debug_session(request):
    """Debug endpoint para verificar sessão e cliente"""
    cod_cliente = request.session.get('cod_cliente', None)
    return JsonResponse({
        'usuario': request.user.username,
        'cod_cliente': cod_cliente,
        'session_keys': list(request.session.keys()),
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargaxml_avisos(request):
    """Retorna jobs de carga XML com status ERROR (para o botão Avisos e modal de logs)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)
    jobs = CargaXmlJob.objects.filter(
        cliente__cod_cliente=cod_cliente,
        status='ERROR'
    ).order_by('-started_at')[:100]
    items = []
    for job in jobs:
        log_lines = [line.strip() for line in (job.mensagem or '').splitlines() if line.strip()]
        items.append({
            'id': job.id,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
            'total_arquivos': job.total_arquivos,
            'total_sucesso': job.total_sucesso,
            'total_erro': job.total_erro,
            'mensagem': job.mensagem or '',
            'log': log_lines,
        })
    return JsonResponse({'sucesso': True, 'total_erros': len(items), 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargaxml_jobs(request):
    """Lista todos os jobs de carga XML do cliente"""
    import sys
    cod_cliente = request.session.get('cod_cliente', None)
    print(f"DEBUG: cod_cliente={cod_cliente}", file=sys.stderr)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    jobs = CargaXmlJob.objects.filter(cliente__cod_cliente=cod_cliente).order_by('-started_at')
    print(f"DEBUG: Found {jobs.count()} jobs", file=sys.stderr)
    items = []
    for job in jobs:
        items.append({
            'id': job.id,
            'status': job.status,
            'total_arquivos': job.total_arquivos,
            'total_sucesso': job.total_sucesso,
            'total_erro': job.total_erro,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
            'parametro_id': job.parametro.id if job.parametro else None,
        })
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargaxml_job_details(request, job_id):
    """Retorna detalhes e log de um job específico"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente nao identificado'}, status=403)

    job = get_object_or_404(CargaXmlJob, id=job_id, cliente__cod_cliente=cod_cliente)
    log_lines = [line.strip() for line in (job.mensagem or '').splitlines() if line.strip()]
    param_data = None
    if job.parametro:
        p = job.parametro
        param_data = {
            'id': p.id,
            'ativo': p.ativo,
            'horario': p.horario.strftime('%H:%M'),
            'origem_dados': p.origem_dados,
            'diretorio': p.diretorio,
            'empresa_id': p.empresa.cod_empresa if p.empresa else None,
            'empresa_nome': p.empresa.fantasia or p.empresa.razao if p.empresa else '',
            'ultima_execucao': p.ultima_execucao.isoformat() if p.ultima_execucao else None,
        }
    return JsonResponse({
        'sucesso': True,
        'job': {
            'id': job.id,
            'status': job.status,
            'total_arquivos': job.total_arquivos,
            'total_sucesso': job.total_sucesso,
            'total_erro': job.total_erro,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        },
        'parametro': param_data,
        'log': log_lines,
    }, status=200)


# ========== APIs Carga SPED (mesma linha de raciocínio da Carga XML) ==========

@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_processar_sped(request):
    """API para processar upload de arquivos SPED (.txt)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    arquivos = request.FILES.getlist('arquivo')
    tipo_sped = request.POST.get('tipo_sped', 'EFD_ICMS')
    if not arquivos:
        return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum arquivo selecionado'}, status=400)
    cl_sped = Carga_sped()
    upload_result = cl_sped.set_upload_sped(arquivos, tipo_sped, request.user.username, cod_cliente)
    try:
        cliente = Clientes.objects.get(cod_cliente=cod_cliente)
        total = len(upload_result['success']) + len(upload_result['errors'])
        CargaSpedJob.objects.create(
            cliente=cliente,
            parametro=None,
            status='SUCCESS' if len(upload_result['errors']) == 0 else 'ERROR',
            total_arquivos=total,
            total_sucesso=len(upload_result['success']),
            total_erro=len(upload_result['errors']),
            mensagem='\n'.join([f"OK: {n}" for n in upload_result['success']] + [f"ERRO: {e.get('file','')} - {e.get('error','')}" for e in upload_result['errors']])[:5000],
            started_at=timezone.localtime(),
            finished_at=timezone.localtime(),
            usuario_execucao=request.user
        )
    except Exception:
        pass
    return JsonResponse({
        'sucesso': len(upload_result['errors']) == 0,
        'mensagem': f"{len(upload_result['success'])} arquivo(s) recebido(s), {len(upload_result['errors'])} erro(s).",
        'total_sucesso': len(upload_result['success']),
        'total_erro': len(upload_result['errors']),
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_api_cargasped_parametros(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)

    if request.method == "GET":
        parametros = CargaSpedParam.objects.filter(cliente=cliente)
        items = []
        for param in parametros.order_by('-data_criacao'):
            items.append({
                'id': param.id,
                'ativo': param.ativo,
                'horario': param.horario.strftime('%H:%M'),
                'tipo_sped': param.tipo_sped,
                'diretorio': param.diretorio,
                'empresa_id': param.empresa.cod_empresa if param.empresa else None,
                'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
                'ultima_execucao': param.ultima_execucao.isoformat() if param.ultima_execucao else None,
            })
        return JsonResponse({'sucesso': True, 'items': items}, status=200)

    elif request.method == "POST":
        payload = json.loads(request.body.decode('utf-8')) if request.content_type and 'application/json' in request.content_type else request.POST
        horario_raw = (payload.get('horario') or '').strip()
        tipo_sped = (payload.get('tipo_sped') or 'EFD_ICMS').strip()
        diretorio = (payload.get('diretorio') or '').strip()
        empresa_id = (payload.get('empresa_id') or '').strip()
        ativo = payload.get('ativo', True)
        if isinstance(ativo, str):
            ativo = ativo.lower() in ['1', 'true', 'yes', 'sim', 'on']
        else:
            ativo = bool(ativo)
        if not horario_raw or not diretorio:
            return JsonResponse({'sucesso': False, 'mensagem': 'Horário e diretório são obrigatórios'}, status=400)
        try:
            from datetime import datetime
            horario = datetime.strptime(horario_raw, '%H:%M').time()
        except ValueError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Horário inválido. Use HH:MM'}, status=400)
        empresa = None
        if empresa_id:
            try:
                empresa = Empresas.objects.get(cod_empresa=empresa_id, cliente=cliente)
            except Empresas.DoesNotExist:
                return JsonResponse({'sucesso': False, 'mensagem': 'Empresa não encontrada'}, status=404)
        param = CargaSpedParam.objects.create(
            cliente=cliente,
            empresa=empresa,
            ativo=ativo,
            horario=horario,
            tipo_sped=tipo_sped,
            diretorio=diretorio,
            usuario_criacao=request.user,
        )
        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Parâmetro salvo com sucesso',
            'item': {
                'id': param.id,
                'ativo': param.ativo,
                'horario': param.horario.strftime('%H:%M'),
                'tipo_sped': param.tipo_sped,
                'diretorio': param.diretorio,
                'empresa_id': param.empresa.cod_empresa if param.empresa else None,
                'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
            }
        }, status=201)


@login_required(login_url='Login')
@require_http_methods(["GET", "PUT"])
def fn_api_cargasped_parametro_detail(request, param_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    param = get_object_or_404(CargaSpedParam, id=param_id, cliente__cod_cliente=cod_cliente)

    if request.method == "GET":
        return JsonResponse({
            'sucesso': True,
            'item': {
                'id': param.id,
                'ativo': param.ativo,
                'horario': param.horario.strftime('%H:%M'),
                'tipo_sped': param.tipo_sped,
                'diretorio': param.diretorio,
                'empresa_id': param.empresa.cod_empresa if param.empresa else None,
                'empresa_nome': param.empresa.fantasia or param.empresa.razao if param.empresa else '',
                'ultima_execucao': param.ultima_execucao.isoformat() if param.ultima_execucao else None,
            }
        }, status=200)

    elif request.method == "PUT":
        payload = json.loads(request.body.decode('utf-8'))
        if 'horario' in payload:
            try:
                param.horario = datetime.strptime((payload['horario'] or '').strip(), '%H:%M').time()
            except ValueError:
                pass
        if 'tipo_sped' in payload:
            param.tipo_sped = (payload['tipo_sped'] or param.tipo_sped).strip() or 'EFD_ICMS'
        if 'diretorio' in payload:
            param.diretorio = (payload['diretorio'] or '').strip()
        if 'empresa_id' in payload:
            if payload.get('empresa_id'):
                try:
                    param.empresa = Empresas.objects.get(cod_empresa=payload['empresa_id'], cliente__cod_cliente=cod_cliente)
                except Empresas.DoesNotExist:
                    pass
            else:
                param.empresa = None
        if 'ativo' in payload:
            param.ativo = payload['ativo'] in [True, 'true', '1', 'yes', 'sim']
        param.save(update_fields=['horario', 'tipo_sped', 'diretorio', 'empresa', 'ativo', 'data_atualizacao'])
        return JsonResponse({'sucesso': True, 'mensagem': 'Parâmetro atualizado'}, status=200)


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_cargasped_upload_zip(request, param_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    cliente = get_object_or_404(Clientes, cod_cliente=cod_cliente)
    param = get_object_or_404(CargaSpedParam, id=param_id, cliente=cliente)
    arquivo_zip = request.FILES.get('arquivo_zip')
    if not arquivo_zip or not (arquivo_zip.name or '').lower().endswith('.zip'):
        return JsonResponse({'sucesso': False, 'mensagem': 'Envie um arquivo .zip'}, status=400)
    if arquivo_zip.size > 100 * 1024 * 1024:
        return JsonResponse({'sucesso': False, 'mensagem': 'ZIP muito grande (máx 100MB)'}, status=400)
    base_dir = Path(param.diretorio)
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        base_dir = base_dir.resolve()
    except OSError as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Diretório inválido: {e}'}, status=400)
    extraidos = 0
    try:
        with zipfile.ZipFile(arquivo_zip, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('/') or not name.lower().endswith('.txt'):
                    continue
                safe_name = Path(name).name
                if not safe_name or '..' in safe_name:
                    continue
                dest_path = base_dir / safe_name
                try:
                    dest_path = dest_path.resolve()
                    if not str(dest_path).startswith(str(base_dir)):
                        continue
                except Exception:
                    continue
                try:
                    with zf.open(name, 'r') as src:
                        dest_path.write_bytes(src.read())
                    extraidos += 1
                except Exception:
                    pass
    except zipfile.BadZipFile:
        return JsonResponse({'sucesso': False, 'mensagem': 'ZIP inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)
    return JsonResponse({'sucesso': True, 'mensagem': f'{extraidos} arquivo(s) SPED (.txt) extraído(s).', 'extraidos': extraidos}, status=200)


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_cargasped_param_toggle(request, param_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    param = get_object_or_404(CargaSpedParam, id=param_id, cliente__cod_cliente=cod_cliente)
    body = json.loads(request.body.decode('utf-8')) if request.content_type and 'application/json' in request.content_type else {}
    ativo_raw = body.get('ativo', request.POST.get('ativo'))
    if ativo_raw is None:
        param.ativo = not param.ativo
    else:
        param.ativo = ativo_raw in [True, 'true', '1', 'yes', 'sim', 'on'] if isinstance(ativo_raw, str) else bool(ativo_raw)
    param.save(update_fields=['ativo', 'data_atualizacao'])
    return JsonResponse({'sucesso': True, 'id': param.id, 'ativo': param.ativo}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargasped_avisos(request):
    """Retorna jobs de carga SPED com status ERROR (para o botão Avisos e modal de logs)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    jobs = CargaSpedJob.objects.filter(
        cliente__cod_cliente=cod_cliente,
        status='ERROR'
    ).order_by('-started_at')[:100]
    items = []
    for job in jobs:
        log_lines = [line.strip() for line in (job.mensagem or '').splitlines() if line.strip()]
        items.append({
            'id': job.id,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
            'total_arquivos': job.total_arquivos,
            'total_sucesso': job.total_sucesso,
            'total_erro': job.total_erro,
            'mensagem': job.mensagem or '',
            'log': log_lines,
        })
    return JsonResponse({'sucesso': True, 'total_erros': len(items), 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargasped_jobs(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    jobs = CargaSpedJob.objects.filter(cliente__cod_cliente=cod_cliente).order_by('-started_at')
    items = [{
        'id': j.id,
        'status': j.status,
        'total_arquivos': j.total_arquivos,
        'total_sucesso': j.total_sucesso,
        'total_erro': j.total_erro,
        'started_at': j.started_at.isoformat() if j.started_at else None,
        'finished_at': j.finished_at.isoformat() if j.finished_at else None,
        'parametro_id': j.parametro.id if j.parametro else None,
    } for j in jobs]
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_cargasped_job_details(request, job_id):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    job = get_object_or_404(CargaSpedJob, id=job_id, cliente__cod_cliente=cod_cliente)
    log_lines = [line.strip() for line in (job.mensagem or '').splitlines() if line.strip()]
    param_data = None
    if job.parametro:
        p = job.parametro
        param_data = {
            'id': p.id, 'ativo': p.ativo,
            'horario': p.horario.strftime('%H:%M'),
            'tipo_sped': p.tipo_sped,
            'diretorio': p.diretorio,
            'empresa_id': p.empresa.cod_empresa if p.empresa else None,
            'empresa_nome': p.empresa.fantasia or p.empresa.razao if p.empresa else '',
            'ultima_execucao': p.ultima_execucao.isoformat() if p.ultima_execucao else None,
        }
    return JsonResponse({
        'sucesso': True,
        'job': {
            'id': job.id, 'status': job.status,
            'total_arquivos': job.total_arquivos,
            'total_sucesso': job.total_sucesso,
            'total_erro': job.total_erro,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        },
        'parametro': param_data,
        'log': log_lines,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_view_CargaSped(request):
    """View para carregamento de arquivos SPED (mesma linha de raciocínio da Carga XML)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Cliente não identificado'})
    try:
        cliente = Clientes.objects.get(cod_cliente=cod_cliente)
        jobs = CargaSpedJob.objects.filter(cliente=cliente).order_by('-started_at')
        parametros = CargaSpedParam.objects.filter(cliente=cliente).order_by('-data_criacao')
        empresas_usuario = Empresas.objects.filter(
            cliente=cliente,
            userempresas__user=request.user
        ).order_by('fantasia', 'razao', 'cod_empresa').distinct()
    except Clientes.DoesNotExist:
        jobs = []
        parametros = []
        empresas_usuario = []
    context = {
        'cod_cliente': cod_cliente,
        'jobs': jobs,
        'parametros': parametros,
        'empresas_usuario': empresas_usuario,
    }
    return render(request, 'Processamento/index_CargaSped.html', context)


# ========== APIs Relatório Fiscal (NFe, CTe, NFS, SPED nível cabeçalho) ==========

def _relatorio_empresas_queryset(request):
    """Retorna queryset de empresas do cliente que o usuário pode acessar."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return Empresas.objects.none()
    return Empresas.objects.filter(
        cliente__cod_cliente=cod_cliente,
        userempresas__user=request.user
    ).distinct()


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_nfe(request):
    """Lista NFe nível cabeçalho com filtros empresa e período."""
    empresas = _relatorio_empresas_queryset(request)
    if not empresas.exists():
        return JsonResponse({'sucesso': True, 'items': []}, status=200)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    empresa_id = request.GET.get('empresa_id', '').strip()
    if empresa_id:
        cod_empresas = [empresa_id] if empresa_id in cod_empresas else []
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    busca = request.GET.get('busca', '').strip()
    parcelas = request.GET.get('parcelas', '').strip()
    tipo_operacao = request.GET.get('tipo_operacao', '').strip()  # '0'=Entrada, '1'=Saída
    tipo_pagamento = request.GET.get('tipo_pagamento', '').strip()  # código meio_pagamento (01, 02, 20, etc.)

    qs = NFe.objects.filter(empresa__cod_empresa__in=cod_empresas).select_related('identificacao', 'empresa')
    if tipo_operacao in ('0', '1'):
        qs = qs.filter(identificacao__tipo_operacao=tipo_operacao)
    if tipo_pagamento:
        qs = qs.filter(identificacao__pagamento__meio_pagamento=tipo_pagamento)
    if parcelas != '':
        try:
            qtd = int(parcelas)
            if qtd >= 0:
                qs = qs.annotate(num_parcelas=Count('identificacao__cobranca__parcelas', distinct=True)).filter(num_parcelas=qtd)
        except ValueError:
            pass
    if busca:
        qs = qs.filter(
            Q(identificacao__chave_acesso__icontains=busca) |
            Q(identificacao__numero__icontains=busca) |
            Q(identificacao__serie__icontains=busca) |
            Q(status__icontains=busca) |
            Q(identificacao__natureza_operacao__icontains=busca)
        )
    if data_inicio:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_inicio)
            if dt:
                qs = qs.filter(identificacao__emissao__date__gte=dt)
        except Exception:
            pass
    if data_fim:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_fim)
            if dt:
                qs = qs.filter(identificacao__emissao__date__lte=dt)
        except Exception:
            pass
    qs = qs.order_by('-identificacao__emissao')[:500]
    items = []
    for nfe in qs:
        id_ = nfe.identificacao
        items.append({
            'id_nfe': nfe.id_nfe,
            'numero': id_.numero,
            'serie': id_.serie,
            'chave': id_.chave_acesso,
            'emissao': id_.emissao.isoformat() if id_.emissao else None,
            'tipo_operacao': id_.tipo_operacao,
            'status': nfe.status,
            'empresa': nfe.empresa.cod_empresa if nfe.empresa else None,
            'natureza': id_.natureza_operacao,
        })
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_cte(request):
    """Lista CTe nível cabeçalho com filtros."""
    empresas = _relatorio_empresas_queryset(request)
    if not empresas.exists():
        return JsonResponse({'sucesso': True, 'items': []}, status=200)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    empresa_id = request.GET.get('empresa_id', '').strip()
    if empresa_id:
        cod_empresas = [empresa_id] if empresa_id in cod_empresas else []
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    busca = request.GET.get('busca', '').strip()

    qs = CTe.objects.filter(empresa__cod_empresa__in=cod_empresas).select_related('identificacao', 'empresa')
    if busca:
        qs = qs.filter(
            Q(identificacao__chave_acesso__icontains=busca) |
            Q(identificacao__numero__icontains=busca) |
            Q(identificacao__serie__icontains=busca)
        )
    if data_inicio:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_inicio)
            if dt:
                qs = qs.filter(identificacao__emissao__date__gte=dt)
        except Exception:
            pass
    if data_fim:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_fim)
            if dt:
                qs = qs.filter(identificacao__emissao__date__lte=dt)
        except Exception:
            pass
    qs = qs.order_by('-identificacao__emissao')[:500]
    items = []
    for cte in qs:
        id_ = cte.identificacao
        items.append({
            'id_cte': cte.id_cte,
            'numero': id_.numero,
            'serie': id_.serie,
            'chave': id_.chave_acesso,
            'emissao': id_.emissao.isoformat() if id_.emissao else None,
            'empresa': cte.empresa.cod_empresa if cte.empresa else None,
        })
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_nfse(request):
    """Lista NFSe nível cabeçalho com filtros."""
    empresas = _relatorio_empresas_queryset(request)
    if not empresas.exists():
        return JsonResponse({'sucesso': True, 'items': []}, status=200)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    empresa_id = request.GET.get('empresa_id', '').strip()
    if empresa_id:
        cod_empresas = [empresa_id] if empresa_id in cod_empresas else []
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    busca = request.GET.get('busca', '').strip()

    qs = NFSe.objects.filter(empresa__cod_empresa__in=cod_empresas).select_related('identificacao', 'empresa')
    if busca:
        qs = qs.filter(
            Q(identificacao__chave__icontains=busca) |
            Q(identificacao__numero__icontains=busca)
        )
    if data_inicio:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_inicio)
            if dt:
                qs = qs.filter(identificacao__emissao__date__gte=dt)
        except Exception:
            pass
    if data_fim:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_fim)
            if dt:
                qs = qs.filter(identificacao__emissao__date__lte=dt)
        except Exception:
            pass
    qs = qs.order_by('-identificacao__emissao')[:500]
    items = []
    for nfse in qs:
        id_ = nfse.identificacao
        items.append({
            'id_nfse': nfse.id_nfse,
            'numero': id_.numero,
            'chave': id_.chave,
            'emissao': id_.emissao.isoformat() if id_.emissao else None,
            'empresa': nfse.empresa.cod_empresa if nfse.empresa else None,
        })
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_sped(request):
    """Lista SPED nível cabeçalho (Sped_Arquivo) com filtros. tipo: C=Contribuição, F=Fiscal."""
    empresas = _relatorio_empresas_queryset(request)
    if not empresas.exists():
        return JsonResponse({'sucesso': True, 'items': []}, status=200)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    empresa_id = request.GET.get('empresa_id', '').strip()
    if empresa_id:
        cod_empresas = [empresa_id] if empresa_id in cod_empresas else []
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    busca = request.GET.get('busca', '').strip()

    qs = Sped_Arquivo.objects.filter(empresa__cod_empresa__in=cod_empresas).select_related('empresa')
    if busca:
        qs = qs.filter(
            Q(nome_arquivo__icontains=busca) |
            Q(tipo__icontains=busca)
        )
    if data_inicio:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_inicio)
            if dt:
                qs = qs.filter(competencia__gte=dt)
        except Exception:
            pass
    if data_fim:
        try:
            from django.utils.dateparse import parse_date
            dt = parse_date(data_fim)
            if dt:
                qs = qs.filter(competencia__lte=dt)
        except Exception:
            pass
    qs = qs.order_by('-data_carga')[:500]
    items = []
    for arq in qs:
        items.append({
            'id_arquivo': arq.id_arquivo,
            'tipo': arq.tipo,
            'tipo_display': arq.get_tipo_display(),
            'competencia': arq.competencia.isoformat() if arq.competencia else None,
            'nome_arquivo': arq.nome_arquivo,
            'data_carga': arq.data_carga.isoformat() if arq.data_carga else None,
            'empresa': arq.empresa.cod_empresa if arq.empresa else None,
        })
    return JsonResponse({'sucesso': True, 'items': items}, status=200)


def _serialize_model(inst, exclude=None):
    """Converte um model instance em dict para JSON (datas e decimals já serializáveis)."""
    if inst is None:
        return None
    exclude = set(exclude or [])
    from django.forms.models import model_to_dict
    d = model_to_dict(inst, exclude=exclude)
    for k, v in list(d.items()):
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat() if v else None
        elif hasattr(v, '__float__') and not isinstance(v, (bool, int)):
            try:
                d[k] = float(v)
            except (TypeError, ValueError):
                pass
    return d


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_nfe_detalhe(request, id_nfe):
    """Detalhe completo da NFe para modal: cabeçalho, itens, total, cobrança/parcelas, pagamento, transporte, info adicionais."""
    empresas = _relatorio_empresas_queryset(request)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    nfe = get_object_or_404(
        NFe.objects.select_related(
            'identificacao', 'emitente', 'destinatario', 'empresa',
            'emitente__endereco', 'destinatario__endereco',
        ).prefetch_related(
            'identificacao__produtos__icms',
            'identificacao__produtos__pis',
            'identificacao__produtos__cofins',
            'identificacao__produtos__ipi',
            'identificacao__totalizacao',
            'identificacao__cobranca__parcelas',
            'identificacao__pagamento',
            'identificacao__transporte',
            'identificacao__informacoes_adicionais',
        ),
        id_nfe=id_nfe,
        empresa__cod_empresa__in=cod_empresas,
    )
    ide = nfe.identificacao
    cabecalho = {
        'identificacao': _serialize_model(ide),
        'emitente': _serialize_model(nfe.emitente),
        'destinatario': _serialize_model(nfe.destinatario),
        'nfe': _serialize_model(nfe, exclude=['identificacao', 'emitente', 'destinatario', 'empresa']),
        'empresa': nfe.empresa.cod_empresa if nfe.empresa else None,
    }
    if nfe.emitente and nfe.emitente.endereco:
        cabecalho['emitente_endereco'] = _serialize_model(nfe.emitente.endereco)
    if nfe.destinatario and nfe.destinatario.endereco:
        cabecalho['destinatario_endereco'] = _serialize_model(nfe.destinatario.endereco)
    itens = []
    for p in ide.produtos.all().order_by('numero_item'):
        item = _serialize_model(p, exclude=['nfe_serie'])
        item['icms'] = _serialize_model(p.icms, exclude=['produto']) if getattr(p, 'icms', None) else None
        item['pis'] = _serialize_model(p.pis, exclude=['produto']) if getattr(p, 'pis', None) else None
        item['cofins'] = _serialize_model(p.cofins, exclude=['produto']) if getattr(p, 'cofins', None) else None
        item['ipi'] = _serialize_model(p.ipi, exclude=['produto']) if getattr(p, 'ipi', None) else None
        itens.append(item)
    totalizacao = _serialize_model(ide.totalizacao) if hasattr(ide, 'totalizacao') and ide.totalizacao else None
    cobranca = None
    parcelas = []
    try:
        if getattr(ide, 'cobranca', None):
            cobranca = _serialize_model(ide.cobranca, exclude=['nfe_identificacao'])
            parcelas = [_serialize_model(parc, exclude=['nfe_cobranca']) for parc in ide.cobranca.parcelas.all().order_by('numero_parcela')]
    except Exception:
        cobranca = None
        parcelas = []
    pagamento = None
    try:
        if getattr(ide, 'pagamento', None):
            pagamento = _serialize_model(ide.pagamento, exclude=['nfe_identificacao'])
            # Descrição do tipo de pagamento: json/Tipo_pagamento.json, senão display do model
            pagamento['tipo_pagamento'] = (
                _descricao_tipo_pagamento(ide.pagamento.meio_pagamento)
                or ide.pagamento.get_meio_pagamento_display()
            )
            if ide.pagamento.cartao_bandeira:
                pagamento['bandeira_cartao'] = ide.pagamento.get_cartao_bandeira_display()
            if ide.pagamento.pix_tipo_chave:
                pagamento['pix_tipo_chave_desc'] = ide.pagamento.get_pix_tipo_chave_display()
    except Exception:
        pagamento = None
    transporte = _serialize_model(ide.transporte) if hasattr(ide, 'transporte') and ide.transporte else None
    info_adic = _serialize_model(ide.informacoes_adicionais) if hasattr(ide, 'informacoes_adicionais') and ide.informacoes_adicionais else None
    return JsonResponse({
        'sucesso': True,
        'cabecalho': cabecalho,
        'itens': itens,
        'totalizacao': totalizacao,
        'cobranca': cobranca,
        'parcelas': parcelas,
        'pagamento': pagamento,
        'transporte': transporte,
        'informacoes_adicionais': info_adic,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_cte_detalhe(request, id_cte):
    """Detalhe completo do CTe para modal: cabeçalho, valor, transporte, carga, serviço, veículo, motorista, percurso, fiscal."""
    empresas = _relatorio_empresas_queryset(request)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    cte = get_object_or_404(
        CTe.objects.select_related(
            'identificacao', 'emitente', 'destinatario', 'empresa',
            'emitente__endereco', 'destinatario__endereco',
        ),
        id_cte=id_cte,
        empresa__cod_empresa__in=cod_empresas,
    )
    ide = cte.identificacao
    cabecalho = {
        'identificacao': _serialize_model(ide),
        'emitente': _serialize_model(cte.emitente),
        'destinatario': _serialize_model(cte.destinatario),
        'cte': _serialize_model(cte, exclude=['identificacao', 'emitente', 'destinatario', 'empresa']),
        'empresa': cte.empresa.cod_empresa if cte.empresa else None,
    }
    if cte.emitente and cte.emitente.endereco:
        cabecalho['emitente_endereco'] = _serialize_model(cte.emitente.endereco)
    if cte.destinatario and cte.destinatario.endereco:
        cabecalho['destinatario_endereco'] = _serialize_model(cte.destinatario.endereco)
    valor = _serialize_model(ide.valor) if hasattr(ide, 'valor') and ide.valor else None
    transporte = _serialize_model(ide.transporte) if hasattr(ide, 'transporte') and ide.transporte else None
    carga = _serialize_model(ide.carga) if hasattr(ide, 'carga') and ide.carga else None
    servico = _serialize_model(ide.servico) if hasattr(ide, 'servico') and ide.servico else None
    veiculo = _serialize_model(ide.veiculo) if hasattr(ide, 'veiculo') and ide.veiculo else None
    motorista = _serialize_model(ide.motorista) if hasattr(ide, 'motorista') and ide.motorista else None
    percurso = _serialize_model(ide.percurso) if hasattr(ide, 'percurso') and ide.percurso else None
    fiscal = _serialize_model(ide.fiscal) if hasattr(ide, 'fiscal') and ide.fiscal else None
    return JsonResponse({
        'sucesso': True,
        'cabecalho': cabecalho,
        'valor': valor,
        'transporte': transporte,
        'carga': carga,
        'servico': servico,
        'veiculo': veiculo,
        'motorista': motorista,
        'percurso': percurso,
        'fiscal': fiscal,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_nfse_detalhe(request, id_nfse):
    """Detalhe completo da NFSe para modal: cabeçalho, prestador, tomador, serviços, RPS, retenção, pagamento."""
    empresas = _relatorio_empresas_queryset(request)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    nfse = get_object_or_404(
        NFSe.objects.select_related(
            'identificacao', 'prestador', 'tomador', 'empresa',
            'prestador__endereco', 'tomador__endereco',
        ).prefetch_related(
            'identificacao__servicos',
            'identificacao__rps_list',
        ),
        id_nfse=id_nfse,
        empresa__cod_empresa__in=cod_empresas,
    )
    ide = nfse.identificacao
    cabecalho = {
        'identificacao': _serialize_model(ide),
        'prestador': _serialize_model(nfse.prestador),
        'tomador': _serialize_model(nfse.tomador),
        'nfse': _serialize_model(nfse, exclude=['identificacao', 'prestador', 'tomador', 'empresa']),
        'empresa': nfse.empresa.cod_empresa if nfse.empresa else None,
    }
    if nfse.prestador and nfse.prestador.endereco:
        cabecalho['prestador_endereco'] = _serialize_model(nfse.prestador.endereco)
    if nfse.tomador and nfse.tomador.endereco:
        cabecalho['tomador_endereco'] = _serialize_model(nfse.tomador.endereco)
    servicos = [_serialize_model(s) for s in ide.servicos.all()]
    rps_list = [_serialize_model(r) for r in ide.rps_list.all()]
    retencao = _serialize_model(ide.retencao) if hasattr(ide, 'retencao') and ide.retencao else None
    pagamento = _serialize_model(ide.pagamento) if hasattr(ide, 'pagamento') and ide.pagamento else None
    return JsonResponse({
        'sucesso': True,
        'cabecalho': cabecalho,
        'servicos': servicos,
        'rps': rps_list,
        'retencao': retencao,
        'pagamento': pagamento,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_relatorio_sped_detalhe(request, id_arquivo):
    """Detalhe do arquivo SPED: cabeçalho e registros fiscal/contribuição."""
    empresas = _relatorio_empresas_queryset(request)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    arq = get_object_or_404(
        Sped_Arquivo.objects.prefetch_related('registros_fiscal', 'registros_contribuicao').select_related('empresa'),
        id_arquivo=id_arquivo,
        empresa__cod_empresa__in=cod_empresas,
    )
    cabecalho = _serialize_model(arq)
    if cabecalho and 'empresa' in cabecalho:
        cabecalho['empresa'] = arq.empresa.cod_empresa if arq.empresa else None
    registros_fiscal = [{'bloco': r.bloco, 'registro': r.registro, 'conteudo': r.conteudo, 'linha': r.linha} for r in arq.registros_fiscal.all()[:500]]
    registros_contribuicao = [{'bloco': r.bloco, 'registro': r.registro, 'conteudo': r.conteudo, 'linha': r.linha} for r in arq.registros_contribuicao.all()[:500]]
    return JsonResponse({
        'sucesso': True,
        'cabecalho': cabecalho,
        'registros_fiscal': registros_fiscal,
        'registros_contribuicao': registros_contribuicao,
    }, status=200)


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_view_Relatorio_Fiscal(request):
    """Relatório com dados e filtros das tabelas carregadas: NFe, CTe, NFS e SPED (nível cabeçalho)."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Cliente não identificado'})
    try:
        cliente = Clientes.objects.get(cod_cliente=cod_cliente)
        empresas_usuario = Empresas.objects.filter(
            cliente=cliente,
            userempresas__user=request.user
        ).order_by('fantasia', 'razao', 'cod_empresa').distinct()
    except Clientes.DoesNotExist:
        empresas_usuario = []
    # Opções de tipo de pagamento (NFe) para o filtro do relatório (código 2 dígitos = valor no XML tPag)
    try:
        meio_pagamento_choices = list(
            NFe_Pagamento._meta.get_field('meio_pagamento').choices
        )
    except Exception:
        meio_pagamento_choices = []
    context = {
        'cod_cliente': cod_cliente,
        'empresas_usuario': empresas_usuario,
        'tipo_pagamento_json': json.dumps(TIPO_PAGAMENTO_DESC),
        'meio_pagamento_choices': meio_pagamento_choices,
    }
    return render(request, 'Processamento/index_Relatorio.html', context)


# -------------------------------------------------------------------------
# Reprocessamento – Solução com subsolução Painel (confronto SPED x NFe)
# -------------------------------------------------------------------------
@login_required(login_url='Login')
def fn_view_Reprocessamento(request):
    """Legado: redireciona para o Painel."""
    return redirect('Reproc_Painel')


@login_required(login_url='Login')
def fn_view_Reprocessamento_Painel(request):
    """Painel de Reprocessamento: confronto SPED x NFe, divergências e reprocessamento controlado."""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        context = {'cod_cliente': None, 'empresas': []}
        return render(request, 'Reprocessamento/index_Painel.html', context)
    empresas = list(
        Empresas.objects.filter(cliente_id=cod_cliente).values('cod_empresa', 'razao', 'fantasia').order_by('razao')
    )
    context = {
        'cod_cliente': cod_cliente,
        'empresas': empresas,
    }
    return render(request, 'Reprocessamento/index_Painel.html', context)


def _reprocessamento_empresas_cliente(cod_cliente):
    """Retorna lista de cod_empresa permitidos para o cliente (para filtrar lotes/divergências)."""
    if not cod_cliente:
        return []
    return list(Empresas.objects.filter(cliente_id=cod_cliente).values_list('cod_empresa', flat=True))


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_reprocessamento_lotes(request):
    """Lista lotes de reprocessamento do cliente (filtros: empresa, competência, status)."""
    cod_cliente = request.session.get('cod_cliente')
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    cod_empresas = _reprocessamento_empresas_cliente(cod_cliente)
    if not cod_empresas:
        return JsonResponse({'sucesso': True, 'lotes': [], 'total': 0})

    qs = ReprocessamentoLote.objects.filter(cod_empresa__in=cod_empresas)
    cod_empresa = request.GET.get('empresa')
    if cod_empresa and cod_empresa in cod_empresas:
        qs = qs.filter(cod_empresa=cod_empresa)
    competencia = request.GET.get('competencia')
    if competencia:
        competencia = competencia.strip()
        if len(competencia) == 7 and competencia[4] == '-':  # YYYY-MM
            from datetime import datetime
            try:
                dt_comp = datetime.strptime(competencia + '-01', '%Y-%m-%d').date()
                qs = qs.filter(competencia=dt_comp)
            except ValueError:
                pass
        else:
            try:
                from datetime import datetime
                dt_comp = datetime.strptime(competencia, '%Y-%m-%d').date()
                qs = qs.filter(competencia=dt_comp)
            except ValueError:
                pass
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    criado_de = request.GET.get('criado_de')  # YYYY-MM-DD
    criado_ate = request.GET.get('criado_ate')
    if criado_de:
        try:
            from datetime import datetime
            qs = qs.filter(data_criacao__date__gte=datetime.strptime(criado_de, '%Y-%m-%d').date())
        except ValueError:
            pass
    if criado_ate:
        try:
            from datetime import datetime
            qs = qs.filter(data_criacao__date__lte=datetime.strptime(criado_ate, '%Y-%m-%d').date())
        except ValueError:
            pass
    qs = qs.order_by('-data_criacao')[:500]
    lotes = [
        {
            'id_lote': l.id_lote,
            'cod_empresa': l.cod_empresa,
            'escopo_empresas': getattr(l, 'escopo_empresas', 'UMA'),
            'competencia': str(l.competencia),
            'competencia_mes': l.competencia.strftime('%Y-%m') if l.competencia else None,
            'id_arquivo_sped': l.id_arquivo_sped,
            'total_nfe_esperado': l.total_nfe_esperado,
            'total_nfe_encontrado': l.total_nfe_encontrado,
            'total_divergencias': l.total_divergencias,
            'status': l.status,
            'mensagem_erro': l.mensagem_erro,
            'usuario_criacao': l.usuario_criacao,
            'data_inicio': l.data_inicio.isoformat() if l.data_inicio else None,
            'data_fim': l.data_fim.isoformat() if l.data_fim else None,
            'data_criacao': l.data_criacao.isoformat(),
        }
        for l in qs
    ]
    return JsonResponse({'sucesso': True, 'lotes': lotes, 'total': len(lotes)})


@login_required(login_url='Login')
@require_http_methods(["GET"])
def fn_api_reprocessamento_divergencias(request, id_lote):
    """Lista divergências de um lote."""
    cod_cliente = request.session.get('cod_cliente')
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    cod_empresas = _reprocessamento_empresas_cliente(cod_cliente)
    lote = get_object_or_404(ReprocessamentoLote, id_lote=id_lote, cod_empresa__in=cod_empresas)
    divs = Divergencia.objects.filter(lote=lote).order_by('-data_criacao')[:1000]
    lista = [
        {
            'id_divergencia': d.id_divergencia,
            'tipo': d.tipo,
            'status': d.status,
            'chave_nfe': d.chave_nfe,
            'numero_nfe': d.numero_nfe,
            'serie_nfe': d.serie_nfe,
            'descricao': d.descricao,
            'valor_esperado': str(d.valor_esperado) if d.valor_esperado is not None else None,
            'valor_encontrado': str(d.valor_encontrado) if d.valor_encontrado is not None else None,
            'data_criacao': d.data_criacao.isoformat(),
        }
        for d in divs
    ]
    return JsonResponse({'sucesso': True, 'divergencias': lista, 'lote_id': lote.id_lote})


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_reprocessamento_confronto(request):
    """Dispara confronto SPED x NFe para uma ou mais empresas (ou todas) e competência (mês)."""
    cod_cliente = request.session.get('cod_cliente')
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    empresas_permitidas = _reprocessamento_empresas_cliente(cod_cliente)
    if not empresas_permitidas:
        return JsonResponse({'sucesso': False, 'mensagem': 'Nenhuma empresa vinculada ao cliente.'}, status=400)

    data = json.loads(request.body) if request.body else {}
    competencia = data.get('competencia')
    if not competencia:
        return JsonResponse({'sucesso': False, 'mensagem': 'Competência obrigatória (mês: YYYY-MM).'}, status=400)

    from datetime import datetime
    competencia = competencia.strip()
    try:
        if len(competencia) == 7 and competencia[4] == '-':
            dt = datetime.strptime(competencia + '-01', '%Y-%m-%d').date()
        else:
            dt = datetime.strptime(competencia, '%Y-%m-%d').date()
            dt = dt.replace(day=1)
    except ValueError:
        return JsonResponse({'sucesso': False, 'mensagem': 'Competência inválida. Use YYYY-MM (mês).'}, status=400)

    # Definir lista de empresas: todas ou as selecionadas (cod_empresas array)
    todas = data.get('todas_empresas', False)
    cod_empresas_list = data.get('cod_empresas') or data.get('cod_empresa')
    if isinstance(cod_empresas_list, str):
        cod_empresas_list = [cod_empresas_list] if cod_empresas_list else []
    if todas or not cod_empresas_list:
        cod_empresas_a_processar = list(empresas_permitidas)
    else:
        cod_empresas_a_processar = [c for c in cod_empresas_list if c in empresas_permitidas]
    if not cod_empresas_a_processar:
        return JsonResponse({'sucesso': False, 'mensagem': 'Selecione ao menos uma empresa válida.'}, status=400)

    # Escopo para exibição: TODAS, VARIAS ou UMA
    if todas:
        escopo = 'TODAS'
    elif len(cod_empresas_a_processar) > 1:
        escopo = 'VARIAS'
    else:
        escopo = 'UMA'
    usuario = getattr(request.user, 'username', '') or str(request.user)
    ids_lotes = []
    for cod_empresa in cod_empresas_a_processar:
        lote = ReprocessamentoLote.objects.create(
            cod_empresa=cod_empresa,
            competencia=dt,
            status='PENDENTE',
            usuario_criacao=usuario,
            escopo_empresas=escopo,
        )
        job = ReprocessamentoJob.objects.create(
            tipo='CONFRONTO',
            status='AGUARDANDO',
            id_lote=lote.id_lote,
            usuario=usuario,
        )
        lote.status = 'EM_CONFRONTO'
        lote.data_inicio = timezone.now()
        lote.save(update_fields=['status', 'data_inicio'])
        job.status = 'EM_EXECUCAO'
        job.data_inicio = timezone.now()
        job.save(update_fields=['status', 'data_inicio'])
        try:
            from app.classes.Reprocessamento import confrontar_sped_nfe
            confrontar_sped_nfe(lote.id_lote, cod_empresa, dt)
        except ImportError:
            lote.total_nfe_esperado = 0
            lote.total_nfe_encontrado = 0
            lote.total_divergencias = 0
            lote.status = 'CONCLUIDO'
            lote.data_fim = timezone.now()
            lote.save(update_fields=['total_nfe_esperado', 'total_nfe_encontrado', 'total_divergencias', 'status', 'data_fim'])
            job.status = 'CONCLUIDO'
            job.data_fim = timezone.now()
            job.total_processados = 0
            job.save(update_fields=['status', 'data_fim', 'total_processados'])
        ids_lotes.append(lote.id_lote)

    n = len(ids_lotes)
    return JsonResponse({
        'sucesso': True,
        'id_lote': ids_lotes[0] if ids_lotes else None,
        'ids_lotes': ids_lotes,
        'total_lotes': n,
        'mensagem': f'Confronto iniciado para {n} empresa(s). Consulte o painel para acompanhar.',
    })


@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_reprocessamento_reprocessar_divergencia(request, id_divergencia):
    """Marca divergência como resolvida após reprocessamento."""
    cod_cliente = request.session.get('cod_cliente')
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'}, status=403)
    cod_empresas = _reprocessamento_empresas_cliente(cod_cliente)
    div = get_object_or_404(Divergencia, id_divergencia=id_divergencia)
    if div.lote.cod_empresa not in cod_empresas:
        return JsonResponse({'sucesso': False, 'mensagem': 'Divergência não pertence ao cliente'}, status=403)
    usuario = getattr(request.user, 'username', '') or str(request.user)
    div.status = 'RESOLVIDA'
    div.data_reprocessamento = timezone.now()
    div.usuario_reprocessamento = usuario
    div.save(update_fields=['status', 'data_reprocessamento', 'usuario_reprocessamento'])
    return JsonResponse({'sucesso': True, 'mensagem': 'Divergência marcada como resolvida.'})