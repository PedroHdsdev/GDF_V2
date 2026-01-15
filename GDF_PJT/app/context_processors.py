def solucoes_context(request):
    return {
        't_solucoes': request.session.get('t_solucoes', []),
        'cod_cliente': request.session.get('cod_cliente')
    }