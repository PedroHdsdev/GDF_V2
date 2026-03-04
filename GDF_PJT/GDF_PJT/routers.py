"""
Router de banco de dados para suportar múltiplos schemas no PostgreSQL

Estrutura:
- Models em 'db_GDF' → banco 'default' (schemas: public, nfe, sped)
- Models em 'db_Reprocessamento' → banco 'default', schema 'reprocessamento'
"""

class GDFRouter:
    """Router para models do banco GDF (default)."""

    def db_for_read(self, model, **hints):
        if 'db_GDF' in model.__module__:
            return 'default'
        if 'db_Reprocessamento' in model.__module__:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if 'db_GDF' in model.__module__:
            return 'default'
        if 'db_Reprocessamento' in model.__module__:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        m1 = obj1.__class__.__module__
        m2 = obj2.__class__.__module__
        if ('db_GDF' in m1 or 'db_Reprocessamento' in m1) and ('db_GDF' in m2 or 'db_Reprocessamento' in m2):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'default' and app_label == 'app':
            return True
        if db != 'default':
            return False
        return None

