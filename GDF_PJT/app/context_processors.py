import unicodedata


def _norm_desc_solucao(text):
    if not text:
        return ""
    s = "".join(
        c
        for c in unicodedata.normalize("NFD", str(text).strip())
        if unicodedata.category(c) != "Mn"
    )
    return s.lower()


def _is_solucao_menu_engrenagem(sol):
    """Solução cujas subsoluções vão para a engrenagem: Configuração (e legado Administração/typo)."""
    d = _norm_desc_solucao((sol or {}).get("descricao", ""))
    return d in ("administracao", "adiministracao", "configuracao")


COD_SUB_FILIAIS = "Dm_Filiais"  # Gerido só no modal de Empresas, não entra no menu/engrenagem
COD_SUB_DM_CLIENTES = "Dm_Clientes"  # Rótulo no menu: "Mandante" (em vez de Cliente(s) GDF na sessão antiga)
_DESC_MANDANTE = "Mandante"


def _rotular_dm_clientes_mandante(t_subs_admin, t_solucoes):
    """Força a descrição de Dm_Clientes no menu; a sessão ainda pode ter o nome antigo até novo login."""
    for sub in t_subs_admin or []:
        if str((sub or {}).get("cod_subsolucao", "")) == COD_SUB_DM_CLIENTES and isinstance(sub, dict):
            sub["descricao"] = _DESC_MANDANTE
    for sol in t_solucoes or []:
        for s in (sol or {}).get("sub_solucoes") or []:
            if str((s or {}).get("cod_subsolucao", "")) == COD_SUB_DM_CLIENTES and isinstance(s, dict):
                s["descricao"] = _DESC_MANDANTE


def _sem_sub_filiais(sol):
    """Remove a subsolução filiais (cadastro fica em Empresas)."""
    subs = sol.get("sub_solucoes") or []
    subs = [s for s in subs if str(s.get("cod_subsolucao", "")) != COD_SUB_FILIAIS]
    out = dict(sol)
    out["sub_solucoes"] = subs
    return out


def _separar_solucao_menu_admin(solucoes):
    """Remove a solução Configuração (ex-Administração) do menu lateral; devolve subsoluções (engrenagem)."""
    t_subs_admin = []
    restante = []
    for sol in solucoes or []:
        if _is_solucao_menu_engrenagem(sol):
            t_subs_admin = [s for s in (sol.get("sub_solucoes") or []) if str(s.get("cod_subsolucao", "")) != COD_SUB_FILIAIS]
        else:
            restante.append(_sem_sub_filiais(sol))
    return t_subs_admin, restante


def solucoes_context(request):
    from django.conf import settings
    url_prefix = (request.META.get("SCRIPT_NAME") or getattr(settings, "FORCE_SCRIPT_NAME", "") or "").strip()
    if url_prefix and not url_prefix.startswith("/"):
        url_prefix = "/" + url_prefix
    url_prefix = url_prefix.rstrip("/")  # '' ou '/gdf'
    raw = request.session.get("t_solucoes", [])
    t_subs_admin, t_solucoes = _separar_solucao_menu_admin(raw)
    _rotular_dm_clientes_mandante(t_subs_admin, t_solucoes)
    ctx = {
        "t_solucoes": t_solucoes,
        "t_subsolucoes_admin": t_subs_admin,
        "cod_cliente": request.session.get("cod_cliente"),
        "url_prefix": url_prefix,
    }
    # Superuser ou usuário cliente PRCIT (empresa dona do projeto): pode trocar cliente em qualquer tela
    if request.user.is_authenticated:
        pode = request.session.get('is_superuser', False) or request.session.get('usuario_cliente_1000', False)
        if pode:
            ctx['pode_trocar_cliente'] = True
            ctx['is_superuser'] = request.session.get('is_superuser', False)
            try:
                from app.classes.gdf import ClGdf
                ctx['lista_clientes'] = ClGdf().get_clientes()
            except Exception:
                ctx['lista_clientes'] = []
    return ctx