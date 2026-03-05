
from django.db.models               import Prefetch
from psycopg2                       import IntegrityError
from django.contrib.auth.models     import User, Group
from app.db_GDF.Public.models       import Clientes, Empresas
from app.db_GDF.NFe.models          import (
    NFe, NFe_Total, NFe_Produto, NFe_Identificacao, NFe_Emitente, NFe_Destinatario,
    NFe_Endereco, NFe_ICMS, NFe_IPI, NFe_PIS, NFe_COFINS, NFe_Transporte,
    NFe_Cobranca, NFe_Parcela, NFe_Pagamento, NFe_Informacoes_Adicionais, NFe_Evento
)
from app.db_GDF.CTe.models          import (
    CTe, CTe_Identificacao, CTe_Emitente, CTe_Destinatario, CTe_Transporte, CTe_Valor,
    CTe_Carga, CTe_Servico, CTe_Veiculo, CTe_Motorista, CTe_Percurso, CTe_Fiscal, CTe_Evento
)
from app.db_GDF.NFSe.models         import (
    NFSe, NFSe_Identificacao, NFSe_Prestador, NFSe_Tomador, NFSe_Servico, NFSe_Endereco,
    NFSe_RPS, NFSe_Retencao, NFSe_Pagamento, NFSe_Credenciamento, NFSe_Evento
)
from typing                        import List, Dict, Optional
from datetime import datetime, time
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
import xml.etree.ElementTree as ET


class EmpresaNaoCadastradaError(Exception):
    """XML não será registrado: CNPJ não pertence a nenhuma empresa cadastrada no GDF. Deve ir para pasta pendentes."""
    pass


def _find_first_child(parent, tag_names, ns):
    """Retorna o primeiro filho cuja tag (local name) está em tag_names."""
    if parent is None:
        return None
    for child in parent:
        local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if local in tag_names:
            return child
    return None


class Carga_xml():
    def __init__(self):
        self.ns = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'cte': 'http://www.portalfiscal.inf.br/cte',
            'nfse': 'http://www.abrasf.org.br/nfse'
        }
    
    def _get_text(self, element, path, default=''):
        """Extrai texto de elemento XML com fallback para namespace (nfe, cte, sem prefixo)"""
        if element is None:
            return default
        for prefix in ('nfe', 'cte'):
            result = element.findtext(f'.//{prefix}:{path}', default='', namespaces=self.ns)
            if result:
                return result or default
        result = element.findtext(f'.//{path}', default=default)
        return result or default
    
    def _to_decimal(self, value, default=0):
        """Converte string para Decimal"""
        try:
            return Decimal(value) if value else Decimal(default)
        except:
            return Decimal(default)
    
    def _to_datetime(self, value, format='%Y-%m-%d'):
        """Converte string para datetime (timezone-aware)"""
        try:
            if not value:
                return None

            parsed = parse_datetime(value)
            if parsed is None:
                parsed_date = parse_date(value)
                if parsed_date is None:
                    parsed = datetime.strptime(value, format)
                else:
                    parsed = datetime.combine(parsed_date, time.min)

            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed
        except:
            return None
    
    def _processar_endereco(self, element, is_emitente=True):
        """Processa endereço do emitente ou destinatário"""
        if element is None:
            return None
        
        tag_endereco = 'enderEmit' if is_emitente else 'enderDest'
        endereco_node = element.find(f'.//nfe:{tag_endereco}', self.ns) or element.find(f'.//{tag_endereco}')
        
        if endereco_node is None:
            return None
        
        return NFe_Endereco.objects.create(
            logradouro=self._get_text(endereco_node, 'xLgr'),
            numero=self._get_text(endereco_node, 'nro'),
            complemento=self._get_text(endereco_node, 'xCpl'),
            bairro=self._get_text(endereco_node, 'xBairro'),
            codigo_municipio=self._get_text(endereco_node, 'cMun'),
            uf=self._get_text(endereco_node, 'UF'),
            cep=self._get_text(endereco_node, 'CEP'),
            pais=self._get_text(endereco_node, 'cPais', '1058'),
            nome_municipio=self._get_text(endereco_node, 'xMun'),
            nome_pais=self._get_text(endereco_node, 'xPais', 'Brasil'),
            telefone=self._get_text(endereco_node, 'fone'),
            data_criacao=timezone.now()
        )
    
    def _processar_produtos(self, infNFe, identificacao):
        """Processa todos os produtos da NFe"""
        det_nodes = infNFe.findall('.//nfe:det', self.ns) or infNFe.findall('.//det')
        
        for det in det_nodes:
            # Dados do produto
            prod = det.find('.//nfe:prod', self.ns) or det.find('.//prod')
            if prod is None:
                continue
            
            # Criar produto
            produto = NFe_Produto.objects.create(
                nfe_serie=identificacao,
                numero_item=self._get_text(det, 'nItem', '1'),
                codigo_interno=self._get_text(prod, 'cProd'),
                ean=self._get_text(prod, 'cEAN'),
                descricao=self._get_text(prod, 'xProd'),
                ncm=self._get_text(prod, 'NCM'),
                cfop=self._get_text(prod, 'CFOP'),
                unidade=self._get_text(prod, 'uCom'),
                quantidade=self._to_decimal(self._get_text(prod, 'qCom')),
                valor_unitario=self._to_decimal(self._get_text(prod, 'vUnCom')),
                valor_total=self._to_decimal(self._get_text(prod, 'vProd')),
                ean_tributavel=self._get_text(prod, 'cEANTrib'),
                quantidade_tributavel=self._to_decimal(self._get_text(prod, 'qTrib')),
                valor_unitario_tributavel=self._to_decimal(self._get_text(prod, 'vUnTrib')),
                valor_desconto=self._to_decimal(self._get_text(prod, 'vDesc')),
                valor_outras_despesas=self._to_decimal(self._get_text(prod, 'vOutro')),
                data_criacao=timezone.now()
            )
            
            # Processar impostos
            imposto = det.find('.//nfe:imposto', self.ns) or det.find('.//imposto')
            if imposto:
                self._processar_impostos(imposto, produto)
    
    def _processar_impostos(self, imposto_node, produto):
        """Processa todos os impostos de um produto (ICMS, IPI, PIS, COFINS) — todos os tipos."""
        # ICMS
        icms_node = imposto_node.find('.//nfe:ICMS', self.ns) or imposto_node.find('.//ICMS')
        if icms_node:
            icms_tipo = None
            for child in icms_node:
                if 'ICMS' in child.tag:
                    icms_tipo = child
                    break
            if icms_tipo is not None:
                cst_val = (self._get_text(icms_tipo, 'CST') or self._get_text(icms_tipo, 'CSOSN', '00'))[:3]
                NFe_ICMS.objects.create(
                    produto=produto,
                    origem=self._get_text(icms_tipo, 'orig', '0'),
                    cst=cst_val or '00',
                    valor_base_calculo=self._to_decimal(self._get_text(icms_tipo, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(icms_tipo, 'pICMS')),
                    valor_icms=self._to_decimal(self._get_text(icms_tipo, 'vICMS')),
                    valor_base_st=self._to_decimal(self._get_text(icms_tipo, 'vBCST')),
                    valor_icms_st=self._to_decimal(self._get_text(icms_tipo, 'vICMSST')),
                )
        # IPI
        ipi_node = imposto_node.find('.//nfe:IPI', self.ns) or imposto_node.find('.//IPI')
        if ipi_node:
            ipi_trib = ipi_node.find('.//nfe:IPITrib', self.ns) or ipi_node.find('.//IPITrib')
            ipi_nt = ipi_node.find('.//nfe:IPINT', self.ns) or ipi_node.find('.//IPINT')
            if ipi_trib is not None:
                NFe_IPI.objects.create(
                    produto=produto,
                    cst=self._get_text(ipi_trib, 'CST', '99'),
                    valor_base_calculo=self._to_decimal(self._get_text(ipi_trib, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(ipi_trib, 'pIPI')),
                    valor_ipi=self._to_decimal(self._get_text(ipi_trib, 'vIPI'))
                )
            elif ipi_nt is not None:
                NFe_IPI.objects.create(
                    produto=produto,
                    cst=self._get_text(ipi_nt, 'CST', '99'),
                    valor_base_calculo=Decimal('0'),
                    aliquota=Decimal('0'),
                    valor_ipi=Decimal('0')
                )
        # PIS — PISAliq, PISQtde, PISOutr, PISNT, PISST
        pis_node = imposto_node.find('.//nfe:PIS', self.ns) or imposto_node.find('.//PIS')
        if pis_node:
            pis_el = _find_first_child(pis_node, ['PISAliq', 'PISQtde', 'PISOutr', 'PISNT', 'PISST'], self.ns)
            if pis_el is not None:
                cst = self._get_text(pis_el, 'CST', '99')
                vbc = self._to_decimal(self._get_text(pis_el, 'vBC') or self._get_text(pis_el, 'qBCProd'))
                pct = self._to_decimal(self._get_text(pis_el, 'pPIS') or self._get_text(pis_el, 'vAliqProd'))
                vpis = self._to_decimal(self._get_text(pis_el, 'vPIS'))
                qtd = self._to_decimal(self._get_text(pis_el, 'qBCProd'))
                aliq_qtd = self._to_decimal(self._get_text(pis_el, 'vAliqProd'))
                NFe_PIS.objects.create(
                    produto=produto,
                    cst=cst,
                    valor_base_calculo=vbc or Decimal('0'),
                    aliquota=pct,
                    valor_pis=vpis or Decimal('0'),
                    quantidade_vendida=qtd,
                    aliquota_quantidade=aliq_qtd,
                )
        # COFINS — COFINSAliq, COFINSQtde, COFINSOutr, COFINSNT, COFINSST
        cofins_node = imposto_node.find('.//nfe:COFINS', self.ns) or imposto_node.find('.//COFINS')
        if cofins_node:
            cofins_el = _find_first_child(cofins_node, ['COFINSAliq', 'COFINSQtde', 'COFINSOutr', 'COFINSNT', 'COFINSST'], self.ns)
            if cofins_el is not None:
                cst = self._get_text(cofins_el, 'CST', '99')
                vbc = self._to_decimal(self._get_text(cofins_el, 'vBC') or self._get_text(cofins_el, 'qBCProd'))
                pct = self._to_decimal(self._get_text(cofins_el, 'pCOFINS') or self._get_text(cofins_el, 'vAliqProd'))
                vcof = self._to_decimal(self._get_text(cofins_el, 'vCOFINS'))
                qtd = self._to_decimal(self._get_text(cofins_el, 'qBCProd'))
                aliq_qtd = self._to_decimal(self._get_text(cofins_el, 'vAliqProd'))
                NFe_COFINS.objects.create(
                    produto=produto,
                    cst=cst,
                    valor_base_calculo=vbc or Decimal('0'),
                    aliquota=pct,
                    valor_cofins=vcof or Decimal('0'),
                    quantidade_vendida=qtd,
                    aliquota_quantidade=aliq_qtd,
                )
    
    def _processar_total(self, infNFe, identificacao):
        """Processa totais da NFe"""
        total_node = infNFe.find('.//nfe:total', self.ns) or infNFe.find('.//total')
        if total_node is None:
            return None
        
        icms_tot = total_node.find('.//nfe:ICMSTot', self.ns) or total_node.find('.//ICMSTot')
        if icms_tot is None:
            return None
        
        # Usar update_or_create para evitar duplicatas
        total, _ = NFe_Total.objects.update_or_create(
            nfe_identificacao=identificacao,
            defaults={
                'valor_subtotal_produtos': self._to_decimal(self._get_text(icms_tot, 'vProd')),
                'valor_frete': self._to_decimal(self._get_text(icms_tot, 'vFrete')),
                'valor_seguro': self._to_decimal(self._get_text(icms_tot, 'vSeg')),
                'valor_desconto': self._to_decimal(self._get_text(icms_tot, 'vDesc')),
                'valor_outras_despesas': self._to_decimal(self._get_text(icms_tot, 'vOutro')),
                'valor_total_tributos': self._to_decimal(self._get_text(icms_tot, 'vTotTrib')),
                'valor_base_icms': self._to_decimal(self._get_text(icms_tot, 'vBC')),
                'valor_icms': self._to_decimal(self._get_text(icms_tot, 'vICMS')),
                'valor_icms_st': self._to_decimal(self._get_text(icms_tot, 'vST')),
                'valor_ipi': self._to_decimal(self._get_text(icms_tot, 'vIPI')),
                'valor_pis': self._to_decimal(self._get_text(icms_tot, 'vPIS')),
                'valor_cofins': self._to_decimal(self._get_text(icms_tot, 'vCOFINS')),
                'valor_total_nfe': self._to_decimal(self._get_text(icms_tot, 'vNF')),
            }
        )
        return total
    
    def _processar_cobranca(self, infNFe, identificacao):
        """Processa cobrança e parcelas da NFe"""
        cobr_node = infNFe.find('.//nfe:cobr', self.ns) or infNFe.find('.//cobr')
        if cobr_node is None:
            return None
        
        # Criar ou atualizar cobrança
        cobranca, _ = NFe_Cobranca.objects.update_or_create(
            nfe_identificacao=identificacao,
            defaults={
                'banco': self._get_text(cobr_node, 'nBanco'),
                'agencia': self._get_text(cobr_node, 'nAg'),
                'agencia_dv': self._get_text(cobr_node, 'dvAg'),
                'conta': self._get_text(cobr_node, 'nConta'),
                'conta_dv': self._get_text(cobr_node, 'dvConta'),
                'cnpj_banco': self._get_text(cobr_node, 'CNPJBanco'),
            }
        )
        
        # Processar parcelas (duplicatas)
        dup_nodes = cobr_node.findall('.//nfe:dup', self.ns) or cobr_node.findall('.//dup')
        
        # Remover parcelas antigas desta cobrança
        NFe_Parcela.objects.filter(nfe_cobranca=cobranca).delete()
        
        for idx, dup in enumerate(dup_nodes, start=1):
            lv_data_venc = self._get_text(dup, 'dVenc')
            lv_valor = self._to_decimal(self._get_text(dup, 'vDup'))
            
            if lv_data_venc and lv_valor:
                lv_dt_convertida = self._to_datetime(lv_data_venc, '%Y-%m-%d')
                NFe_Parcela.objects.create(
                    nfe_cobranca=cobranca,
                    numero_parcela=idx,
                    data_vencimento=lv_dt_convertida.date() if lv_dt_convertida else timezone.now().date(),
                    valor_parcela=lv_valor
                )
        
        return cobranca

    # Códigos de meio de pagamento aceitos pelo modelo NFe_Pagamento (para normalizar tPag do XML)
    _MEIO_PAGAMENTO_VALIDOS = frozenset(
        ('01', '02', '03', '04', '05', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '99')
    )

    def _processar_pagamento(self, infNFe, identificacao):
        """
        Processa o bloco pag/detPag da NFe e grava em NFe_Pagamento.
        Usa o primeiro detPag como meio_pagamento e soma todos os vPag em valor_pago.
        """
        pag_node = infNFe.find('.//nfe:pag', self.ns) or infNFe.find('.//pag')
        if pag_node is None:
            return None
        det_list = pag_node.findall('.//nfe:detPag', self.ns) or pag_node.findall('.//detPag')
        if not det_list:
            return None
        valor_total = Decimal('0')
        primeiro_tpag = None
        for det in det_list:
            vpag = self._to_decimal(self._get_text(det, 'vPag'))
            valor_total += vpag
            if primeiro_tpag is None:
                tpag = (self._get_text(det, 'tPag') or '').strip()
                if len(tpag) == 1:
                    tpag = '0' + tpag
                if tpag in self._MEIO_PAGAMENTO_VALIDOS:
                    primeiro_tpag = tpag
                else:
                    primeiro_tpag = '99'
        if primeiro_tpag is None or valor_total < 0:
            return None
        if valor_total == 0:
            valor_total = Decimal('0.01')
        NFe_Pagamento.objects.update_or_create(
            nfe_identificacao=identificacao,
            defaults={
                'meio_pagamento': primeiro_tpag,
                'valor_pago': valor_total,
            }
        )
        return None

    def _salvar_condicao_param_se_nao_existir(self, identificacao, cod_cliente=None):
        """
        Se a condição de pagamento da NFe ainda não existir em CondicaoParam, grava
        (cliente, condição NFe, tipo_pagamento, SAP vazio).
        Considera tipo_pagamento para permitir mesma condição com mapeamentos diferentes por tipo.
        Requer cod_cliente para gravar (cada cliente tem sua tabela de parâmetros).
        """
        if not cod_cliente:
            return
        from app.classes.Reprocessamento import condicao_pagamento_da_nfe, tipo_pagamento_da_nfe
        from app.db_Reprocessamento.models import CondicaoParam

        cond_nfe = condicao_pagamento_da_nfe(identificacao)
        if not (cond_nfe or '').strip():
            return
        cond_nfe = (cond_nfe or '').strip()[:120]
        tipo_pag = tipo_pagamento_da_nfe(identificacao) or None
        CondicaoParam.objects.get_or_create(
            cliente_id=cod_cliente,
            condicao_pagamento_nfe=cond_nfe,
            tipo_pagamento=tipo_pag,
            defaults={'condicao_pagamento_sap': ''},
        )

    def _processar_informacoes_adicionais(self, infNFe, identificacao):
        """
        Processa o bloco infAdic da NFe (informações adicionais) e grava em NFe_Informacoes_Adicionais.
        Tags: infCpl (informações complementares), infAdFisco (informações de interesse do fisco),
        xPed (número do pedido de compra - pode estar em infAdic, compra ou em qualquer nó sob infNFe).
        """
        inf_adic = infNFe.find('.//nfe:infAdic', self.ns) or infNFe.find('.//infAdic')
        inf_cpl = None
        inf_ad_fisco = None
        xped = None
        if inf_adic is not None:
            inf_cpl = self._get_text(inf_adic, 'infCpl', '').strip() or None
            inf_ad_fisco = self._get_text(inf_adic, 'infAdFisco', '').strip() or None
            xped = self._get_text(inf_adic, 'xPed', '').strip() or None
        if xped is None:
            compra = infNFe.find('.//nfe:compra', self.ns) or infNFe.find('.//compra')
            if compra is not None:
                xped = self._get_text(compra, 'xPed', '').strip() or None
        if xped is None:
            elem = infNFe.find('.//nfe:xPed', self.ns) or infNFe.find('.//xPed')
            if elem is not None and elem.text:
                xped = elem.text.strip() or None
        if inf_cpl is None and inf_ad_fisco is None and xped is None:
            return None
        NFe_Informacoes_Adicionais.objects.update_or_create(
            nfe_identificacao=identificacao,
            defaults={
                'informacoes_complementares': inf_cpl,
                'informacoes_interesse_fisco': inf_ad_fisco,
                'xped': xped,
            }
        )
        return None

    def _find_local(self, parent, *tag_names):
        """Busca filho por nome local (ignora namespace)."""
        if parent is None:
            return None
        for child in parent.iter():
            local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if local in tag_names:
                return child
        return None

    def _extrair_dados_evento(self, xml_data: bytes) -> Optional[Dict]:
        """
        Detecta se o XML é de evento (procEventoNFe, procEventoCTe) e extrai chave, tipo, justificativa.
        Retorna dict com chave, tipo_doc ('NFe'|'CTe'), tp_evento, desc_evento, justificativa, dh_evento, n_seq, xml_str
        ou None se não for XML de evento.
        """
        try:
            root = ET.fromstring(xml_data)
            tag_root = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            if tag_root not in ('procEventoNFe', 'procEventoCTe'):
                return None

            tipo_doc = 'NFe' if 'NFe' in tag_root else 'CTe'
            tag_chave = 'chNFe' if tipo_doc == 'NFe' else 'chCTe'

            inf_evento = self._find_local(root, 'infEvento')
            if inf_evento is None:
                return None

            chave = self._get_text(inf_evento, tag_chave, '').strip()
            if not chave or len(chave) != 44 or not chave.isdigit():
                return None

            tp_evento = self._get_text(inf_evento, 'tpEvento', '').strip()
            n_seq = int(self._get_text(inf_evento, 'nSeqEvento', '1') or '1')
            dh_evento = self._to_datetime(self._get_text(inf_evento, 'dhEvento'), '%Y-%m-%dT%H:%M:%S%z')

            det_evento = self._find_local(inf_evento, 'detEvento')
            desc_evento = ''
            justificativa = ''
            if det_evento is not None:
                desc_evento = self._get_text(det_evento, 'descEvento', '').strip()
                justificativa = self._get_text(det_evento, 'xJust', '').strip() or self._get_text(det_evento, 'xCorrecao', '').strip()

            return {
                'chave': chave,
                'tipo_doc': tipo_doc,
                'tp_evento': tp_evento,
                'desc_evento': desc_evento or tp_evento,
                'justificativa': justificativa,
                'dh_evento': dh_evento,
                'n_seq': n_seq,
                'xml_str': xml_data.decode('utf-8', errors='ignore'),
            }
        except Exception:
            return None

    def set_evento(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None) -> bool:
        """
        Processa XML de evento: busca a chave (44) em NFe, CTe e NFSe, salva evento e justificativa.
        Retorna True se processou com sucesso, False se não for evento ou chave não encontrada.
        """
        dados = self._extrair_dados_evento(xml_data)
        if not dados:
            return False

        chave = dados['chave']
        tipo_doc = dados['tipo_doc']
        tp_evento = dados['tp_evento']
        desc_evento = dados['desc_evento']
        justificativa = dados['justificativa']
        dh_evento = dados['dh_evento']
        n_seq = dados['n_seq']
        xml_str = dados['xml_str']

        # Buscar na ordem: NFe, CTe, NFSe (chave 44)
        identificacao_nfe = NFe_Identificacao.objects.filter(chave_acesso=chave).first()
        if identificacao_nfe:
            NFe_Evento.objects.update_or_create(
                nfe_identificacao=identificacao_nfe,
                tipo_evento=tp_evento,
                numero_sequencia=n_seq,
                defaults={
                    'descricao_evento': desc_evento,
                    'justificativa': justificativa,
                    'data_evento': dh_evento,
                    'xml_evento': xml_str,
                }
            )
            if tp_evento == '110111':  # Cancelamento
                NFe.objects.filter(identificacao=identificacao_nfe).update(status='CANCELADA', data_atualizacao=timezone.now())
            return True

        identificacao_cte = CTe_Identificacao.objects.filter(chave_acesso=chave).first()
        if identificacao_cte:
            CTe_Evento.objects.update_or_create(
                cte_identificacao=identificacao_cte,
                tipo_evento=tp_evento,
                numero_sequencia=n_seq,
                defaults={
                    'descricao_evento': desc_evento,
                    'justificativa': justificativa,
                    'data_evento': dh_evento,
                    'xml_evento': xml_str,
                }
            )
            return True

        identificacao_nfse = NFSe_Identificacao.objects.filter(chave=chave).first()
        if identificacao_nfse:
            NFSe_Evento.objects.update_or_create(
                nfse_identificacao=identificacao_nfse,
                tipo_evento=tp_evento,
                numero_sequencia=n_seq,
                defaults={
                    'descricao_evento': desc_evento,
                    'justificativa': justificativa,
                    'data_evento': dh_evento,
                    'xml_evento': xml_str,
                }
            )
            return True

        return False  # Chave não encontrada em nenhuma tabela

    def set_upload_xml(self, I_LsXml, i_type, I_origem_dados, i_usuario, i_cod_cliente=None) -> Dict:
        """
        Processa upload de múltiplos XMLs
        
        Args:
            I_LsXml: Lista de arquivos XML (Django UploadedFile)
            i_type: Tipo do documento ('NFe', 'CTe', 'NFSe')
            I_origem_dados: Origem dos dados ('LOCAL', 'SAP', 'SPED', 'OUTROS')
            i_usuario: Usuário que fez o upload
            i_cod_cliente: código do cliente para validação de empresas
        """
        result = {
            'success': [],
            'errors': [],
            'pendentes': []  # não registrados: empresa não cadastrada no GDF (devem ir para pasta pendentes)
        }

        for xml_file in I_LsXml:
            try:
                xml_data = xml_file.read()

                # Verificar se é XML de evento (procEventoNFe, procEventoCTe) - chave 44
                if self._extrair_dados_evento(xml_data):
                    if self.set_evento(xml_data, I_origem_dados, i_usuario, i_cod_cliente):
                        result['success'].append(xml_file.name)
                    else:
                        result['errors'].append({
                            'file': xml_file.name,
                            'error': 'Chave do evento não encontrada em NFe, CTe ou NFSe.',
                            'type': 'ChaveNaoEncontrada'
                        })
                    continue

                if i_type == 'NFe':
                    self.set_nfe(xml_data, I_origem_dados, i_usuario, i_cod_cliente)
                
                elif i_type == 'CTe':
                    self.set_cte(xml_data, I_origem_dados, i_usuario, i_cod_cliente)
                
                elif i_type == 'NFSe':
                    self.set_nfse(xml_data, I_origem_dados, i_usuario, i_cod_cliente)

                result['success'].append(xml_file.name)
            
            except EmpresaNaoCadastradaError as e:
                result['pendentes'].append({
                    'file': xml_file.name,
                    'motivo': str(e),
                })
            except Exception as e:
                result['errors'].append({
                    'file': xml_file.name, 
                    'error': str(e),
                    'type': type(e).__name__
                })

        return result
    
    def set_nfe(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None):
        """
        Processa e insere NFe no banco de dados com TODOS os campos
        Detecta automaticamente se é entrada ou saída e busca a empresa corretamente
        cod_cliente opcional é usado para validar que a empresa pertence ao cliente
        """
        try:
            # Fazer parse do XML
            root = ET.fromstring(xml_data)
            
            # Extrair dados básicos da NFe
            infNFe = root.find('.//nfe:infNFe', self.ns) or root.find('.//infNFe')
            if infNFe is None:
                raise ValueError("Estrutura de NFe inválida: infNFe não encontrado")
            
            # ========== IDENTIFICAÇÃO ==========
            ide = infNFe.find('.//nfe:ide', self.ns) or infNFe.find('.//ide')
            if ide is None:
                raise ValueError("Seção ide não encontrada")
            
            numero = self._get_text(ide, 'nNF')
            serie = self._get_text(ide, 'serie')
            chave_acesso = infNFe.get('Id', '').replace('NFe', '')
            
            if not numero or not serie:
                raise ValueError("Número e série são obrigatórios")
            
            # Dados de emissão e operação
            data_emissao = self._to_datetime(self._get_text(ide, 'dhEmi') or self._get_text(ide, 'dEmi'), '%Y-%m-%dT%H:%M:%S') or self._to_datetime(self._get_text(ide, 'dEmi'))
            data_saida = self._to_datetime(self._get_text(ide, 'dhSaiEnt') or self._get_text(ide, 'dSaiEnt'), '%Y-%m-%dT%H:%M:%S')
            # tpNF: 0 = Entrada, 1 = Saída (manual NFe). Default '0' para não marcar entrada como saída quando tag faltar.
            tipo_operacao = (self._get_text(ide, 'tpNF', '0') or '0').strip()
            if tipo_operacao not in ('0', '1'):
                # Fallback: inferir pelo primeiro CFOP (1,2,3 = entrada; 5,6,7 = saída)
                primeiro_cfop = None
                for det in (infNFe.findall('.//nfe:det', self.ns) or infNFe.findall('.//det'))[:1]:
                    prod = det.find('.//nfe:prod', self.ns) or det.find('.//prod')
                    if prod is not None:
                        primeiro_cfop = (self._get_text(prod, 'CFOP') or '').strip()
                        break
                if primeiro_cfop and len(primeiro_cfop) >= 1:
                    tipo_operacao = '0' if primeiro_cfop[0] in ('1', '2', '3') else '1'
                else:
                    tipo_operacao = '0'
            tipo_documento = self._get_text(ide, 'tpEmis', '1')
            
            # ========== EMITENTE ==========
            emit = infNFe.find('.//nfe:emit', self.ns) or infNFe.find('.//emit')
            emitente_cnpj = self._get_text(emit, 'CNPJ')
            
            if not emitente_cnpj:
                raise ValueError("CNPJ do emitente é obrigatório")
            
            # Processar endereço do emitente
            endereco_emit = self._processar_endereco(emit, is_emitente=True)
            
            # Criar/atualizar emitente completo
            emitente, _ = NFe_Emitente.objects.update_or_create(
                cnpj=emitente_cnpj,
                defaults={
                    'razao_social': self._get_text(emit, 'xNome', 'S/N'),
                    'nome_fantasia': self._get_text(emit, 'xFant'),
                    'ie': self._get_text(emit, 'IE'),
                    'ie_st': self._get_text(emit, 'IEST'),
                    'im': self._get_text(emit, 'IM'),
                    'cnae_fiscal': self._get_text(emit, 'CNAE'),
                    'crt': self._get_text(emit, 'CRT'),
                    'endereco': endereco_emit,
                    'data_atualizacao': timezone.now()
                }
            )
            
            # ========== DESTINATÁRIO ==========
            dest = infNFe.find('.//nfe:dest', self.ns) or infNFe.find('.//dest')
            destinatario = None
            destinatario_cnpj = None
            
            if dest is not None:
                # Pode ser CNPJ ou CPF
                destinatario_cnpj = self._get_text(dest, 'CNPJ') or self._get_text(dest, 'CPF')
                tipo_doc = '1' if self._get_text(dest, 'CNPJ') else '2'  # 1=CNPJ, 2=CPF
                
                if destinatario_cnpj:
                    # Processar endereço do destinatário
                    endereco_dest = self._processar_endereco(dest, is_emitente=False)
                    
                    destinatario, _ = NFe_Destinatario.objects.update_or_create(
                        documento=destinatario_cnpj,
                        defaults={
                            'tipo': tipo_doc,
                            'razao_social': self._get_text(dest, 'xNome', 'S/N'),
                            'ie': self._get_text(dest, 'IE'),
                            'isuf': self._get_text(dest, 'ISUF'),
                            'im': self._get_text(dest, 'IM'),
                            'email': self._get_text(dest, 'email'),
                            'endereco': endereco_dest,
                            'data_atualizacao': timezone.now()
                        }
                    )
            
            # ========== BUSCAR EMPRESA ==========
            # Se CNPJ não estiver cadastrado, grava com empresa=None (não é obrigatório informar empresa na carga)
            empresa = None
            cnpj_para_busca = None
            tipo_nfe = "SAÍDA" if tipo_operacao == '1' else "ENTRADA"
            
            if tipo_operacao == '1':  # SAÍDA
                cnpj_para_busca = destinatario_cnpj
            else:  # ENTRADA
                cnpj_para_busca = emitente_cnpj
            
            if cnpj_para_busca:
                try:
                    empresa = Empresas.objects.get(cnpj=cnpj_para_busca)
                    if cod_cliente and empresa.cliente and empresa.cliente.cod_cliente != cod_cliente:
                        empresa = None
                except Empresas.DoesNotExist:
                    empresa = None
            else:
                raise ValueError(f"Não foi possível identificar CNPJ da empresa (tipo: {tipo_nfe})")
            
            # Cliente: nunca vazio. Preferir empresa.cliente; se não encontrar, usar cod_cliente (cliente do usuário/parâmetro)
            cliente_eff = None
            if empresa and empresa.cliente:
                cliente_eff = empresa.cliente
            if not cliente_eff and cod_cliente:
                try:
                    cliente_eff = Clientes.objects.get(cod_cliente=cod_cliente)
                except Clientes.DoesNotExist:
                    pass
            
            # ========== CRIAR IDENTIFICAÇÃO COMPLETA ==========
            identificacao, _ = NFe_Identificacao.objects.update_or_create(
                chave_acesso=chave_acesso,
                defaults={
                    'numero': numero,
                    'serie': serie,
                    'emissao': data_emissao or timezone.now(),
                    'saida_entrada': data_saida,
                    'tipo_documento': tipo_documento,
                    'tipo_operacao': tipo_operacao,
                    'codigo_municipio': self._get_text(ide, 'cMunFG'),
                    'municipio': self._get_text(ide, 'xMunFG'),
                    'uf': self._get_text(ide, 'UF'),
                    'finalidade_emissao': self._get_text(ide, 'finNFe', '1'),
                    'consumidor_final': self._get_text(ide, 'indFinal', '0'),
                    'presenca_comprador': self._get_text(ide, 'indPres', '0'),
                    'natureza_operacao': self._get_text(ide, 'natOp'),
                    'modelo': self._get_text(ide, 'mod', '55'),
                    'ambiente': self._get_text(ide, 'tpAmb', '2'),
                    'forma_emissao': tipo_documento,
                    'dv_chave': chave_acesso[-1] if chave_acesso else '0',
                    'data_atualizacao': timezone.now()
                }
            )
            
            # ========== CRIAR NFe PRINCIPAL ==========
            nfe, created = NFe.objects.update_or_create(
                identificacao=identificacao,
                defaults={
                    'emitente': emitente,
                    'destinatario': destinatario,
                    'empresa': empresa,
                    'cliente': cliente_eff,
                    'status': 'DRAFT',
                    'xml_assinado': xml_data.decode('utf-8', errors='ignore'),
                    'usuario_atualizacao': usuario,
                    'origem_dados': origem_dados,
                    'data_atualizacao': timezone.now()
                }
            )

            if created:
                nfe.usuario_criacao = usuario
                nfe.save(update_fields=['usuario_criacao'])
            
            # ========== PROCESSAR PRODUTOS E IMPOSTOS ==========
            self._processar_produtos(infNFe, identificacao)
            
            # ========== PROCESSAR TOTAIS ==========
            self._processar_total(infNFe, identificacao)
            
            # ========== PROCESSAR COBRANÇA E PARCELAS ==========
            self._processar_cobranca(infNFe, identificacao)

            # ========== PROCESSAR PAGAMENTO (pag/detPag) ==========
            self._processar_pagamento(infNFe, identificacao)

            # ========== PROCESSAR INFORMAÇÕES ADICIONAIS (infAdic) ==========
            self._processar_informacoes_adicionais(infNFe, identificacao)

            # ========== SALVAR CONDIÇÃO DE PAGAMENTO EM CondicaoParam (se ainda não existir) ==========
            _cod_cliente = cod_cliente or (empresa.cliente_id if empresa and getattr(empresa, 'cliente_id', None) else None)
            self._salvar_condicao_param_se_nao_existir(identificacao, cod_cliente=_cod_cliente)

            return []
        
        except EmpresaNaoCadastradaError:
            raise
        except Exception as e:
            print(str(e))
            raise Exception(f"Erro ao processar NFe: {str(e)}")

    def set_cte(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None):
        """
        Processa e insere CTe no banco de dados com extração completa de todos os campos
        """
        try:
            root = ET.fromstring(xml_data)
            infCte = root.find('.//cte:infCte', self.ns) or root.find('.//infCte')
            
            if infCte is None:
                raise ValueError("Estrutura de CTe inválida: infCte não encontrado")
            
            # Identificação
            ide = infCte.find('.//cte:ide', self.ns) or infCte.find('.//ide')
            numero = self._get_text(ide, 'nCT') or self._get_text(ide, 'nNF') or ''
            serie = self._get_text(ide, 'serie')
            chave = (infCte.get('Id') or '').replace('CTe', '')
            data_emissao = self._to_datetime(self._get_text(ide, 'dhEmi') or self._get_text(ide, 'dEmi'), '%Y-%m-%dT%H:%M:%S') or self._to_datetime(self._get_text(ide, 'dEmi'))

            # Emitente / Remetente
            rem = (infCte.find('.//cte:rem', self.ns) or infCte.find('.//rem') or
                   infCte.find('.//cte:emit', self.ns) or infCte.find('.//emit'))
            emitente_cnpj = self._get_text(rem, 'CNPJ') or self._get_text(rem, 'CPF') if rem is not None else None
            endereco_emit = self._processar_endereco(rem, is_emitente=True) if rem is not None else None
            emitente = None
            if emitente_cnpj:
                emitente, _ = CTe_Emitente.objects.update_or_create(
                    cnpj=emitente_cnpj,
                    defaults={
                        'razao_social': self._get_text(rem, 'xNome', 'S/N'),
                        'nome_fantasia': self._get_text(rem, 'xFant'),
                        'ie': self._get_text(rem, 'IE'),
                        'endereco': endereco_emit,
                        'data_atualizacao': timezone.now()
                    }
                )

            # Destinatario / Tomador
            dest = infCte.find('.//cte:dest', self.ns) or infCte.find('.//dest')
            destinatario = None
            destinatario_cnpj = None
            if dest is not None:
                destinatario_cnpj = self._get_text(dest, 'CNPJ') or self._get_text(dest, 'CPF')
                if destinatario_cnpj:
                    endereco_dest = self._processar_endereco(dest, is_emitente=False)
                    destinatario, _ = CTe_Destinatario.objects.update_or_create(
                        documento=destinatario_cnpj,
                        defaults={
                            'tipo': '1' if self._get_text(dest, 'CNPJ') else '2',
                            'razao_social': self._get_text(dest, 'xNome', 'S/N'),
                            'endereco': endereco_dest,
                            'data_atualizacao': timezone.now()
                        }
                    )

            # Encontrar empresa (tenta emitente primeiro, depois destinatario)
            empresa = None
            cnpj_para_busca = emitente_cnpj or destinatario_cnpj
            if cnpj_para_busca:
                try:
                    empresa = Empresas.objects.get(cnpj=cnpj_para_busca)
                    if cod_cliente and empresa.cliente and empresa.cliente.cod_cliente != cod_cliente:
                        empresa = None
                except Empresas.DoesNotExist:
                    empresa = None

            # Cliente: nunca vazio. Preferir empresa.cliente; se não encontrar, usar cod_cliente (cliente do usuário/parâmetro)
            cliente_eff = None
            if empresa and empresa.cliente:
                cliente_eff = empresa.cliente
            if not cliente_eff and cod_cliente:
                try:
                    cliente_eff = Clientes.objects.get(cod_cliente=cod_cliente)
                except Clientes.DoesNotExist:
                    pass

            # Criar/atualizar identificação
            identificacao, _ = CTe_Identificacao.objects.update_or_create(
                chave_acesso=chave or f"{numero}_{serie}",
                defaults={
                    'numero': numero,
                    'serie': serie,
                    'emissao': data_emissao or timezone.now(),
                    'modelo': self._get_text(ide, 'mod', '57'),
                    'data_atualizacao': timezone.now()
                }
            )

            # Criar CTe principal
            cte, created = CTe.objects.update_or_create(
                identificacao=identificacao,
                defaults={
                    'emitente': emitente,
                    'destinatario': destinatario,
                    'empresa': empresa,
                    'cliente': cliente_eff,
                    'data_atualizacao': timezone.now()
                }
            )

            # === EXTRAÇÃO DE CARGA ===
            infCarga = infCte.find('.//cte:infCarga', self.ns) or infCte.find('.//infCarga')
            if infCarga is not None:
                cte_carga, _ = CTe_Carga.objects.update_or_create(
                    cte_identificacao=identificacao,
                    defaults={
                        'natureza_carga': self._get_text(infCarga, 'xNaturez'),
                        'weight_total': self._to_decimal(self._get_text(infCarga, 'vPBrutoCarga')),
                        'weight_cubagem': self._to_decimal(self._get_text(infCarga, 'vMerc')),
                        'quantidade_volumes': int(self._get_text(infCarga, 'qVol', '0')) or 0,
                        'produto_perigoso': self._get_text(infCarga, 'xMatPer') != '',
                        'data_criacao': timezone.now()
                    }
                )

            # === EXTRAÇÃO DE SERVIÇO ===
            serv = infCte.find('.//cte:infServ', self.ns) or infCte.find('.//infServ')
            if serv is not None:
                cte_servico, _ = CTe_Servico.objects.update_or_create(
                    cte_identificacao=identificacao,
                    defaults={
                        'valor_padrao_servico': self._to_decimal(self._get_text(serv, 'vTPrest')),
                        'valor_vale_pedagio': self._to_decimal(self._get_text(serv, 'vVpd')),
                        'valor_gris': self._to_decimal(self._get_text(serv, 'vGRIS')),
                        'valor_seguro': self._to_decimal(self._get_text(serv, 'vValorCobrado')),
                        'taxa_adicional': self._to_decimal(self._get_text(serv, 'vOutrasDesp')),
                        'data_criacao': timezone.now()
                    }
                )

            # === EXTRAÇÃO DE VEÍCULO ===
            infModal = infCte.find('.//cte:infCteCarregamento', self.ns) or infCte.find('.//infCteCarregamento')
            if infModal is not None:
                veiculo = infModal.find('.//cte:veiculo', self.ns) or infModal.find('.//veiculo')
                if veiculo is not None:
                    cte_veiculo, _ = CTe_Veiculo.objects.update_or_create(
                        cte_identificacao=identificacao,
                        defaults={
                            'tipo_veiculo': self._get_text(veiculo, 'tpVeic'),
                            'placa': self._get_text(veiculo, 'placa'),
                            'uf_placa': self._get_text(veiculo, 'UF', 'SP'),
                            'tara': int(self._to_decimal(self._get_text(veiculo, 'tara', '0'))) or 0,
                            'capacidade_maxima': int(self._to_decimal(self._get_text(veiculo, 'capKg', '0'))) or 0,
                            'modelo': self._get_text(veiculo, 'modelo'),
                            'ano_fabricacao': int(self._get_text(veiculo, 'anoFab', '2000')) or 2000,
                            'eixos': int(self._get_text(veiculo, 'nEixos', '0')) or 0,
                            'combustivel': self._get_text(veiculo, 'tComb'),
                            'data_criacao': timezone.now()
                        }
                    )

            # === EXTRAÇÃO DE MOTORISTA ===
            mot = infModal.find('.//cte:mot', self.ns) or infModal.find('.//mot') if infModal is not None else None
            if mot is not None:
                cpf_mot = self._get_text(mot, 'CPF')
                if cpf_mot:
                    cte_motorista, _ = CTe_Motorista.objects.update_or_create(
                        cte_identificacao=identificacao,
                        defaults={
                            'cpf': cpf_mot,
                            'nome': self._get_text(mot, 'xNome'),
                            'cnh': self._get_text(mot, 'nCNH'),
                            'cnh_categoria': self._get_text(mot, 'cCNH'),
                            'cnh_validade': self._to_datetime(self._get_text(mot, 'dVencCNH')),
                            'banco': self._get_text(mot, 'banco'),
                            'agencia': self._get_text(mot, 'agencia'),
                            'conta': self._get_text(mot, 'conta'),
                            'data_criacao': timezone.now()
                        }
                    )

            # === EXTRAÇÃO DE PERCURSO ===
            peri = infCte.find('.//cte:perCurso', self.ns) or infCte.find('.//perCurso')
            if peri is not None:
                cte_percurso, _ = CTe_Percurso.objects.update_or_create(
                    cte_identificacao=identificacao,
                    defaults={
                        'municipio_origem': self._get_text(peri, 'xOrigem'),
                        'municipio_destino': self._get_text(peri, 'xDestino'),
                        'valor_pedagio_estimado': self._to_decimal(self._get_text(peri, 'vTpPed')),
                        'odometro_inicio': int(self._get_text(peri, 'odIni', '0')) or 0,
                        'odometro_fim': int(self._get_text(peri, 'odFim', '0')) or 0,
                        'data_criacao': timezone.now()
                    }
                )

            # === EXTRAÇÃO DE INFORMAÇÕES FISCAIS (ICMS, PIS, COFINS, IRRF) ===
            imp = infCte.find('.//cte:imp', self.ns) or infCte.find('.//imp')
            if imp is not None:
                icms_wrapper = imp.find('.//cte:ICMS', self.ns) or imp.find('.//ICMS')
                icms = _find_first_child(icms_wrapper, ['ICMS00', 'ICMS45', 'ICMS90', 'ICMS20', 'ICMS60', 'ICMS10', 'ICMS30'], self.ns) if icms_wrapper is not None else None
                icms = icms or icms_wrapper
                cte_fiscal, _ = CTe_Fiscal.objects.update_or_create(
                    cte_identificacao=identificacao,
                    defaults={
                        'cfop': self._get_text(icms, 'CFOP') if icms is not None else None,
                        'valor_base_icms': self._to_decimal(self._get_text(icms, 'vBC') if icms else None),
                        'aliquota_icms': self._to_decimal(self._get_text(icms, 'pICMS') if icms else None),
                        'valor_icms': self._to_decimal(self._get_text(icms, 'vICMS') if icms else None),
                        'valor_base_pis': self._to_decimal(self._get_text(imp, 'vBCPIS') or self._get_text(imp, 'vBC')),
                        'aliquota_pis': self._to_decimal(self._get_text(imp, 'pPIS')),
                        'valor_pis': self._to_decimal(self._get_text(imp, 'vPIS')),
                        'valor_base_cofins': self._to_decimal(self._get_text(imp, 'vBCCOFINS') or self._get_text(imp, 'vBC')),
                        'aliquota_cofins': self._to_decimal(self._get_text(imp, 'pCOFINS')),
                        'valor_cofins': self._to_decimal(self._get_text(imp, 'vCOFINS')),
                        'valor_irrf': self._to_decimal(self._get_text(imp, 'vIRRF')),
                        'cst_icms': self._get_text(icms, 'CST') if icms else None,
                        'data_criacao': timezone.now()
                    }
                )

            return cte

        except Exception as e:
            raise Exception(f"Erro ao processar CTe: {str(e)}")

    def set_nfse(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None):
        """
        Processa e insere NFSe no banco de dados com extração completa de RPS, retenções e pagamento.

        The structure of NFSe XML varies significantly between municipalities and
        providers.  We therefore perform namespace-agnostic searches for the key
        nodes by iterating over the tree and comparing local names.  This makes
        the parser much more tolerant of default namespaces and missing prefixes.
        """
        try:
            root = ET.fromstring(xml_data)

            def find_local(root, *names):
                for elem in root.iter():
                    tag = elem.tag.split('}')[-1]
                    if tag in names:
                        return elem
                return None

            inf = find_local(root, 'InfNfse', 'infNfse', 'InfRps', 'infRps', 'Rps', 'Nfse', 'NFSe')
            if inf is None:
                raise ValueError('Estrutura de NFSe inválida: nó de identificação não encontrado')

            numero = self._get_text(inf, 'Numero') or self._get_text(inf, 'numero') or ''
            emissao = self._to_datetime(self._get_text(inf, 'DataEmissao') or self._get_text(inf, 'dataEmissao')) or timezone.now()
            competencia = self._to_datetime(self._get_text(inf, 'Competencia') or self._get_text(inf, 'competencia'))
            chave = self._get_text(inf, 'Chave') or (numero or '')

            # PRESTADOR
            prest = find_local(inf, 'Prestador', 'PrestadorServico') or find_local(root, 'Prestador', 'PrestadorServico')
            prestador = None
            endereco_prest = None
            if prest is not None:
                prest_cnpj = self._get_text(prest, 'CNPJ') or self._get_text(prest, 'Cpf')
                # tentar endereço dentro do prestador
                end_p = find_local(prest, 'Endereco', 'EnderecoPrestador', 'enderPrestador') or prest
                if end_p is not None:
                    endereco_prest = NFSe_Endereco.objects.create(
                        logradouro=self._get_text(end_p, 'xLgr'),
                        numero=self._get_text(end_p, 'nro'),
                        complemento=self._get_text(end_p, 'xCpl'),
                        bairro=self._get_text(end_p, 'xBairro'),
                        codigo_municipio=self._get_text(end_p, 'cMun'),
                        nome_municipio=self._get_text(end_p, 'xMun'),
                        uf=self._get_text(end_p, 'UF'),
                        cep=self._get_text(end_p, 'CEP'),
                        pais=self._get_text(end_p, 'cPais', '1058'),
                        nome_pais=self._get_text(end_p, 'xPais', 'Brasil'),
                        telefone=self._get_text(end_p, 'fone'),
                        email=self._get_text(end_p, 'email'),
                        data_criacao=timezone.now()
                    )

                if prest_cnpj:
                    prestador, _ = NFSe_Prestador.objects.update_or_create(
                        cnpj=prest_cnpj,
                        defaults={
                            'razao_social': self._get_text(prest, 'xNome', self._get_text(prest, 'RazaoSocial', 'S/N')),
                            'nome_fantasia': self._get_text(prest, 'xFant'),
                            'ie': self._get_text(prest, 'IE'),
                            'endereco': endereco_prest,
                            'data_atualizacao': timezone.now()
                        }
                    )

            # TOMADOR
            tom = find_local(inf, 'Tomador', 'TomadorServico') or find_local(root, 'Tomador', 'TomadorServico')
            tomador = None
            if tom is not None:
                tom_doc = self._get_text(tom, 'CNPJ') or self._get_text(tom, 'CPF')
                tipo = '1' if self._get_text(tom, 'CNPJ') else '2'
                end_t = find_local(tom, 'Endereco', 'enderTomador') or tom
                endereco_tom = None
                if end_t is not None:
                    endereco_tom = NFSe_Endereco.objects.create(
                        logradouro=self._get_text(end_t, 'xLgr'),
                        numero=self._get_text(end_t, 'nro'),
                        complemento=self._get_text(end_t, 'xCpl'),
                        bairro=self._get_text(end_t, 'xBairro'),
                        codigo_municipio=self._get_text(end_t, 'cMun'),
                        nome_municipio=self._get_text(end_t, 'xMun'),
                        uf=self._get_text(end_t, 'UF'),
                        cep=self._get_text(end_t, 'CEP'),
                        pais=self._get_text(end_t, 'cPais', '1058'),
                        nome_pais=self._get_text(end_t, 'xPais', 'Brasil'),
                        telefone=self._get_text(end_t, 'fone'),
                        email=self._get_text(end_t, 'email'),
                        data_criacao=timezone.now()
                    )

                if tom_doc:
                    tomador, _ = NFSe_Tomador.objects.update_or_create(
                        documento=tom_doc,
                        defaults={
                            'tipo': tipo,
                            'razao_social': self._get_text(tom, 'xNome', self._get_text(tom, 'RazaoSocial', 'S/N')),
                            'endereco': endereco_tom,
                            'data_atualizacao': timezone.now()
                        }
                    )

            # Empresa: prestador (emissor) primeiro, depois tomador
            empresa = None
            cnpj_para_busca = None
            if prest is not None:
                cnpj_para_busca = self._get_text(prest, 'CNPJ') or self._get_text(prest, 'Cpf')
            if not cnpj_para_busca and tom is not None:
                cnpj_para_busca = self._get_text(tom, 'CNPJ') or self._get_text(tom, 'CPF')
            if cnpj_para_busca:
                try:
                    empresa = Empresas.objects.get(cnpj=cnpj_para_busca)
                    if cod_cliente and empresa.cliente and empresa.cliente.cod_cliente != cod_cliente:
                        empresa = None
                except Empresas.DoesNotExist:
                    empresa = None

            # Cliente: nunca vazio. Preferir empresa.cliente; se não encontrar, usar cod_cliente (cliente do usuário/parâmetro)
            cliente_eff = None
            if empresa and empresa.cliente:
                cliente_eff = empresa.cliente
            if not cliente_eff and cod_cliente:
                try:
                    cliente_eff = Clientes.objects.get(cod_cliente=cod_cliente)
                except Clientes.DoesNotExist:
                    pass

            # Identificacao
            identificacao, _ = NFSe_Identificacao.objects.update_or_create(
                chave=chave or f"{numero}",
                defaults={
                    'numero': numero or '0',
                    'emissao': emissao,
                    'competencia': competencia,
                    'codigo_prefeitura': self._get_text(inf, 'CodigoMunicipio') or self._get_text(inf, 'codigoMunicipio'),
                    'data_atualizacao': timezone.now()
                }
            )

            # Criar NFSe principal
            nfse, created = NFSe.objects.update_or_create(
                identificacao=identificacao,
                defaults={
                    'prestador': prestador,
                    'tomador': tomador,
                    'empresa': empresa,
                    'cliente': cliente_eff,
                    'data_atualizacao': timezone.now()
                }
            )

            # === EXTRAÇÃO DE RPS ===
            rps_node = find_local(inf, 'Rps', 'RPS')
            if rps_node is not None:
                numero_rps = self._get_text(rps_node, 'Numero') or self._get_text(rps_node, 'numero')
                serie_rps = self._get_text(rps_node, 'Serie') or self._get_text(rps_node, 'serie') or 'RPS'
                tipo_rps = self._get_text(rps_node, 'Tipo') or 'RPS'
                data_rps = self._to_datetime(self._get_text(rps_node, 'DataEmissao') or self._get_text(rps_node, 'dataEmissao'))
                status_rps = self._get_text(rps_node, 'Status') or 'NORMAL'
                
                if numero_rps:
                    NFSe_RPS.objects.update_or_create(
                        numero_rps=numero_rps,
                        serie_rps=serie_rps,
                        nfse_identificacao=identificacao,
                        defaults={
                            'tipo_rps': tipo_rps,
                            'data_emissao_rps': data_rps or timezone.now().date(),
                            'status_rps': status_rps,
                            'numero_nfse_gerada': numero,
                            'valor_rps': self._to_decimal(self._get_text(rps_node, 'Valor') or self._get_text(inf, 'ValorServicos')),
                            'data_criacao': timezone.now()
                        }
                    )

            # === EXTRAÇÃO DE RETENÇÕES (nível cabeçalho) ===
            def _get_retencao(no, *nomes):
                for n in nomes:
                    v = self._get_text(no, n) if no else ''
                    if v:
                        return self._to_decimal(v)
                return Decimal('0')
            valor_ir = _get_retencao(inf, 'ValorIRRetido', 'ValorRetidoIR', 'valor_ir_retido')
            valor_issqn = _get_retencao(inf, 'ValorISSRetido', 'ValorRetidoISS', 'valor_issqn_retido')
            valor_inss = _get_retencao(inf, 'ValorINSSRetido', 'ValorRetidoINSS', 'valor_inss_retido')
            valor_cofins = _get_retencao(inf, 'ValorCOFINSRetido', 'ValorRetidoCOFINS', 'valor_cofins_retido')
            valor_pis = _get_retencao(inf, 'ValorPISRetido', 'ValorRetidoPIS', 'valor_pis_retido')
            valor_csll = _get_retencao(inf, 'ValorCSLLRetido', 'ValorRetidoCSLL', 'valor_csll_retido')
            retencao_parent = find_local(inf, 'Retencoes', 'RetencaoDados', 'Deducoes', 'ImpostosRetidos')
            if retencao_parent is not None:
                for ded in list(retencao_parent):
                    desc = (self._get_text(ded, 'DescricaoDeducao') or self._get_text(ded, 'Tipo') or ded.tag.split('}')[-1] or '').upper()
                    val = self._to_decimal(self._get_text(ded, 'ValorDeducao') or self._get_text(ded, 'Valor') or self._get_text(ded, 'ValorRetido'))
                    if 'IR' in desc:
                        valor_ir += val
                    elif 'ISS' in desc:
                        valor_issqn += val
                    elif 'INSS' in desc:
                        valor_inss += val
                    elif 'COFINS' in desc:
                        valor_cofins += val
                    elif 'PIS' in desc:
                        valor_pis += val
                    elif 'CSLL' in desc:
                        valor_csll += val
            total_ret = valor_ir + valor_issqn + valor_inss + valor_cofins + valor_pis + valor_csll
            if total_ret or valor_ir or valor_issqn or valor_inss or valor_cofins or valor_pis or valor_csll:
                NFSe_Retencao.objects.update_or_create(
                    nfse_identificacao=identificacao,
                    defaults={
                        'valor_ir': valor_ir,
                        'valor_issqn': valor_issqn,
                        'valor_inss': valor_inss,
                        'valor_cofins': valor_cofins,
                        'valor_pis': valor_pis,
                        'valor_csll': valor_csll,
                        'valor_total_retencoes': total_ret,
                        'data_criacao': timezone.now()
                    }
                )

            # === EXTRAÇÃO DE PAGAMENTO ===
            pag_node = find_local(inf, 'Pagamento', 'DadosFormaPagamento')
            if pag_node is not None:
                forma = self._get_text(pag_node, 'Forma') or self._get_text(pag_node, 'forma') or 'DINHEIRO'
                NFSe_Pagamento.objects.update_or_create(
                    nfse_identificacao=identificacao,
                    defaults={
                        'forma_pagamento': forma,
                        'descricao_forma_pagamento': self._get_text(pag_node, 'Descricao'),
                        'banco': self._get_text(pag_node, 'Banco'),
                        'agencia': self._get_text(pag_node, 'Agencia'),
                        'conta': self._get_text(pag_node, 'Conta'),
                        'valor_total_pagamento': self._to_decimal(self._get_text(inf, 'ValorLiquido') or self._get_text(inf, 'valorLiquido')),
                        'data_pagamento': self._to_datetime(self._get_text(pag_node, 'DataPagamento')),
                        'condicao_pagamento': 'VISTA' if self._get_text(pag_node, 'Parcelas') == '1' else 'PARCELADO',
                        'num_parcelas': int(self._get_text(pag_node, 'Parcelas', '1')),
                        'data_criacao': timezone.now()
                    }
                )

            # === EXTRAÇÃO DE CREDENCIAMENTO ===
            codigo_municipio = self._get_text(inf, 'CodigoMunicipio') or '0000000'
            if codigo_municipio != '0000000':
                NFSe_Credenciamento.objects.update_or_create(
                    nfse_identificacao=identificacao,
                    defaults={
                        'inscricao_municipal': self._get_text(inf, 'InscricaoMunicipal') or '',
                        'optante_simples_nacional': self._get_text(inf, 'OptanteSimplesNacional') == 'S' if self._get_text(inf, 'OptanteSimplesNacional') else False,
                        'codigo_municipio': codigo_municipio,
                        'nome_municipio': self._get_text(inf, 'CodigoMunicipio') or 'Sem informação',
                        'uf': self._get_text(inf, 'UF') or '',
                        'ambiente_emissao': 'PRODUCAO' if self._get_text(inf, 'Ambiente') != 'H' else 'HOMOLOGACAO',
                        'data_criacao': timezone.now()
                    }
                )

            # Serviços - tentar localizar lista de servicos
            serv_nodes = []
            for s in inf.iter():
                if s.tag.split('}')[-1] in ('Servico', 'ItensServico', 'DetalhamentoServico'):
                    serv_nodes.append(s)

            # Apagar serviços existentes para evitar duplicatas
            NFSe_Servico.objects.filter(nfse_identificacao=identificacao).delete()

            for s in serv_nodes:
                descricao = self._get_text(s, 'Discriminacao') or self._get_text(s, 'Descricao') or self._get_text(s, 'discriminacao')
                quantidade = self._to_decimal(self._get_text(s, 'Quantidade') or self._get_text(s, 'quantidade') or '1')
                valor_unit = self._to_decimal(self._get_text(s, 'ValorUnitario') or self._get_text(s, 'valorUnitario') or self._get_text(s, 'valor'))
                valor_total = self._to_decimal(self._get_text(s, 'ValorTotal') or self._get_text(s, 'valorTotal') or self._get_text(s, 'valorServico') or self._get_text(s, 'ValorServicos'))

                if descricao and valor_total:
                    NFSe_Servico.objects.create(
                        descricao=descricao,
                        quantidade=quantidade,
                        valor_unitario=valor_unit,
                        valor_total=valor_total,
                        nfse_identificacao=identificacao,
                        codigo_servico=self._get_text(s, 'CodigoServicoMunicipal') or self._get_text(s, 'CodigoServico'),
                        aliquota_issqn=self._to_decimal(self._get_text(s, 'AliquotaIssqn') or self._get_text(s, 'AliquotaISS') or self._get_text(s, 'Aliquota')),
                        valor_issqn=self._to_decimal(self._get_text(s, 'ValorISSQN') or self._get_text(s, 'ValorISS') or self._get_text(s, 'ValorLiquidoNfse')),
                        municipio_incidencia=self._get_text(s, 'CodigoMunicipio') or self._get_text(s, 'MunicipioIncidencia'),
                        valor_ir_retido=self._to_decimal(self._get_text(s, 'ValorIRRetido') or self._get_text(s, 'ValorRetidoIR') or self._get_text(s, 'valor_ir_retido')),
                        valor_issqn_retido=self._to_decimal(self._get_text(s, 'ValorISSRetido') or self._get_text(s, 'ValorRetidoISS') or self._get_text(s, 'valor_issqn_retido')),
                        valor_inss_retido=self._to_decimal(self._get_text(s, 'ValorINSSRetido') or self._get_text(s, 'ValorRetidoINSS') or self._get_text(s, 'valor_inss_retido')),
                        valor_cofins_retido=self._to_decimal(self._get_text(s, 'ValorCOFINSRetido') or self._get_text(s, 'ValorRetidoCOFINS') or self._get_text(s, 'valor_cofins_retido')),
                        valor_pis_retido=self._to_decimal(self._get_text(s, 'ValorPISRetido') or self._get_text(s, 'ValorRetidoPIS') or self._get_text(s, 'valor_pis_retido')),
                        valor_csll_retido=self._to_decimal(self._get_text(s, 'ValorCSLLRetido') or self._get_text(s, 'ValorRetidoCSLL') or self._get_text(s, 'valor_csll_retido')),
                        data_criacao=timezone.now()
                    )

            return nfse

        except Exception as e:
            raise Exception(f"Erro ao processar NFSe: {str(e)}")    