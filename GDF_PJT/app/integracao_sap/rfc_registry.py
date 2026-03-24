"""
Registry de RFCs SAP – arquitetura para registrar e executar RFCs que alimentam o schema sap.

Uso:
  1. Registre um handler com RfcRegistry.get_instance().register(...)
  2. Chame RfcRegistry.get_instance().execute(cod_rfc, cod_cliente, **params)
  3. Novos RFCs: crie um handler e registre em handlers.py (importado no __init__)

Para adicionar um novo RFC:
  1. Crie a função handler que recebe (cod_cliente, **params) e retorna dict com sucesso, mensagem, etc.
  2. Chame RfcRegistry.get_instance().register(RfcHandler(...)) em handlers.py
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RfcParamType(str, Enum):
    """Tipo de parâmetro para o formulário da UI."""
    STRING = "string"
    DATE = "date"
    INTEGER = "integer"
    BOOLEAN = "boolean"


@dataclass
class RfcParam:
    """Definição de um parâmetro de RFC para a UI."""
    key: str
    label: str
    param_type: RfcParamType = RfcParamType.STRING
    required: bool = True
    default: Any = None
    help_text: str = ""


@dataclass
class RfcHandler:
    """
    Handler de uma RFC: nome, descrição, parâmetros e função de execução.
    """
    codigo: str
    nome: str
    descricao: str
    tabela_sap: str  # ex: "sap.relatorio_custo"
    params: List[RfcParam] = field(default_factory=list)
    handler_fn: Callable[..., Dict[str, Any]] = None

    def execute(self, cod_cliente: str, **params) -> Dict[str, Any]:
        """Executa o handler com os parâmetros fornecidos."""
        if not self.handler_fn:
            return {
                "sucesso": False,
                "mensagem": f"Handler não configurado para RFC '{self.codigo}'.",
            }
        try:
            return self.handler_fn(cod_cliente=cod_cliente, **params)
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": str(e),
            }


class RfcRegistry:
    """Registry central de RFCs – singleton."""

    _instance: Optional["RfcRegistry"] = None

    def __init__(self):
        self._handlers: Dict[str, RfcHandler] = {}

    @classmethod
    def get_instance(cls) -> "RfcRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._register_builtin_handlers()
        return cls._instance

    def register(self, handler: RfcHandler):
        """Registra um handler de RFC."""
        self._handlers[handler.codigo] = handler

    def get(self, codigo: str) -> Optional[RfcHandler]:
        """Retorna o handler pelo código."""
        return self._handlers.get(codigo)

    def list_all(self) -> List[RfcHandler]:
        """Lista todos os handlers registrados."""
        return list(self._handlers.values())

    def execute(self, codigo: str, cod_cliente: str, **params) -> Dict[str, Any]:
        """Executa o RFC pelo código."""
        handler = self.get(codigo)
        if not handler:
            return {
                "sucesso": False,
                "mensagem": f"RFC '{codigo}' não encontrado.",
            }
        return handler.execute(cod_cliente=cod_cliente, **params)

    def _register_builtin_handlers(self):
        """Registra os handlers padrão (importados de handlers.py)."""
        from app.integracao_sap import handlers

        handlers.register_all(self)
