def solucoes_context(request):
    return {
        't_solucoes': request.session.get('t_solucoes', [])
    }