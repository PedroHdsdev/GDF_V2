"""
Router de banco de dados para suportar múltiplos schemas no PostgreSQL

Estrutura:
- Models em 'db_GDF' → banco 'default' (schemas: public, nfe)
- Models em 'db_Reprocessamento' → banco 'reprocessamento'
"""

class GDFRouter:
    """Router para models do banco GDF_DEV (default)"""
    
    def db_for_read(self, model, **hints):
        if 'db_GDF' in model.__module__:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if 'db_GDF' in model.__module__:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_db_gdf = 'db_GDF' in obj1.__class__.__module__
        obj2_db_gdf = 'db_GDF' in obj2.__class__.__module__
        if obj1_db_gdf and obj2_db_gdf:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'default' and app_label == 'app':
            return True
        elif db != 'default':
            return False
        return None


class ReprocessamentoRouter:
    """Router para models do banco REPROCESSAMENTO_DEV"""
    
    def db_for_read(self, model, **hints):
        if 'db_Reprocessamento' in model.__module__:
            return 'reprocessamento'
        return None

    def db_for_write(self, model, **hints):
        if 'db_Reprocessamento' in model.__module__:
            return 'reprocessamento'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_reprocessamento = 'db_Reprocessamento' in obj1.__class__.__module__
        obj2_reprocessamento = 'db_Reprocessamento' in obj2.__class__.__module__
        if obj1_reprocessamento and obj2_reprocessamento:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'reprocessamento' and app_label == 'app':
            return True
        elif db != 'reprocessamento':
            return False
        return None

