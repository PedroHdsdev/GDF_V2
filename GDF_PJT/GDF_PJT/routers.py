class GDFRouter:
    """Router para models do banco GDF_DEV (default)"""
    
    def db_for_read(self, model, **hints):
        # Verifica se o model está no módulo db_GDF
        if 'db_GDF' in model.__module__:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        # Verifica se o model está no módulo db_GDF
        if 'db_GDF' in model.__module__:
            return 'default'
        return None


class ReprocessamentoRouter:
    """Router para models do banco REPROCESSAMENTO_DEV"""
    
    def db_for_read(self, model, **hints):
        # Verifica se o model está no módulo db_Reprocessamento
        if 'db_Reprocessamento' in model.__module__:
            return 'reprocessamento'
        return None

    def db_for_write(self, model, **hints):
        # Verifica se o model está no módulo db_Reprocessamento
        if 'db_Reprocessamento' in model.__module__:
            return 'reprocessamento'
        return None 
