"""
Query Optimization Utils
Helpers para otimizar queries e evitar N+1 problems
"""

from django.db.models import Prefetch, Q, prefetch_related_objects
from django.core.cache import cache


class QueryOptimizer:
    """Utilitários para otimizar queries Django"""
    
    @staticmethod
    def optimize_usuarios(queryset=None):
        """Otimiza query de usuários - evita N+1"""
        from django.contrib.auth.models import User
        from app.db_GDF.Public.models import UserEmpresas
        
        if queryset is None:
            queryset = User.objects.all()
        
        return queryset.select_related(
            'empresa',
            'empresa__cliente',
            'empresa__grupo_empresa',
        ).prefetch_related(
            'groups',
            'user_permissions',
            Prefetch('userempresas_set', queryset=UserEmpresas.objects.select_related('empresa'))
        ).only(
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'date_joined'
        )
    
    @staticmethod
    def optimize_empresas(queryset=None):
        """Otimiza query de empresas"""
        from app.db_GDF.Public.models import Empresas
        
        if queryset is None:
            queryset = Empresas.objects.all()
        
        return queryset.select_related(
            'cliente',
            'grupo_empresa',
        ).only(
            'id', 'cod_empresa', 'razao_social', 'fantasia',
            'cnpj', 'cliente_id', 'grupo_empresa_id', 'is_active'
        )
    
    @staticmethod
    def optimize_clientes(queryset=None):
        """Otimiza query de clientes"""
        from app.db_GDF.Public.models import Clientes
        
        if queryset is None:
            queryset = Clientes.objects.all()
        
        return queryset.prefetch_related(
            'empresas_set',
            'solucoes_acesso_set',
        ).only(
            'id', 'cod_cliente', 'razao_social', 'cnpj', 'is_active'
        )
    
    @staticmethod
    def optimize_solucoes(queryset=None):
        """Otimiza query de soluções"""
        from app.db_GDF.Public.models import Solucoes
        
        if queryset is None:
            queryset = Solucoes.objects.all()
        
        return queryset.prefetch_related(
            'subsolucoes_set',
            'solucoesacesso_set',
        ).only(
            'id', 'cod_solucao', 'descricao'
        )
    
    @staticmethod
    def bulk_optimize_queries(items_list, relation_field, related_model):
        """
        Otimiza queries em batch
        Útil quando você tem lista de items e precisa popular relações
        
        Exemplo:
            empresas = list(Empresas.objects.all())
            QueryOptimizer.bulk_optimize_queries(
                empresas, 'cliente_id', Clientes
            )
            # Agora company.cliente está carregado sem queries adicionais
        """
        ids = [getattr(item, relation_field) for item in items_list if hasattr(item, relation_field)]
        ids = list(set(filter(None, ids)))  # Remover duplicatas e None
        
        if not ids:
            return {}
        
        related_objects = {
            obj.id: obj for obj in related_model.objects.filter(id__in=ids)
        }
        
        return related_objects


class CachedQueryManager:
    """Manager para queries com cache automático"""
    
    DEFAULT_TIMEOUT = 60 * 60  # 1 hora
    
    @staticmethod
    def get_with_cache(model, cache_key, timeout=None, **filters):
        """
        Busca objetos com cache
        
        Exemplo:
            usuarios = CachedQueryManager.get_with_cache(
                User, 'usuarios_empresa_123',
                timeout=3600,
                empresa_id=123
            )
        """
        if timeout is None:
            timeout = CachedQueryManager.DEFAULT_TIMEOUT
        
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        queryset = model.objects.filter(**filters)
        data = list(queryset)
        
        cache.set(cache_key, data, timeout)
        return data
    
    @staticmethod
    def invalidate_cache(cache_key):
        """Invalidar cache"""
        cache.delete(cache_key)
    
    @staticmethod
    def get_solucoes_for_cliente(cliente_id, cache_timeout=3600):
        """Cache de soluções por cliente"""
        from app.db_GDF.Public.models import Solucoes, SolucoesAcesso
        
        cache_key = f'solucoes_cliente_{cliente_id}'
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        solucoes = Solucoes.objects.filter(
            solucoesacesso__cliente_id=cliente_id
        ).prefetch_related(
            'subsolucoes_set',
            Prefetch('solucoesacesso_set',
                    queryset=SolucoesAcesso.objects.filter(cliente_id=cliente_id))
        ).distinct()
        
        data = list(solucoes)
        cache.set(cache_key, data, cache_timeout)
        return data
    
    @staticmethod
    def get_empresas_for_cliente(cliente_id, cache_timeout=3600):
        """Cache de empresas por cliente"""
        from app.db_GDF.Public.models import Empresas
        
        cache_key = f'empresas_cliente_{cliente_id}'
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        empresas = QueryOptimizer.optimize_empresas(
            Empresas.objects.filter(cliente_id=cliente_id)
        )
        
        data = list(empresas)
        cache.set(cache_key, data, cache_timeout)
        return data


def prefetch_everything(queryset, model_name):
    """
    Aplicar otimizações automáticas baseado no model
    
    Uso:
        usuarios = prefetch_everything(
            User.objects.all(), 'user'
        )
    """
    mappings = {
        'user': QueryOptimizer.optimize_usuarios,
        'empresa': QueryOptimizer.optimize_empresas,
        'cliente': QueryOptimizer.optimize_clientes,
        'solucao': QueryOptimizer.optimize_solucoes,
    }
    
    optimizer = mappings.get(model_name.lower())
    if optimizer:
        return optimizer(queryset)
    
    return queryset
