"""
Módulo de integração SAP via RFC.

Permite registrar e executar RFCs que alimentam as tabelas do schema sap.
Arquitetura extensível: novos RFCs podem ser adicionados registrando handlers.
"""
from app.integracao_sap.rfc_registry import (
    RfcRegistry,
    RfcHandler,
    RfcParam,
    RfcParamType,
)
from app.integracao_sap.consulta_fiscal_material import (
    SapFiscalMaterialError,
    SapFiscalMaterialHttpError,
    SapFiscalMaterialInvalidResponseError,
    SapFiscalMaterialNotConfiguredError,
    SapFiscalMaterialResult,
    SapFiscalMaterialTimeoutError,
    consultar_fiscal_material,
)


def get_rfc_registry():
    """Retorna o registry central de RFCs."""
    return RfcRegistry.get_instance()


__all__ = [
    'RfcRegistry',
    'RfcHandler',
    'RfcParam',
    'RfcParamType',
    'get_rfc_registry',
    'SapFiscalMaterialError',
    'SapFiscalMaterialHttpError',
    'SapFiscalMaterialInvalidResponseError',
    'SapFiscalMaterialNotConfiguredError',
    'SapFiscalMaterialResult',
    'SapFiscalMaterialTimeoutError',
    'consultar_fiscal_material',
]
