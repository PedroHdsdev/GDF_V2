"""
Módulo de classes de negócio (POO) do app GDF.

Exporta:
- ClGdf: serviço de sessão/cliente/empresas/soluções/certificados
- CargaXml, EmpresaNaoCadastradaError: carga de XMLs (NFe, CTe, NFSe)
- CargaSped: carga de arquivos SPED (EFD Fiscal/Contribuições)
- SapRfc: integração SAP (RFC)
- Reprocessamento: confrontar_sped_nfe, gerar_condicoes_pagamento_lote,
  condicao_pagamento_da_nfe, tipo_pagamento_da_nfe
- enviar_condicoes_pagamento_sap (SapRfc)
"""
from .gdf import ClGdf
from .CargaXml import CargaXml, EmpresaNaoCadastradaError
from .CargaSped import CargaSped
from .SapRfc import SapRfc, enviar_condicoes_pagamento_sap
from .Reprocessamento import (
    confrontar_sped_nfe,
    gerar_condicoes_pagamento_lote,
    condicao_pagamento_da_nfe,
    tipo_pagamento_da_nfe,
)

__all__ = [
    'ClGdf',
    'CargaXml',
    'CargaSped',
    'SapRfc',
    'EmpresaNaoCadastradaError',
    'enviar_condicoes_pagamento_sap',
    'confrontar_sped_nfe',
    'gerar_condicoes_pagamento_lote',
    'condicao_pagamento_da_nfe',
    'tipo_pagamento_da_nfe',
]
