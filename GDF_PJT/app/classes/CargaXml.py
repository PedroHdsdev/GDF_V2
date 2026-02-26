
from django.db.models               import Prefetch
from psycopg2                       import IntegrityError
from django.contrib.auth.models     import User, Group
from app.db_GDF.Public.models       import Clientes, Empresas
from app.db_GDF.NFe.models          import (
    NFe, NFe_Total, NFe_Produto, NFe_Identificacao, NFe_Emitente, NFe_Destinatario,
    NFe_Endereco, NFe_ICMS, NFe_IPI, NFe_PIS, NFe_COFINS, NFe_Transporte,
    NFe_Cobranca, NFe_Parcela, NFe_Pagamento, NFe_Informacoes_Adicionais
)
from typing                        import List, Dict
from datetime import datetime, time
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
import xml.etree.ElementTree as ET

class Carga_xml():
    def __init__(self):
        self.ns = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'cte': 'http://www.portalfiscal.inf.br/cte',
            'nfse': 'http://www.abrasf.org.br/nfse'
        }
    
    def _get_text(self, element, path, default=''):
        """Extrai texto de elemento XML com fallback para namespace"""
        if element is None:
            return default
        result = element.findtext(f'.//nfe:{path}', default='', namespaces=self.ns)
        if not result:
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
        """Processa todos os impostos de um produto"""
        # ICMS
        icms_node = imposto_node.find('.//nfe:ICMS', self.ns) or imposto_node.find('.//ICMS')
        if icms_node:
            # ICMS pode ter vários tipos (ICMS00, ICMS10, ICMS20, etc)
            icms_tipo = None
            for child in icms_node:
                if 'ICMS' in child.tag:
                    icms_tipo = child
                    break
            
            if icms_tipo is not None:
                NFe_ICMS.objects.create(
                    produto=produto,
                    origem=self._get_text(icms_tipo, 'orig', '0'),
                    cst=self._get_text(icms_tipo, 'CST') or self._get_text(icms_tipo, 'CSOSN', '00'),
                    valor_base_calculo=self._to_decimal(self._get_text(icms_tipo, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(icms_tipo, 'pICMS')),
                    valor_icms=self._to_decimal(self._get_text(icms_tipo, 'vICMS'))
                )
        
        # IPI
        ipi_node = imposto_node.find('.//nfe:IPI', self.ns) or imposto_node.find('.//IPI')
        if ipi_node:
            ipi_trib = ipi_node.find('.//nfe:IPITrib', self.ns) or ipi_node.find('.//IPITrib')
            if ipi_trib is not None:
                NFe_IPI.objects.create(
                    produto=produto,
                    cst=self._get_text(ipi_trib, 'CST', '99'),
                    valor_base_calculo=self._to_decimal(self._get_text(ipi_trib, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(ipi_trib, 'pIPI')),
                    valor_ipi=self._to_decimal(self._get_text(ipi_trib, 'vIPI'))
                )
        
        # PIS
        pis_node = imposto_node.find('.//nfe:PIS', self.ns) or imposto_node.find('.//PIS')
        if pis_node:
            pis_aliq = pis_node.find('.//nfe:PISAliq', self.ns) or pis_node.find('.//PISAliq')
            if pis_aliq is not None:
                NFe_PIS.objects.create(
                    produto=produto,
                    cst=self._get_text(pis_aliq, 'CST', '99'),
                    valor_base_calculo=self._to_decimal(self._get_text(pis_aliq, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(pis_aliq, 'pPIS')),
                    valor_pis=self._to_decimal(self._get_text(pis_aliq, 'vPIS'))
                )
        
        # COFINS
        cofins_node = imposto_node.find('.//nfe:COFINS', self.ns) or imposto_node.find('.//COFINS')
        if cofins_node:
            cofins_aliq = cofins_node.find('.//nfe:COFINSAliq', self.ns) or cofins_node.find('.//COFINSAliq')
            if cofins_aliq is not None:
                NFe_COFINS.objects.create(
                    produto=produto,
                    cst=self._get_text(cofins_aliq, 'CST', '99'),
                    valor_base_calculo=self._to_decimal(self._get_text(cofins_aliq, 'vBC')),
                    aliquota=self._to_decimal(self._get_text(cofins_aliq, 'pCOFINS')),
                    valor_cofins=self._to_decimal(self._get_text(cofins_aliq, 'vCOFINS'))
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
            'errors': []
        }

        for xml_file in I_LsXml:
            try:
                xml_data = xml_file.read()

                if i_type == 'NFe':
                    self.set_nfe(xml_data, I_origem_dados, i_usuario, i_cod_cliente)
                
                elif i_type == 'CTe':
                    self.set_cte(xml_data, I_origem_dados, i_usuario, i_cod_cliente)
                
                elif i_type == 'NFSe':
                    self.set_nfse(xml_data, I_origem_dados, i_usuario, i_cod_cliente)

                result['success'].append(xml_file.name)
            
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
            tipo_operacao = self._get_text(ide, 'tpNF', '1')
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
                except Empresas.DoesNotExist:
                    raise ValueError(
                        f"Empresa não encontrada. NFe {tipo_nfe}: CNPJ {cnpj_para_busca} não cadastrado."
                    )
                if cod_cliente and empresa.cliente and empresa.cliente.cod_cliente != cod_cliente:
                    raise ValueError(f"Empresa {empresa.cnpj} não pertence ao cliente {cod_cliente}")
            else:
                raise ValueError(f"Não foi possível identificar CNPJ da empresa (tipo: {tipo_nfe})")
            
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
            
            return nfe
        
        except Exception as e:
            print(str(e))
            raise Exception(f"Erro ao processar NFe: {str(e)}")

    def set_cte(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None):
        """
        Processa e insere CTe no banco de dados
        (atualmente apenas valida a estrutura; adiciona parâmetro cliente para futuro uso)
        """
        try:
            root = ET.fromstring(xml_data)
            infCte = root.find('.//cte:infCte', self.ns) or root.find('.//infCte')
            
            if infCte is None:
                raise ValueError("Estrutura de CTe inválida: infCte não encontrado")
            
            # registro reduzido
            return True
        
        except Exception as e:
            raise Exception(f"Erro ao processar CTe: {str(e)}")

    def set_nfse(self, xml_data: bytes, origem_dados: str, usuario: str, cod_cliente: str = None):
        """
        Processa e insere NFSe no banco de dados
        (placeholder; cliente adicionado para coerência)
        """
        try:
            root = ET.fromstring(xml_data)
            # TODO: tratamento real
            return True
        
        except Exception as e:
            raise Exception(f"Erro ao processar NFSe: {str(e)}")    