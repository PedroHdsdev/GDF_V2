def solucoes_context(request):
    from django.conf import settings
    url_prefix = (request.META.get("SCRIPT_NAME") or getattr(settings, "FORCE_SCRIPT_NAME", "") or "").strip()
    if url_prefix and not url_prefix.startswith("/"):
        url_prefix = "/" + url_prefix
    url_prefix = url_prefix.rstrip("/")  # '' ou '/gdf'
    ctx = {
        't_solucoes': request.session.get('t_solucoes', []),
        'cod_cliente': request.session.get('cod_cliente'),
        'url_prefix': url_prefix,
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