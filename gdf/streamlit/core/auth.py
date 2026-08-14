"""Autenticação JWT e validação de usuário."""
import streamlit as st

try:
    from jwt import decode as jwt_decode
except ImportError:
    try:
        import jwt as jwt_module
        jwt_decode = getattr(jwt_module, "decode", None)
    except (ImportError, AttributeError):
        jwt_decode = None


class AuthResult:
    """Resultado da autenticação."""
    __slots__ = ("username", "user_id", "tipo_relatorio", "cod_cliente", "acesso_total", "payload")

    def __init__(self, username, user_id, tipo_relatorio="Vendas", cod_cliente="", acesso_total=False, payload=None):
        self.username = username
        self.user_id = user_id
        self.tipo_relatorio = tipo_relatorio
        self.cod_cliente = cod_cliente.strip()
        self.acesso_total = acesso_total
        self.payload = payload or {}

    def to_session_state(self):
        """Salva dados na session_state do Streamlit."""
        st.session_state["username"] = self.username
        st.session_state["user_id"] = self.user_id
        st.session_state["tipo_relatorio"] = self.tipo_relatorio
        st.session_state["cod_cliente"] = self.cod_cliente
        st.session_state["acesso_total"] = self.acesso_total


def authenticate(token: str, secret_key: str) -> AuthResult | None:
    """
    Valida o token JWT e retorna AuthResult ou None em caso de falha.
    """
    if jwt_decode is None:
        st.error("❌ JWT não disponível no servidor")
        return None

    if not token:
        st.error("Acesso negado")
        return None

    try:
        payload = jwt_decode(token, secret_key, algorithms=["HS256"])
        result = AuthResult(
            username=payload["username"],
            user_id=payload["user_id"],
            tipo_relatorio=payload.get("tipo_relatorio", "Vendas"),
            cod_cliente=payload.get("cod_cliente", ""),
            acesso_total=payload.get("is_superuser", False) or payload.get("usuario_cliente_1000", False),
            payload=payload
        )
        result.to_session_state()
        return result
    except Exception as err:
        st.error(f"❌ Erro de autenticação: {str(err)}")
        return None
