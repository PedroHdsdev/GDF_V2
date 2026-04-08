"""Dashboard Balanço financeiro — integração com SAP (ZF_ECF01) via backend Django."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from core.auth import AuthResult
from core.django_backend import balanco_financeiro_api_url, post_json_bearer

# Alinhado a SapRfc._ZF_ECF01_MAX_NUMERO_PERIODO (I_MONTH_B / I_MONTH_V na RFC).
_MAX_PERIODO_SAP = 99


class DashboardBalancoFin:
    """Painel de balanço financeiro com filtros e tabela de resultados."""

    TIPO_RELATORIO = "BalancoFin"

    def __init__(self, auth: AuthResult):
        self.auth = auth

    def _load_empresas(self):
        from django.contrib.auth.models import User
        from app.db_GDF.Public.models import Empresa

        try:
            user = User.objects.get(username=self.auth.username)
        except User.DoesNotExist:
            st.error("Usuário inválido.")
            return None

        if self.auth.acesso_total and self.auth.cod_cliente:
            qs = Empresa.objects.filter(
                gdfcliente__cod_cliente=self.auth.cod_cliente
            ).distinct()
        else:
            qs = Empresa.objects.filter(usuarioempresa__user=user).distinct()
            if self.auth.cod_cliente:
                qs = qs.filter(gdfcliente__cod_cliente=self.auth.cod_cliente)

        if not qs.exists():
            st.error("Nenhuma empresa vinculada ao usuário.")
            return None
        return list(qs.order_by("cod_empresa"))

    def run(self) -> bool:
        if not self.auth.cod_cliente:
            st.error("Cliente não identificado no token. Selecione um cliente no GDF e abra o dashboard novamente.")
            return False

        empresas = self._load_empresas()
        if not empresas:
            return False

        st.sidebar.markdown("### Sessão")
        st.sidebar.markdown(f"**{self.auth.username}**")
        if self.auth.cod_cliente:
            st.sidebar.markdown(f"**{self.auth.cod_cliente}**")

        st.markdown("## Balanço financeiro")

        st.markdown("**Filtros**")
        labels = [
            f"{e.cod_empresa} — {(e.fantasia or e.razao or '')[:40]}"
            for e in empresas
        ]
        idx = st.selectbox(
            "Empresa",
            range(len(empresas)),
            format_func=lambda i: labels[i],
            key="balanco_fin_empresa",
        )
        i_bukrs = empresas[idx].cod_empresa

        agora = datetime.now()
        st.caption(
            "Período SAP enviado à RFC como I_MONTH_B (inicial) e I_MONTH_V (final), com I_YEAR — "
            "ex.: 1 a 12 ou 1 a 16. Uma única chamada à RFC."
        )
        col_pi, col_pf, col_y = st.columns(3)
        with col_pi:
            i_month_b = st.number_input(
                "I_MONTH_B (inicial)",
                min_value=1,
                max_value=_MAX_PERIODO_SAP,
                value=1,
                step=1,
                help="Período inicial (RFC I_MONTH_B).",
                key="balanco_fin_i_month_b",
            )
        with col_pf:
            i_month_v = st.number_input(
                "I_MONTH_V (final)",
                min_value=1,
                max_value=_MAX_PERIODO_SAP,
                value=12,
                step=1,
                help="Período final (RFC I_MONTH_V). Igual ao inicial = um período só.",
                key="balanco_fin_i_month_v",
            )
        with col_y:
            i_year = st.number_input(
                "Ano (exercício)",
                min_value=1900,
                max_value=9999,
                value=int(agora.year),
                step=1,
                key="balanco_fin_i_year",
            )

        i_month_b_rfc = int(i_month_b)
        i_month_v_rfc = int(i_month_v)
        i_year_rfc = int(i_year)

        col_pc, col_ver = st.columns(2)
        with col_pc:
            i_ktopl = st.text_input(
                "Plano de contas",
                max_chars=4,
                placeholder="ex.: INT",
                key="balanco_fin_ktopl",
            )
        with col_ver:
            i_versn = st.text_input(
                "Versão",
                max_chars=4,
                placeholder="ex.: 0001",
                key="balanco_fin_versn",
            )

        consultar = st.button("Consultar", type="primary", key="balanco_fin_consultar")

        st.divider()

        if not consultar:
            st.info("Selecione os filtros acima e clique em **Consultar** para carregar os dados.")
            return True

        jwt_token = (st.query_params.get("token") or "").strip()
        if not jwt_token:
            st.error("Token do dashboard ausente. Abra o balanço pelo menu do GDF.")
            return True

        api_url = balanco_financeiro_api_url()
        payload = {
            "i_bukrs": str(i_bukrs).strip(),
            "i_year": i_year_rfc,
            "i_month_b": i_month_b_rfc,
            "i_month_v": i_month_v_rfc,
            "i_ktopl": (i_ktopl or "").strip(),
            "i_versn": (i_versn or "").strip(),
        }

        with st.spinner("Carregando dados…"):
            out = post_json_bearer(api_url, jwt_token, payload)

        r_ret = (out.get("r_return") or "").strip()
        if r_ret and out.get("sucesso"):
            st.caption(r_ret)

        if not out.get("sucesso"):
            st.error(out.get("mensagem") or "Não foi possível carregar os dados.")
            return True

        st.success(out.get("mensagem") or "Dados atualizados.")
        rows = out.get("t_balance") or []
        if not rows:
            st.warning("Nenhum registro encontrado para os filtros selecionados.")
            return True

        df = pd.DataFrame(rows)
        st.metric("Registros", len(df))
        st.dataframe(df, use_container_width=True, height=min(520, 120 + 28 * min(len(df), 15)))

        st.caption(f"Atualizado em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")
        return True
