"""
Comunicação RFC com SAP usando a tabela SapConnection.

Padrão de uso para cada função SAP via RFC:
  1. Crie um método com o nome da funcionalidade (ex: importar_custo_cliente).
  2. Esse método chama o responsável pela conexão (SapRfc.call ou SapRfc.with_connection).
  3. Chame a função RFC passando os parâmetros.
  4. A comunicação é fechada ao final (SapRfc.call já abre, chama e fecha).

Exemplo: ver método importar_custo_cliente abaixo.
"""
try:
    from pyrfc import Connection as PyRfcConnection
    PYRFC_AVAILABLE = True
except ImportError:
    PyRfcConnection = None
    PYRFC_AVAILABLE = False


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

    # -------------------------------------------------------------------------
    # Conexão e chamada genérica (use estes dentro dos métodos de funcionalidade)
    # -------------------------------------------------------------------------

    @staticmethod
    def is_available():
        """Retorna True se o PyRFC está instalado."""
        return PYRFC_AVAILABLE

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
            print(f"[SapRfc] connect: ERRO ao conectar SAP (conn id={getattr(conn, 'id', conn)}): {e}")
            return None

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
            return False, "PyRFC não disponível. SAP desativado."
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
                return False, "Falha ao abrir conexão SAP."
            result = sap.call(rfc_name, **params)
            print(f"[SapRfc] call: RFC '{rfc_name}' executado com sucesso (result type={type(result).__name__})")
            return True, result
        except Exception as e:
            print(f"[SapRfc] call: EXCEÇÃO ao chamar RFC '{rfc_name}': {e}")
            return False, str(e)
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
            return False, "PyRFC não disponível. SAP desativado."
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
            'mensagem': 'PyRFC não disponível. SAP desativado.',
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
