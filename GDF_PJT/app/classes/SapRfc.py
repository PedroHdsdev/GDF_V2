"""
Comunicação RFC com SAP usando a tabela SapConnection.

Padrão de uso para cada função SAP via RFC:
  1. Crie um método com o nome da funcionalidade (ex: importar_custo_cliente).
  2. Esse método chama o responsável pela conexão (SapRfc.call ou SapRfc.with_connection).
  3. Chame a função RFC passando os parâmetros.
  4. A comunicação é fechada ao final (SapRfc.call já abre, chama e fecha).

Exemplo: ver importar_custo_cliente, importar_relatorio_custo, consultar_balanco_financeiro (ZF_ECF01).
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

PYRFC_IMPORT_ERROR: str = ""

try:
    from pyrfc import Connection as PyRfcConnection

    PYRFC_AVAILABLE = True
except Exception as _pyrfc_exc:
    PyRfcConnection = None
    PYRFC_AVAILABLE = False
    PYRFC_IMPORT_ERROR = str(_pyrfc_exc).strip() or repr(_pyrfc_exc)

_RFC_BALANCO_FINANCEIRO = "ZF_ECF01"

# T_BALANCE (ZF_ECF01): estrutura ABAP documentada — ordem fixa para API/UI.
_T_BALANCE_CAMPOS_CABECALHO: Tuple[str, ...] = (
    "TP_IMP",
    "SAKNR",
    "DESC",
    "TIPO",
    "IND_DC",
)
_T_BALANCE_CAMPOS_SALDO_MES: Tuple[str, ...] = tuple(f"UM{i:02d}O" for i in range(1, 13))
_T_BALANCE_CAMPOS_FIM: Tuple[str, ...] = ("SORT",)
T_BALANCE_COLUNAS_PROCESSADAS: Tuple[str, ...] = (
    *_T_BALANCE_CAMPOS_CABECALHO,
    *_T_BALANCE_CAMPOS_SALDO_MES,
    *_T_BALANCE_CAMPOS_FIM,
)
# Colunas adicionais: ano e intervalo I_MONTH_B / I_MONTH_V enviados à RFC + soma do exercício
T_BALANCE_COLUNAS_RESPOSTA: Tuple[str, ...] = (
    "ano_referencia",
    "mes_referencia_b",
    "mes_referencia_v",
    *T_BALANCE_COLUNAS_PROCESSADAS,
    "total_saldo_exercicio",
    "saldos_mensais",
)

# Limite dos números em I_MONTH_B / I_MONTH_V e largura máxima do intervalo (inclusive).
_ZF_ECF01_MAX_NUMERO_PERIODO: int = 99
_ZF_ECF01_MAX_INTERVALO_PERIODOS: int = 120


def _zf_ecf01_valor_json(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, (bool, int, float, str)):
        return v
    return str(v)


def _zf_ecf01_buscar_chave_dict(d: Dict[str, Any], *nomes: str) -> Any:
    for nome in nomes:
        if nome in d:
            return d[nome]
    lower_map = {str(k).upper(): k for k in d}
    for nome in nomes:
        k = lower_map.get(nome.upper())
        if k is not None:
            return d[k]
    return None


def _zf_ecf01_extrair_t_balance_e_return(result: Optional[Dict[str, Any]]) -> tuple:
    if not result or not isinstance(result, dict):
        return [], ""
    raw_tb = _zf_ecf01_buscar_chave_dict(result, "T_BALANCE", "ET_BALANCE")
    if raw_tb is None:
        linhas = []
    elif isinstance(raw_tb, list):
        linhas = raw_tb
    else:
        linhas = list(raw_tb)
    r_ret = _zf_ecf01_buscar_chave_dict(result, "R_RETURN", "E_RETURN", "EV_RETURN")
    if r_ret is None:
        msg = ""
    else:
        msg = str(r_ret).strip()
    return linhas, msg


def _zf_ecf01_campo_str(linha: Dict[str, Any], nome_abap: str) -> str:
    v = _zf_ecf01_buscar_chave_dict(linha, nome_abap)
    if v is None:
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace").strip()
    return str(v).strip()


def _zf_ecf01_para_decimal_saldo(v: Any) -> Optional[Decimal]:
    """Interpreta CURR/quantidade vinda do PyRFC como Decimal."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    s = str(v).strip().replace(" ", "")
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _zf_ecf01_multiplicador_ind_dc(ind_dc: Any) -> Decimal:
    """
    Fator aplicado aos saldos UM01O–UM12O conforme indicador débito/crédito (ZECFED_INDICADOR_D_C).

    Convenção: valores no SAP seguem o lado da conta; para exibição analítica unificada,
    crédito (Haben) inverte o sinal. Ajuste o mapeamento se o domínio no SAP for outro.

    S, D, 1 → +1 (Soll / débito)
    H, C, 2 → -1 (Haben / crédito)
    """
    s = (str(ind_dc).strip()[:1] if ind_dc is not None else "") or ""
    if not s:
        return Decimal("1")
    u = s.upper()
    if u in ("H", "C", "2"):
        return Decimal("-1")
    if u in ("S", "D", "1"):
        return Decimal("1")
    return Decimal("1")


def _zf_ecf01_processar_linha_t_balance(linha: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapeia uma linha bruta de T_BALANCE para o layout documentado, com saldos mensais
    já multiplicados por IND_DC (sinal analítico).
    """
    if not linha:
        return {}

    ind_dc_raw = _zf_ecf01_buscar_chave_dict(linha, "IND_DC")
    mult = _zf_ecf01_multiplicador_ind_dc(ind_dc_raw)

    out: Dict[str, Any] = {}
    for nome in _T_BALANCE_CAMPOS_CABECALHO:
        out[nome] = _zf_ecf01_campo_str(linha, nome)

    total_parcial = Decimal("0")
    for key in _T_BALANCE_CAMPOS_SALDO_MES:
        bruto = _zf_ecf01_para_decimal_saldo(_zf_ecf01_buscar_chave_dict(linha, key))
        if bruto is None:
            out[key] = None
        else:
            assinado = (bruto * mult).quantize(Decimal("0.01"))
            out[key] = str(assinado)
            total_parcial += assinado

    out["SORT"] = _zf_ecf01_campo_str(linha, "SORT")
    out["total_saldo_exercicio"] = str(total_parcial.quantize(Decimal("0.01")))

    # Lista Jan–Dez (mesmo sinal que as colunas UMxxO) — útil para gráficos sem reparsing
    out["saldos_mensais"] = [out[k] for k in _T_BALANCE_CAMPOS_SALDO_MES]

    return out


def _zf_ecf01_montar_parametros(
    i_bukrs: str, i_month_b: int, i_month_v: int, i_year: int, i_ktopl: str, i_versn: str
) -> Dict[str, str]:
    """Parâmetros de importação ZF_ECF01: I_MONTH_B (inicial), I_MONTH_V (final), 2 dígitos."""
    return {
        "I_BUKRS": str(i_bukrs).strip(),
        "I_MONTH_B": f"{int(i_month_b):02d}",
        "I_MONTH_V": f"{int(i_month_v):02d}",
        "I_YEAR": str(int(i_year)),
        "I_KTOPL": str(i_ktopl).strip(),
        "I_VERSN": str(i_versn).strip(),
    }


def _zf_ecf01_resolver_intervalo_meses(
    params: Dict[str, Any],
) -> Tuple[Optional[Tuple[int, int, int]], Optional[str]]:
    """
    Resolve (ano, mês/período inicial, mês/período final) para uma única chamada RFC.

    Aceita i_month_b / i_month_v (ou I_MONTH_B / I_MONTH_V), ou i_month_ini / i_month_fim
    como alias; período único: i_month + i_year (define B = V = i_month).
    Números podem ultrapassar 12 (ex.: 1–16).
    """
    mb = params.get("i_month_b")
    if mb is None:
        mb = params.get("I_MONTH_B")
    mv = params.get("i_month_v")
    if mv is None:
        mv = params.get("I_MONTH_V")

    if mb is None and mv is None:
        mi = params.get("i_month_ini")
        if mi is None:
            mi = params.get("I_MONTH_INI")
        mf = params.get("i_month_fim")
        if mf is None:
            mf = params.get("I_MONTH_FIM")
        mb, mv = mi, mf

    if (mb is not None) ^ (mv is not None):
        return None, (
            "Informe ambos i_month_b e i_month_v (período inicial e final na RFC), "
            "ou i_month_ini e i_month_fim, ou i_month com i_year."
        )

    if mb is not None and mv is not None:
        y_raw = params.get("i_year")
        if y_raw is None:
            y_raw = params.get("I_YEAR")
        if y_raw is None:
            return None, "Informe i_year junto com o intervalo de períodos."
        try:
            y = int(y_raw)
            a, b = int(mb), int(mv)
        except (TypeError, ValueError):
            return None, "Ano ou número de período inválido."
        if y < 1900 or y > 9999:
            return None, "Ano fora do intervalo permitido."
        if a < 1 or a > _ZF_ECF01_MAX_NUMERO_PERIODO or b < 1 or b > _ZF_ECF01_MAX_NUMERO_PERIODO:
            return None, (
                f"Período deve estar entre 1 e {_ZF_ECF01_MAX_NUMERO_PERIODO} "
                "(valores enviados a I_MONTH_B e I_MONTH_V)."
            )
        if a > b:
            a, b = b, a
        qtd = b - a + 1
        if qtd > _ZF_ECF01_MAX_INTERVALO_PERIODOS:
            return None, (
                f"Intervalo excede {_ZF_ECF01_MAX_INTERVALO_PERIODOS} períodos. "
                "Reduza a diferença entre inicial e final."
            )
        return (y, a, b), None

    ms = params.get("i_month")
    if ms is None:
        ms = params.get("I_MONTH")
    if ms is not None:
        y_raw = params.get("i_year")
        if y_raw is None:
            y_raw = params.get("I_YEAR")
        if y_raw is None:
            return None, "Informe i_year junto com i_month."
        try:
            y = int(y_raw)
            m = int(ms)
        except (TypeError, ValueError):
            return None, "Período ou ano inválido."
        if m < 1 or m > _ZF_ECF01_MAX_NUMERO_PERIODO:
            return None, (
                f"i_month (período) deve estar entre 1 e {_ZF_ECF01_MAX_NUMERO_PERIODO}."
            )
        if y < 1900 or y > 9999:
            return None, "Ano fora do intervalo permitido."
        return (y, m, m), None

    return None, (
        "Informe i_month_b e i_month_v (ou i_month_ini e i_month_fim) e i_year, ou i_month e i_year."
    )


def _get_sap_connection_model():
    from app.db_GDF.Public.models import ConexaoSap
    return ConexaoSap


class SapRfc:
    """
    Classe responsável pela comunicação com SAP via RFC usando registros da tabela SapConnection.
    A conexão é sempre vinculada ao cliente: use cod_cliente para buscar o registro em SapConnection.

    Padrão para novas funcionalidades RFC:
      - Criar um método com nome da funcionalidade.
      - Chamar SapRfc.call(cod_cliente, nome_rfc, **params) [abre conexão, chama RFC, fecha].
      - Ou SapRfc.with_connection(cod_cliente, lambda sap: sap.call(...)) para várias chamadas.
    """
    _last_connect_error = ""

    # -------------------------------------------------------------------------
    # Conexão e chamada genérica (use estes dentro dos métodos de funcionalidade)
    # -------------------------------------------------------------------------

    @staticmethod
    def is_available():
        """Retorna True se o PyRFC está instalado."""
        return PYRFC_AVAILABLE

    @staticmethod
    def pyrfc_mensagem_indisponivel() -> str:
        """
        Mensagem para API/UI quando o PyRFC não carrega (pacote ausente, SDK ou LD_LIBRARY_PATH).
        """
        det_full = (PYRFC_IMPORT_ERROR or "").strip()
        det = det_full[:240] + ("..." if len(det_full) > 240 else "") if det_full else ""

        # Pacote Python não instalado no mesmo interpretador do Gunicorn/Streamlit/Celery
        if "no module named" in det_full.lower() and "pyrfc" in det_full.lower():
            return (
                "Integração SAP inativa: o pacote Python **pyrfc** não está instalado neste ambiente. "
                "Ative o mesmo venv do servidor (ex.: GDF_PJT/venv) e execute: `pip install pyrfc`. "
                "Em seguida instale o SAP NetWeaver RFC SDK em `<raiz-do-repositório>/nwrfcsdk`, "
                "configure SAPNWRFC_HOME e LD_LIBRARY_PATH (nwrfcsdk/lib) e reinicie os processos."
                + (f" (detalhe: {det})" if det else "")
            )

        # SDK / biblioteca nativa ausente ou loader não encontra libsapnwrfc.so
        if any(
            x in det_full.lower()
            for x in (
                "libsapnwrfc",
                "cannot open shared object",
                "connection",
                "importerror",
                "_cyrfc",
            )
        ):
            msg = (
                "Integração SAP inativa: o PyRFC não carregou a biblioteca nativa do SAP. "
                "Instale o SAP NetWeaver RFC SDK, coloque em `<raiz-do-repositório>/nwrfcsdk` "
                "(com `lib/libsapnwrfc.so`), defina SAPNWRFC_HOME e inclua `nwrfcsdk/lib` em "
                "LD_LIBRARY_PATH antes de subir Django ou Streamlit, e reinicie."
            )
            return f"{msg} (detalhe: {det})" if det else msg

        msg = (
            "Integração SAP inativa: falha ao importar o PyRFC. "
            "1) No venv do projeto: `pip install pyrfc`. "
            "2) Instale o SAP NW RFC SDK em `nwrfcsdk`, com SAPNWRFC_HOME e LD_LIBRARY_PATH. "
            "3) Reinicie Django/Streamlit."
        )
        return f"{msg} (detalhe: {det})" if det else msg

    @staticmethod
    def get_connection(cod_cliente):
        """
        Retorna a primeira conexão SAP ativa para o cliente, ou None.
        Parâmetro obrigatório: cod_cliente (código do cliente para filtrar na tabela SapConnection).
        """
        if not cod_cliente:
            print("[SapRfc] get_connection: cod_cliente vazio, retornando None")
            return None
        SapConnection = _get_sap_connection_model()
        conn = SapConnection.objects.filter(gdfcliente_id=cod_cliente, active=True).first()
        if conn:
            print(f"[SapRfc] get_connection: conexão encontrada para cliente '{cod_cliente}' (id={conn.id}, ashost={getattr(conn, 'ashost', '?')})")
        else:
            print(f"[SapRfc] get_connection: nenhuma conexão SAP ativa para cliente '{cod_cliente}'")
        return conn

    @staticmethod
    def get_active_connections(cod_cliente=None, queryset=None):
        """
        Retorna lista de conexões SAP ativas.
        - cod_cliente: se informado, filtra apenas conexões desse cliente (tabela SapConnection).
        - queryset: se informado, usa esse queryset (ignora cod_cliente).
        """
        SapConnection = _get_sap_connection_model()
        if queryset is not None:
            return list(queryset)
        qs = SapConnection.objects.filter(active=True)
        if cod_cliente:
            qs = qs.filter(gdfcliente_id=cod_cliente)
        return list(qs)

    @staticmethod
    def config_from_connection(conn):
        """
        Monta o dicionário de configuração para o pyrfc a partir de um registro SapConnection.
        """
        return {
            "ashost": conn.ashost or "",
            "sysnr": conn.sysnr or "",
            "client": conn.client or "",
            "user": conn.username or "",
            "passwd": conn.passwd or "",
            "lang": conn.lang or "",
            "decimal_output_as_string": "True",
        }

    @staticmethod
    def connect(conn):
        """
        Cria e retorna uma conexão pyrfc (Connection) para o registro SapConnection dado.
        Retorna None se PyRFC não estiver disponível ou se a conexão falhar.
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] connect: PyRFC não disponível")
            return None
        config = SapRfc.config_from_connection(conn)
        print(f"[SapRfc] connect: abrindo conexão SAP (conn id={getattr(conn, 'id', '?')}, ashost={config.get('ashost', '')})")
        try:
            sap = PyRfcConnection(**config)
            print(f"[SapRfc] connect: conexão SAP aberta com sucesso (conn id={getattr(conn, 'id', '?')})")
            return sap
        except Exception as e:
            err_msg = str(e)
            SapRfc._last_connect_error = err_msg
            print(f"[SapRfc] connect: ERRO ao conectar SAP (conn id={getattr(conn, 'id', conn)}): {e}")
            return None

    @staticmethod
    def _mensagem_erro_com_vpn(erro: str) -> str:
        """
        Enriquece mensagem de erro com dica de VPN quando parecer falha de conectividade.
        A conexão RFC é feita pelo SERVIDOR (Django), não pelo navegador.
        """
        if not erro:
            return erro
        erro_lower = str(erro).lower()
        indicadores_rede = (
            'connection refused', 'connection timed out', 'timeout', 'host unreachable',
            'no route to host', 'network is unreachable', 'connection reset',
            'errno 111', 'errno 110', 'errno 113', 'errno 101',
        )
        if any(ind in erro_lower for ind in indicadores_rede):
            return (
                f"{erro} "
                "Se o SAP exige VPN, o servidor onde o Django roda deve estar conectado à VPN corporativa."
            )
        return erro

    @staticmethod
    def _resolve_conn(cod_cliente_or_conn):
        """Retorna SapConnection a partir de cod_cliente (str) ou do próprio registro (conn)."""
        if cod_cliente_or_conn is None:
            return None
        if isinstance(cod_cliente_or_conn, str):
            return SapRfc.get_connection(cod_cliente_or_conn)
        return cod_cliente_or_conn

    @staticmethod
    def call(cod_cliente_or_conn, rfc_name, **params):
        """
        Método responsável pela conexão: abre, chama o RFC e fecha.
        Use este método dentro de cada método de funcionalidade (um por RFC).

        Fluxo: 1) obtém conexão (por cod_cliente na SapConnection)
               2) chama a função RFC com **params
               3) fecha a comunicação

        Args:
            cod_cliente_or_conn: cod_cliente (str) para buscar conexão do cliente, ou
                                instância de SapConnection (model) se já tiver o registro
            rfc_name: nome do módulo de função RFC (ex: '/BRGMN/CUSTR_IMP_CUSTO')
            **params: parâmetros nomeados da chamada RFC (ex: I_V_BUKRS=..., I_V_BRANCH=...)

        Returns:
            tuple (success: bool, result_or_error)
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] call: PyRFC não disponível")
            return False, SapRfc.pyrfc_mensagem_indisponivel()
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            print(f"[SapRfc] call: nenhuma conexão para cliente '{cod}'")
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            print(f"[SapRfc] call: chamando RFC '{rfc_name}' (params keys: {list(params.keys())})")
            sap = SapRfc.connect(conn)
            if sap is None:
                print("[SapRfc] call: falha ao abrir conexão SAP")
                err = getattr(SapRfc, '_last_connect_error', '') or "Falha ao abrir conexão SAP."
                return False, SapRfc._mensagem_erro_com_vpn(err)
            result = sap.call(rfc_name, **params)
            print(f"[SapRfc] call: RFC '{rfc_name}' executado com sucesso (result type={type(result).__name__})")
            return True, result
        except Exception as e:
            print(f"[SapRfc] call: EXCEÇÃO ao chamar RFC '{rfc_name}': {e}")
            return False, SapRfc._mensagem_erro_com_vpn(str(e))
        finally:
            if sap is not None:
                try:
                    sap.close()
                    print("[SapRfc] call: conexão SAP fechada")
                except Exception as ex:
                    print(f"[SapRfc] call: aviso ao fechar conexão: {ex}")

    @staticmethod
    def with_connection(cod_cliente_or_conn, callback, close=True):
        """
        Abre uma conexão SAP (por cod_cliente ou registro SapConnection) e chama callback(sap).
        Útil para várias chamadas RFC na mesma conexão.

        Args:
            cod_cliente_or_conn: cod_cliente (str) ou instância de SapConnection (model)
            callback: função que recebe (sap) e retorna o que quiser
            close: se True, fecha a conexão ao final

        Returns:
            tuple (success: bool, result_or_error)
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] with_connection: PyRFC não disponível")
            return False, SapRfc.pyrfc_mensagem_indisponivel()
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            print(f"[SapRfc] with_connection: nenhuma conexão para cliente '{cod}'")
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            print("[SapRfc] with_connection: abrindo conexão para callback")
            sap = SapRfc.connect(conn)
            if sap is None:
                print("[SapRfc] with_connection: falha ao abrir conexão")
                return False, "Falha ao abrir conexão SAP."
            result = callback(sap)
            print("[SapRfc] with_connection: callback executado com sucesso")
            return True, result
        except Exception as e:
            print(f"[SapRfc] with_connection: EXCEÇÃO no callback: {e}")
            return False, str(e)
        finally:
            if close and sap is not None:
                try:
                    sap.close()
                    print("[SapRfc] with_connection: conexão fechada")
                except Exception as ex:
                    print(f"[SapRfc] with_connection: aviso ao fechar: {ex}")

    @staticmethod
    def run_for_active_connections(rfc_name, cod_cliente=None, params_callback=None, call_callback=None):
        """
        Itera sobre conexões SapConnection ativas e, para cada uma, abre conexão e chama o RFC.
        A conexão é por cliente: use cod_cliente para processar apenas esse cliente.

        Args:
            rfc_name: nome do RFC (ex: '/BRGMN/CUSTR_IMP_CUSTO')
            cod_cliente: opcional. Se informado, usa apenas conexões desse cliente (tabela SapConnection).
            params_callback: opcional. (conn) -> iterável de parâmetros.
            call_callback: opcional. (sap, conn) -> resultado.

        Exemplo:
            for conn, result in SapRfc.run_for_active_connections(
                '/BRGMN/CUSTR_IMP_CUSTO', cod_cliente='CLI01', params_callback=params_por_conexao
            ):
                print(conn, result)
        """
        if not PYRFC_AVAILABLE:
            print("❌ PyRFC não disponível. SAP desativado.")
            return
        conn_list = SapRfc.get_active_connections(cod_cliente=cod_cliente)
        if not conn_list:
            print(f"⚠️ Nenhuma conexão SAP ativa para o cliente '{cod_cliente or '(todos)'}'.")
            return
        for conn in conn_list:
            if call_callback:
                success, result = SapRfc.with_connection(conn, lambda sap: call_callback(sap, conn))
                if not success:
                    print(f"⚠️ Conexão {conn} (id={conn.id}): {result}")
                continue
            params_iter = params_callback(conn) if params_callback else None
            if params_iter is None:
                continue
            sap = SapRfc.connect(conn)
            if sap is None:
                print(f"⚠️ Nenhuma conexão aberta para {conn} (id={conn.id}).")
                continue
            try:
                for param_set in params_iter:
                    try:
                        if isinstance(param_set, dict):
                            result = sap.call(rfc_name, **param_set)
                        else:
                            result = sap.call(rfc_name, *param_set)
                        if result is not None:
                            yield (conn, result)
                    except Exception as e:
                        print(f"⚠️ Erro ao chamar {rfc_name} na conexão {conn.id}: {e}")
            finally:
                try:
                    sap.close()
                except Exception:
                    pass

    # -------------------------------------------------------------------------
    # Métodos de funcionalidade: um método por RFC (conexão → chamada → fechar)
    # -------------------------------------------------------------------------

    @staticmethod
    def importar_custo_cliente(cod_cliente, bukrs, branch, psdat_ini, psdat_fim):
        """
        Exemplo de método por funcionalidade:
          1. Chama o responsável pela conexão (SapRfc.call obtém conexão por cod_cliente).
          2. Chama a função RFC com os parâmetros.
          3. A comunicação é fechada ao final (SapRfc.call já faz isso).

        Returns:
            tuple (success: bool, result_or_error)
        """
        print(f"[SapRfc] importar_custo_cliente: cod_cliente={cod_cliente!r} bukrs={bukrs} branch={branch} psdat_ini={psdat_ini} psdat_fim={psdat_fim}")
        ok, res = SapRfc.call(
            cod_cliente,
            '/PRCIT/GDF_condicoes_pagamento',
            I_V_BUKRS=bukrs,
            I_V_BRANCH=branch,
            I_V_PSDAT_INI=psdat_ini,
            I_V_PSDAT_FIM=psdat_fim,
        )
        print(f"[SapRfc] importar_custo_cliente: resultado success={ok} result_type={type(res).__name__}")
        return ok, res

    @staticmethod
    def importar_relatorio_custo(cod_cliente, bukrs, branch, psdat_ini, psdat_fim, empresa=None, filial=None, persistir=True):
        """
        Chama a RFC /BRGMN/CUSTR_IMP_CUSTO para importar dados de custo do SAP e,
        se persistir=True, grava na tabela sap.relatorio_custo (RelatorioCusto),
        vinculando à Empresa e Filial do GDF.

        Args:
            cod_cliente: Código do cliente GDF (para conexão SAP).
            bukrs: Código da empresa no SAP (string ou objeto com atributo .bukrs).
            branch: Filial/ramo no SAP (string).
            psdat_ini: Data inicial do período (string ou date, formato aceito pelo SAP).
            psdat_fim: Data final do período (string ou date).
            empresa: Opcional. Instância de Empresa (GDF) para vincular aos registros.
                     Se None, tenta resolver por cod_empresa=bukrs.
            filial: Opcional. Instância de Filial (GDF) para vincular.
                    Se None e empresa informada, tenta Filial com cod_filial=branch.
            persistir: Se True, grava o retorno da RFC na tabela sap.relatorio_custo.

        Returns:
            dict: {
                'sucesso': bool,
                'mensagem': str,
                'total_linhas': int (linhas retornadas pela RFC),
                'total_gravados': int (registros inseridos/atualizados, se persistir=True),
                'resultado_rfc': result bruto da RFC (se sucesso),
            }
        """
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        from app.db_GDF.Public.models import Empresa, Filial
        from app.db_GDF.Sap.models import RelatorioCusto

        # Normalizar bukrs (aceitar objeto com .bukrs ou string)
        _bukrs = getattr(bukrs, 'bukrs', bukrs)
        if _bukrs is None:
            _bukrs = ''
        _bukrs = str(_bukrs).strip()

        print(f"[SapRfc] importar_relatorio_custo: cod_cliente={cod_cliente!r} bukrs={_bukrs} branch={branch} psdat_ini={psdat_ini} psdat_fim={psdat_fim} persistir={persistir}")

        if not SapRfc.is_available():
            return {
                'sucesso': False,
                'mensagem': SapRfc.pyrfc_mensagem_indisponivel(),
                'total_linhas': 0,
                'total_gravados': 0,
                'resultado_rfc': None,
            }

        ok, result = SapRfc.call(
            cod_cliente,
            "/BRGMN/CUSTR_IMP_CUSTO",
            I_V_BUKRS=_bukrs,
            I_V_BRANCH=branch or '',
            I_V_PSDAT_INI=psdat_ini,
            I_V_PSDAT_FIM=psdat_fim,
        )

        if not ok:
            return {
                'sucesso': False,
                'mensagem': result or 'Erro ao chamar RFC /BRGMN/CUSTR_IMP_CUSTO.',
                'total_linhas': 0,
                'total_gravados': 0,
                'resultado_rfc': None,
            }

        # Tabela de retorno da RFC /BRGMN/CUSTR_IMP_CUSTO
        table_data = result.get("T_RELAT003", []) if result and isinstance(result, dict) else []
        linhas = table_data if isinstance(table_data, list) else (list(table_data) if table_data else [])

        total_linhas = len(linhas)
        print(f"[SapRfc] importar_relatorio_custo: RFC retornou {total_linhas} linha(s)")

        if not persistir or total_linhas == 0:
            return {
                'sucesso': True,
                'mensagem': f'RFC executada. {total_linhas} linha(s) retornada(s).',
                'total_linhas': total_linhas,
                'total_gravados': 0,
                'resultado_rfc': result,
            }

        # Resolver Empresa e Filial para vincular
        if empresa is None and _bukrs:
            empresa = Empresa.objects.filter(cod_empresa=_bukrs).first()
        if filial is None and empresa and branch:
            filial = Filial.objects.filter(empresa=empresa, cod_filial=str(branch).strip()).first()

        # Mapeamento: nome da coluna no retorno SAP (uppercase) -> campo do modelo RelatorioCusto
        MAPEAMENTO_SAP = {
            'DOCNUM': 'docnum', 'MJAHR': 'mjahr', 'MBLNR': 'mblnr', 'MATNR': 'matnr', 'NFENUM': 'nfenum',
            'SERIES': 'series', 'DOCSTA': 'docsta', 'KUNNR': 'kunnr', 'NAME1': 'name1', 'ORT01': 'ort01',
            'CHAVE_ACESSO': 'chave_acesso', 'ITMNUM': 'itmnum', 'PSTDAT': 'pstdat', 'WERKS': 'werks',
            'NAME': 'name', 'STCD1': 'stcd1', 'UF_ORIGEM': 'uf_origem', 'UF_DESTINO': 'uf_destino',
            'CANCEL': 'cancel', 'MAKTX': 'maktx', 'MTART': 'mtart', 'MATKL': 'matkl', 'WGBEZ': 'wgbez',
            'CFOP': 'cfop', 'QTD_PROD': 'qtd_prod', 'UNID_MEDIDA': 'unid_medida', 'MEINS': 'meins',
            'UMREZ': 'umrez', 'MENGE_UMB': 'menge_umb', 'PRC_UNITARIO': 'prc_unitario',
            'PRC_UNIT_CST_LIQ': 'prc_unit_cst_liq', 'PRC_UNIT_CST_ADM': 'prc_unit_cst_adm',
            'BC_ICMS': 'bc_icms', 'PCT_ICMS': 'pct_icms', 'VLR_ICMS': 'vlr_icms',
            'BC_ICMS_ST': 'bc_icms_st', 'ALQ_ST': 'alq_st', 'VLR_ST': 'vlr_st',
            'BC_IPI': 'bc_ipi', 'PCT_IPI': 'pct_ipi', 'VLR_IPI': 'vlr_ipi',
            'BC_PIS': 'bc_pis', 'PCT_PIS': 'pct_pis', 'VLR_PIS': 'vlr_pis',
            'BC_COF': 'bc_cof', 'PCT_COF': 'pct_cof', 'VLR_COF': 'vlr_cof',
            'TP_DOC': 'tp_doc', 'TOTAL_IMPOSTOS': 'total_impostos', 'VLR_DESCONTO': 'vlr_desconto',
            'VLR_FRETE': 'vlr_frete', 'VLR_LIQUIDO': 'vlr_liquido', 'VLR_TOT_DOC': 'vlr_tot_doc',
            'CMV': 'cmv', 'LUCRO_0': 'lucro_0', 'MARGEM_0': 'margem_0', 'MARGEM_CONTRIB': 'margem_contrib',
            'CMV_GERENCIAL': 'cmv_gerencial', 'LUCRO_0_GERENCIAL': 'lucro_0_gerencial',
            'MARGEM_REAL': 'margem_real', 'LUCRO_REAL': 'lucro_real', 'MARGEM_CONTRIB_GER': 'margem_contrib_ger',
            'CMV_MEDIA': 'cmv_media', 'PER_TAXA_ADM': 'per_taxa_adm', 'VLR_TAXA_ADM': 'vlr_taxa_adm',
            'PER_TAXA_FRT': 'per_taxa_frt', 'VLR_TAXA_FRT': 'vlr_taxa_frt', 'CMV_UE': 'cmv_ue',
        }

        def _to_decimal(val):
            if val is None or val == '':
                return None
            if isinstance(val, Decimal):
                return val
            try:
                return Decimal(str(val).replace(',', '.'))
            except (InvalidOperation, TypeError):
                return None

        def _to_date(val):
            if val is None or val == '':
                return None
            if hasattr(val, 'date'):
                return val.date() if hasattr(val, 'date') else val
            if isinstance(val, str):
                for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
                    try:
                        return datetime.strptime(val[:10], fmt).date()
                    except (ValueError, TypeError):
                        continue
            return None

        gravados = 0
        for row in linhas:
            if not isinstance(row, dict):
                row = dict(row) if hasattr(row, 'keys') else {}
            row_upper = {str(k).strip().upper(): v for k, v in row.items()}
            kwargs = {'empresa': empresa, 'filial': filial}
            for sap_key, model_field in MAPEAMENTO_SAP.items():
                val = row_upper.get(sap_key) or row_upper.get(model_field.upper())
                if val is None:
                    continue
                if model_field == 'pstdat':
                    kwargs[model_field] = _to_date(val)
                elif model_field in (
                    'qtd_prod', 'umrez', 'menge_umb', 'prc_unitario', 'prc_unit_cst_liq', 'prc_unit_cst_adm',
                    'bc_icms', 'pct_icms', 'vlr_icms', 'bc_icms_st', 'alq_st', 'vlr_st',
                    'bc_ipi', 'pct_ipi', 'vlr_ipi', 'bc_pis', 'pct_pis', 'vlr_pis', 'bc_cof', 'pct_cof', 'vlr_cof',
                    'total_impostos', 'vlr_desconto', 'vlr_frete', 'vlr_liquido', 'vlr_tot_doc',
                    'cmv', 'lucro_0', 'margem_0', 'margem_contrib', 'cmv_gerencial', 'lucro_0_gerencial',
                    'margem_real', 'lucro_real', 'margem_contrib_ger', 'cmv_media',
                    'per_taxa_adm', 'vlr_taxa_adm', 'per_taxa_frt', 'vlr_taxa_frt', 'cmv_ue',
                ):
                    kwargs[model_field] = _to_decimal(val)
                else:
                    kwargs[model_field] = str(val).strip()

            docnum = (kwargs.get('docnum') or '').strip()
            mjahr = (kwargs.get('mjahr') or '').strip() or None
            mblnr = (kwargs.get('mblnr') or '').strip() or None
            if not docnum:
                continue
            kwargs.setdefault('docsta', ' ')
            key_fields = ('empresa', 'docnum', 'mjahr', 'mblnr')
            defaults = {}
            for k, v in kwargs.items():
                if k in key_fields or v is None:
                    continue
                try:
                    f = RelatorioCusto._meta.get_field(k)
                    if hasattr(f, 'max_length') and f.max_length and isinstance(v, str) and len(v) > f.max_length:
                        v = v[: f.max_length]
                except Exception:
                    pass
                defaults[k] = v
            try:
                RelatorioCusto.objects.update_or_create(
                    empresa=empresa,
                    docnum=docnum,
                    mjahr=mjahr,
                    mblnr=mblnr,
                    defaults=defaults,
                )
                gravados += 1
            except Exception as e:
                print(f"[SapRfc] importar_relatorio_custo: erro ao gravar linha docnum={docnum}: {e}")

        print(f"[SapRfc] importar_relatorio_custo: {gravados} registro(s) gravado(s) em sap.relatorio_custo")
        return {
            'sucesso': True,
            'mensagem': f'RFC executada. {total_linhas} linha(s) retornada(s), {gravados} gravado(s) em sap.relatorio_custo.',
            'total_linhas': total_linhas,
            'total_gravados': gravados,
            'resultado_rfc': result,
        }

    @staticmethod
    def consultar_balanco_financeiro(cod_cliente, **params):
        """
        RFC ZF_ECF01 — balanço financeiro (T_BALANCE, R_RETURN).

        Parâmetros em params (API/UI), alinhados à RFC:
          I_BUKRS, I_MONTH_B, I_MONTH_V, I_YEAR, I_KTOPL, I_VERSN — na API: i_bukrs, i_month_b,
          i_month_v, i_year, i_ktopl, i_versn (aceita também I_*). Aliases: i_month_ini / i_month_fim
          no lugar de i_month_b / i_month_v. Período único: i_month + i_year (envia B = V).

        Uma única chamada RFC; cada linha traz ano_referencia, mes_referencia_b e mes_referencia_v.

        Retorno: dict com sucesso, mensagem, r_return, t_balance, total_linhas, colunas.
        """
        i_bukrs = str(params.get("i_bukrs") or params.get("I_BUKRS") or "").strip()
        intervalo, err_intervalo = _zf_ecf01_resolver_intervalo_meses(params)
        if err_intervalo or not intervalo:
            return {
                "sucesso": False,
                "mensagem": err_intervalo or "Não foi possível determinar o período.",
                "r_return": "",
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }
        ref_year, month_b, month_v = intervalo
        i_ktopl = str(params.get("i_ktopl") or params.get("I_KTOPL") or "").strip()
        i_versn = str(params.get("i_versn") or params.get("I_VERSN") or "").strip()

        if not i_bukrs:
            return {
                "sucesso": False,
                "mensagem": "Empresa (I_BUKRS) é obrigatória.",
                "r_return": "",
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }
        if not i_ktopl or not i_versn:
            return {
                "sucesso": False,
                "mensagem": "Plano de contas (I_KTOPL) e versão (I_VERSN) são obrigatórios.",
                "r_return": "",
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }

        if not SapRfc.is_available():
            return {
                "sucesso": False,
                "mensagem": SapRfc.pyrfc_mensagem_indisponivel(),
                "r_return": "",
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }

        rfc_params = _zf_ecf01_montar_parametros(
            i_bukrs, month_b, month_v, ref_year, i_ktopl, i_versn
        )
        print(
            f"[SapRfc] consultar_balanco_financeiro: cod_cliente={cod_cliente!r} "
            f"I_BUKRS={rfc_params['I_BUKRS']} I_MONTH_B={rfc_params['I_MONTH_B']} "
            f"I_MONTH_V={rfc_params['I_MONTH_V']} I_YEAR={rfc_params['I_YEAR']}"
        )
        ok, result = SapRfc.call(cod_cliente, _RFC_BALANCO_FINANCEIRO, **rfc_params)

        if not ok:
            err = str(result or f"Erro ao chamar RFC {_RFC_BALANCO_FINANCEIRO}.")
            return {
                "sucesso": False,
                "mensagem": err,
                "r_return": "",
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }

        linhas_brutas, r_return = _zf_ecf01_extrair_t_balance_e_return(
            result if isinstance(result, dict) else None
        )
        linhas_proc = [
            _zf_ecf01_processar_linha_t_balance(row) for row in linhas_brutas if isinstance(row, dict)
        ]
        if not linhas_proc and r_return:
            return {
                "sucesso": False,
                "mensagem": r_return,
                "r_return": r_return,
                "t_balance": [],
                "total_linhas": 0,
                "colunas": [],
            }

        t_balance: List[Dict[str, Any]] = []
        for proc in linhas_proc:
            linha = {
                "ano_referencia": ref_year,
                "mes_referencia_b": month_b,
                "mes_referencia_v": month_v,
                **proc,
            }
            t_balance.append(linha)

        colunas: List[str] = list(T_BALANCE_COLUNAS_RESPOSTA) if t_balance else []
        label_periodo = f"{ref_year}: I_MONTH_B={month_b} … I_MONTH_V={month_v}"
        if month_b == month_v:
            msg_ok = (
                "Dados obtidos com sucesso." if t_balance else "Nenhuma linha retornada para os filtros informados."
            )
        else:
            msg_ok = (
                f"Dados obtidos com sucesso ({label_periodo})."
                if t_balance
                else f"Nenhuma linha retornada ({label_periodo})."
            )
        print(f"[SapRfc] consultar_balanco_financeiro: {len(t_balance)} linha(s) em T_BALANCE")
        return {
            "sucesso": True,
            "mensagem": msg_ok,
            "r_return": r_return or "",
            "t_balance": t_balance,
            "total_linhas": len(t_balance),
            "colunas": colunas,
        }


def enviar_condicoes_pagamento_sap(id_lote, cod_cliente, condicoes_lista):
    """
    Envia as condições de pagamento ao SAP via RFC e retorna o que o SAP aplicou por chave.
    Usa cod_cliente (do lote/grupo) para obter a conexão SAP.

    Args:
        id_lote: ID do lote (reprocessamento).
        cod_cliente: Código do cliente GDF (para mapear conexão SAP).
        condicoes_lista: Lista de dict com chave_nfe, numero_nfe, serie_nfe,
                         condicao_pagamento_nfe, condicao_pagamento_sap (opcional).

    Returns:
        dict: {
            'sucesso': bool,
            'mensagem': str,
            'retornos': [ {'chave_nfe': str, 'condicao_sap': str}, ... ]
        }
    """
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: INÍCIO id_lote={id_lote} cod_cliente={cod_cliente!r} qtd_condicoes={len(condicoes_lista) if condicoes_lista else 0}")

    if not condicoes_lista:
        print("[SapRfc] enviar_condicoes_pagamento_sap: lista vazia, retornando sucesso sem envio")
        return {'sucesso': True, 'mensagem': 'Nenhum registro para enviar.', 'retornos': []}

    if not SapRfc.is_available():
        print("[SapRfc] enviar_condicoes_pagamento_sap: PyRFC não disponível")
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': SapRfc.pyrfc_mensagem_indisponivel(),
            'retornos': retornos,
        }

    if not cod_cliente:
        print("[SapRfc] enviar_condicoes_pagamento_sap: cod_cliente não informado")
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': 'Cliente não informado. Não é possível obter conexão SAP.',
            'retornos': retornos,
        }

    # Mapear para estrutura ZGDF_S_COND_PAGAMENTO: CHAVE, COND_PAG_NFE, COND_PAG_SAP
    # (SAP retorna a mesma tabela com STATUS preenchido em R_T_COND)
    t_cond_pagamento = []
    for c in condicoes_lista:
        t_cond_pagamento.append({
            'CHAVE': (c.get('chave_nfe') or '')[:44],
            'COND_PAG_NFE': (c.get('condicao_pagamento_nfe') or '')[:50],
            'COND_PAG_SAP': (c.get('condicao_pagamento_sap') or '')[:4],
        })
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: montada tabela T_COND_PAGAMENTO com {len(t_cond_pagamento)} registro(s), chamando RFC ZGDF_CONDICOES_PAGAMENTO")

    success, result = SapRfc.call(
        cod_cliente,
        'ZGDF_CONDICOES_PAGAMENTO',
        T_COND_PAGAMENTO=t_cond_pagamento,
    )

    # Status válidos do modelo CondicaoPagamentoLote: P, E, S, U, I, R
    STATUS_VALIDOS = ('P', 'E', 'S', 'U', 'I', 'R')

    retornos = [
        {
            'chave_nfe': (c.get('chave_nfe') or ''),
            'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-'),
            'status': 'R',
        }
        for c in condicoes_lista
    ]
    if not success:
        print(f"[SapRfc] enviar_condicoes_pagamento_sap: FALHA na chamada RFC - {result}")
        return {
            'sucesso': False,
            'mensagem': result or 'Erro ao chamar SAP.',
            'retornos': retornos,
        }
    # SAP retorna R_T_COND (mesma tabela com STATUS: P, E, S, U, I, R)
    if result:
        r_t_cond = result.get('R_T_COND') or result.get('T_COND_PAGAMENTO') or []
        print(f"[SapRfc] enviar_condicoes_pagamento_sap: RFC retornou result com {len(r_t_cond)} item(ns) em R_T_COND/T_COND_PAGAMENTO")
        retornos = []
        for r in r_t_cond:
            status_sap = (r.get('STATUS') or r.get('status') or '').strip().upper()[:1]
            status_lote = status_sap if status_sap in STATUS_VALIDOS else 'S'
            retornos.append({
                'chave_nfe': (r.get('CHAVE') or r.get('chave') or ''),
                'condicao_sap': (r.get('COND_PAG_SAP') or r.get('cond_pag_sap') or ''),
                'status': status_lote,
            })
    else:
        print("[SapRfc] enviar_condicoes_pagamento_sap: RFC retornou result vazio/None, usando retornos padrão")
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: SUCESSO - {len(retornos)} retorno(s)")
    return {
        'sucesso': True,
        'mensagem': f'{len(retornos)} registro(s) enviado(s) ao SAP.',
        'retornos': retornos,
    }
