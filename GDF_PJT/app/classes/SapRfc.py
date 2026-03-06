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
            return None
        SapConnection = _get_sap_connection_model()
        return SapConnection.objects.filter(gdfcliente_id=cod_cliente, active=True).first()

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
            return None
        config = SapRfc.config_from_connection(conn)
        try:
            return PyRfcConnection(**config)
        except Exception as e:
            print(f"❌ Erro ao conectar SAP (conn id={getattr(conn, 'id', conn)}): {e}")
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
            return False, "PyRFC não disponível. SAP desativado."
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            sap = SapRfc.connect(conn)
            if sap is None:
                return False, "Falha ao abrir conexão SAP."
            result = sap.call(rfc_name, **params)
            return True, result
        except Exception as e:
            return False, str(e)
        finally:
            if sap is not None:
                try:
                    sap.close()
                except Exception:
                    pass

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
            return False, "PyRFC não disponível. SAP desativado."
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            sap = SapRfc.connect(conn)
            if sap is None:
                return False, "Falha ao abrir conexão SAP."
            result = callback(sap)
            return True, result
        except Exception as e:
            return False, str(e)
        finally:
            if close and sap is not None:
                try:
                    sap.close()
                except Exception:
                    pass

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
        return SapRfc.call(
            cod_cliente,
            '/PRCIT/GDF_condicoes_pagamento',
            I_V_BUKRS=bukrs,
            I_V_BRANCH=branch,
            I_V_PSDAT_INI=psdat_ini,
            I_V_PSDAT_FIM=psdat_fim,
        )


def enviar_condicoes_pagamento_sap(id_lote, cod_empresa, condicoes_lista):
    """
    Envia as condições de pagamento ao SAP via RFC e retorna o que o SAP aplicou por chave.
    Usa a tabela SapConnection para obter conexões ativas (por cliente/empresa).

    Args:
        id_lote: ID do lote (reprocessamento).
        cod_empresa: Código da empresa (para mapear sistema SAP).
        condicoes_lista: Lista de dict com chave_nfe, numero_nfe, serie_nfe,
                         condicao_pagamento_nfe, condicao_pagamento_sap (opcional).

    Returns:
        dict: {
            'sucesso': bool,
            'mensagem': str,
            'retornos': [ {'chave_nfe': str, 'condicao_sap': str}, ... ]
        }
    """
    if not condicoes_lista:
        return {'sucesso': True, 'mensagem': 'Nenhum registro para enviar.', 'retornos': []}

    if not SapRfc.is_available():
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': 'PyRFC não disponível. SAP desativado.',
            'retornos': retornos,
        }

    from app.db_GDF.Public.models import Empresa

    cod_cliente = None
    try:
        empresa = Empresa.objects.select_related('cliente').get(cod_empresa=cod_empresa)
        if empresa.gdfcliente:
            cod_cliente = empresa.gdfcliente.cod_cliente
    except Empresa.DoesNotExist:
        pass

    if not cod_cliente:
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': 'Empresa sem cliente vinculado ou empresa não encontrada. Não é possível obter conexão SAP.',
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

    success, result = SapRfc.call(
        cod_cliente,
        'ZGDF_CONDICOES_PAGAMENTO',
        T_COND_PAGAMENTO=t_cond_pagamento,
    )

    retornos = [
        {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-'), 'status': 'S'}
        for c in condicoes_lista
    ]
    if not success:
        return {
            'sucesso': False,
            'mensagem': result or 'Erro ao chamar SAP.',
            'retornos': retornos,
        }
    # SAP retorna R_T_COND (mesma tabela com STATUS preenchido: U=update, I=insert)
    if result:
        r_t_cond = result.get('R_T_COND') or result.get('T_COND_PAGAMENTO') or []
        retornos = []
        for r in r_t_cond:
            status_sap = (r.get('STATUS') or r.get('status') or '').strip().upper()
            status_lote = 'U' if status_sap == 'U' else ('I' if status_sap == 'I' else 'S')
            retornos.append({
                'chave_nfe': (r.get('CHAVE') or r.get('chave') or ''),
                'condicao_sap': (r.get('COND_PAG_SAP') or r.get('cond_pag_sap') or ''),
                'status': status_lote,
            })
    return {
        'sucesso': True,
        'mensagem': f'{len(retornos)} registro(s) enviado(s) ao SAP.',
        'retornos': retornos,
    }
