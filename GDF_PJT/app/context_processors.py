def solucoes_context(request):
    ctx = {
        't_solucoes': request.session.get('t_solucoes', []),
        'cod_cliente': request.session.get('cod_cliente'),
    }
    # Superuser ou usuário cliente 1000 (empresa dona do projeto): pode trocar cliente em qualquer tela
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