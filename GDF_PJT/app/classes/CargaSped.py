"""
Carga de arquivos SPED (EFD ICMS/IPI, EFD Contribuições, etc.).
Persiste em Sped_Arquivo e grava cada tipo de registro na sua tabela com seus campos.
Validações para evitar carga duplicada: mesmo nome+empresa+competência, mesmo hash, mesmo 0000.
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from django.utils import timezone


def _decode_sped_text(conteudo: bytes) -> str:
    """
    Decodifica o conteúdo do arquivo SPED. Arquivos brasileiros costumam vir em
    Latin-1/CP1252; se UTF-8 produzir caracteres de substituição (�), usa Latin-1.
    """
    try:
        texto = conteudo.decode('utf-8', errors='replace')
        if '\ufffd' in texto:
            texto = conteudo.decode('latin-1', errors='replace')
    except Exception:
        texto = conteudo.decode('latin-1', errors='replace')
    return texto


def _detectar_tipo_sped_pelo_conteudo(texto: str) -> Optional[str]:
    """
    Detecta o tipo do SPED pelo conteúdo do arquivo (registro 0000, cod_ver).
    EFD Contribuições: cod_ver 006 a 016 → 'C'
    EFD ICMS/IPI (Fiscal): cod_ver 017 em diante → 'F'
    Retorna 'F', 'C' ou None se não conseguir identificar.
    """
    for linha in texto.splitlines()[:500]:
        if '|' not in linha or '|0000|' not in linha:
            continue
        partes = [p.strip() for p in linha.split('|') if p.strip()]
        if not partes or (partes[0] or '').strip() != '0000':
            continue
        cod_ver = (partes[1] if len(partes) > 1 else '').strip()
        if not cod_ver or not cod_ver.isdigit():
            return None
        try:
            v = int(cod_ver)
            if v >= 17:
                return 'F'  # EFD ICMS/IPI
            if 6 <= v <= 16:
                return 'C'  # EFD Contribuições
        except ValueError:
            pass
        return None
    return None


class Carga_sped:
    """Processador de carga de arquivos SPED. Estrutura alinhada à Carga XML."""

    EXTENSOES_SPED = ('.txt',)

    def __init__(self):
        pass

    def _p(self, partes: List[str], i: int, default: str = '') -> str:
        """Retorna parte[i] ou default."""
        return (partes[i] if i < len(partes) else default).strip() or default

    def _p_dec(self, partes: List[str], i: int):
        """Retorna parte[i] como Decimal ou None."""
        try:
            s = self._p(partes, i)
            return Decimal(s) if s else None
        except Exception:
            return None

    def _p_date(self, partes: List[str], i: int):
        """Retorna parte[i] como date (DDMMAAAA ou AAAAMMDD) ou None."""
        from datetime import datetime
        s = self._p(partes, i)
        if not s or len(s) != 8 or not s.isdigit():
            return None
        try:
            # SPED usa DDMMAAAA
            return datetime.strptime(s, '%d%m%Y').date()
        except ValueError:
            try:
                return datetime.strptime(s, '%Y%m%d').date()
            except ValueError:
                pass
        return None

    def _gravar_linha(self, arq, partes: List[str], num: int, last_c100_ref) -> Optional[Any]:
        """Grava uma linha do SPED na tabela correspondente ao registro. Se não houver tabela própria, salva em Sped_Registro. Retorna último C100 se for o caso."""
        from app.db_GDF.Sped.models import (
            Sped_Arquivo,
            Sped_Reg_0000, Sped_Reg_0001, Sped_Reg_0005, Sped_Reg_0150, Sped_Reg_0190, Sped_Reg_0200,
            Sped_Reg_C001, Sped_Reg_C100, Sped_Reg_C170, Sped_Reg_C190, Sped_Reg_D100,
            Sped_Registro,
        )
        if not partes:
            return last_c100_ref
        reg = (partes[0] or '').strip().upper()
        if reg == '0000':
            cnpj_raw = (self._p(partes, 6) or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
            Sped_Reg_0000.objects.create(
                arquivo=arq,
                linha=num,
                cod_ver=self._p(partes, 1)[:3],
                cod_fin=self._p(partes, 2)[:1],
                dt_ini=self._p_date(partes, 3),
                dt_fin=self._p_date(partes, 4),
                nome=self._p(partes, 5)[:100],
                cnpj=cnpj_raw or None,
                cpf=self._p(partes, 7)[:11],
                uf=self._p(partes, 8)[:2],
                ie=self._p(partes, 9)[:14],
                cod_mun=self._p(partes, 10)[:7],
                im=self._p(partes, 11)[:15],
                suframa=self._p(partes, 12)[:9],
                ind_perfil=self._p(partes, 13)[:1],
                ind_ativ=self._p(partes, 14)[:1],
            )
        elif reg == '0001':
            Sped_Reg_0001.objects.create(
                arquivo=arq,
                linha=num,
                ind_mov=self._p(partes, 1)[:1],
            )
        elif reg == '0005':
            Sped_Reg_0005.objects.create(
                arquivo=arq,
                linha=num,
                fantasia=self._p(partes, 1)[:60],
                cep=self._p(partes, 2)[:8],
                end=self._p(partes, 3)[:60],
                num=self._p(partes, 4)[:10],
                compl=self._p(partes, 5)[:60],
                bairro=self._p(partes, 6)[:60],
                fone=self._p(partes, 7)[:11],
                fax=self._p(partes, 8)[:11],
                email=self._p(partes, 9)[:60],
            )
        elif reg == '0150':
            Sped_Reg_0150.objects.create(
                arquivo=arq,
                linha=num,
                cod_part=self._p(partes, 1)[:60],
                nome=self._p(partes, 2)[:100],
                cod_pais=self._p(partes, 3)[:3],
                cnpj=self._p(partes, 4)[:14],
                cpf=self._p(partes, 5)[:11],
                ie=self._p(partes, 6)[:14],
                cod_mun=self._p(partes, 7)[:7],
                end=self._p(partes, 8)[:60],
                num=self._p(partes, 9)[:10],
                compl=self._p(partes, 10)[:60],
                bairro=self._p(partes, 11)[:60],
            )
        elif reg == '0190':
            Sped_Reg_0190.objects.create(
                arquivo=arq,
                linha=num,
                unid=self._p(partes, 1)[:6],
                descr=self._p(partes, 2)[:255],
            )
        elif reg == '0200':
            Sped_Reg_0200.objects.create(
                arquivo=arq,
                linha=num,
                cod_item=self._p(partes, 1)[:60],
                descr_item=self._p(partes, 2)[:255],
                cod_barra=self._p(partes, 3)[:14],
                cod_ant_item=self._p(partes, 4)[:60],
                unid_inv=self._p(partes, 5)[:6],
                tipo_item=self._p(partes, 6)[:2],
                cod_ncm=self._p(partes, 7)[:8],
                ex_ipi=self._p(partes, 8)[:3],
                cod_gen=self._p(partes, 9)[:2],
                cod_lst=self._p(partes, 10)[:5],
                aliq_icms=self._p_dec(partes, 11),
            )
        elif reg == 'C001':
            Sped_Reg_C001.objects.create(
                arquivo=arq,
                linha=num,
                ind_mov=self._p(partes, 1)[:1],
            )
        elif reg == 'C100':
            c100 = Sped_Reg_C100.objects.create(
                arquivo=arq,
                linha=num,
                ind_oper=self._p(partes, 1)[:1],
                ind_emit=self._p(partes, 2)[:1],
                cod_part=self._p(partes, 3)[:60],
                cod_mod=self._p(partes, 4)[:2],
                cod_sit=self._p(partes, 5)[:2],
                ser=self._p(partes, 6)[:3],
                num_doc=self._p(partes, 7)[:9],
                chv_nfe=self._p(partes, 8)[:44],
                dt_doc=self._p_date(partes, 9),
                dt_e_s=self._p_date(partes, 10),
                vl_doc=self._p_dec(partes, 11),
                ind_frt=self._p(partes, 12)[:1],
                vl_frt=self._p_dec(partes, 13),
                vl_seg=self._p_dec(partes, 14),
                vl_out_da=self._p_dec(partes, 15),
                vl_bc_icms=self._p_dec(partes, 16),
                vl_icms=self._p_dec(partes, 17),
                vl_bc_icms_st=self._p_dec(partes, 18),
                vl_icms_st=self._p_dec(partes, 19),
                vl_ipi=self._p_dec(partes, 20),
                vl_pis=self._p_dec(partes, 21),
                vl_cofins=self._p_dec(partes, 22),
                vl_pis_st=self._p_dec(partes, 23),
                vl_cofins_st=self._p_dec(partes, 24),
            )
            return c100
        elif reg == 'C170':
            c170 = Sped_Reg_C170.objects.create(
                arquivo=arq,
                c100=last_c100_ref,
                linha=num,
                num_item=self._p(partes, 1)[:3],
                cod_item=self._p(partes, 2)[:60],
                descr_compl=self._p(partes, 3)[:255],
                qtd=self._p_dec(partes, 4),
                unid=self._p(partes, 5)[:6],
                vl_item=self._p_dec(partes, 6),
                vl_desc=self._p_dec(partes, 7),
                ind_mov=self._p(partes, 8)[:1],
                cst_icms=self._p(partes, 9)[:3],
                cfop=self._p(partes, 10)[:4],
                cod_nat=self._p(partes, 11)[:10],
                vl_bc_icms=self._p_dec(partes, 12),
                aliq_icms=self._p_dec(partes, 13),
                vl_icms=self._p_dec(partes, 14),
                vl_bc_icms_st=self._p_dec(partes, 15),
                aliq_st=self._p_dec(partes, 16),
                vl_icms_st=self._p_dec(partes, 17),
                cst_pis=self._p(partes, 22)[:2],
                vl_bc_pis=self._p_dec(partes, 23),
                aliq_pis=self._p_dec(partes, 24),
                vl_pis=self._p_dec(partes, 25),
                cst_cofins=self._p(partes, 26)[:2],
                vl_bc_cofins=self._p_dec(partes, 27),
                aliq_cofins=self._p_dec(partes, 28),
                vl_cofins=self._p_dec(partes, 29),
            )
        elif reg == 'C190':
            Sped_Reg_C190.objects.create(
                arquivo=arq,
                c100=last_c100_ref,
                linha=num,
                cst_icms=self._p(partes, 1)[:3],
                cfop=self._p(partes, 2)[:4],
                aliq_icms=self._p_dec(partes, 3),
                vl_opr=self._p_dec(partes, 4),
                vl_bc_icms=self._p_dec(partes, 5),
                vl_icms=self._p_dec(partes, 6),
                vl_bc_icms_st=self._p_dec(partes, 7),
                vl_icms_st=self._p_dec(partes, 8),
                vl_red_bc=self._p_dec(partes, 9),
                vl_ipi=self._p_dec(partes, 10),
                cod_obs=self._p(partes, 11)[:6],
            )
        elif reg == 'D100':
            Sped_Reg_D100.objects.create(
                arquivo=arq,
                linha=num,
                ind_oper=self._p(partes, 1)[:1],
                ind_emit=self._p(partes, 2)[:1],
                cod_part=self._p(partes, 3)[:60],
                cod_mod=self._p(partes, 4)[:2],
                cod_sit=self._p(partes, 5)[:2],
                ser=self._p(partes, 6)[:3],
                sub_ser=self._p(partes, 7)[:3],
                num_doc=self._p(partes, 8)[:9],
                chv_cte=self._p(partes, 9)[:44],
                dt_doc=self._p_date(partes, 10),
                dt_a_p=self._p_date(partes, 11),
                tp_ct_e=self._p(partes, 12)[:1],
                chv_cte_ref=self._p(partes, 13)[:44],
                vl_doc=self._p_dec(partes, 14),
                vl_desc=self._p_dec(partes, 15),
                ind_frt=self._p(partes, 16)[:1],
                vl_frt=self._p_dec(partes, 17),
                vl_seg=self._p_dec(partes, 18),
                vl_out_da=self._p_dec(partes, 19),
                vl_bc_icms=self._p_dec(partes, 20),
                vl_icms=self._p_dec(partes, 21),
                vl_nf=self._p_dec(partes, 22),
                cod_inf=self._p(partes, 23)[:6],
            )
        else:
            campos = {str(i): (partes[i] if i < len(partes) else '') for i in range(1, len(partes))}
            Sped_Registro.objects.create(
                arquivo=arq,
                registro=reg[:20],
                linha=num,
                campos=campos,
                conteudo='|'.join(partes)[:8000],
            )
        return last_c100_ref

    def set_upload_sped(
        self,
        arquivos: List,
        usuario: str,
        cod_cliente: str,
        empresa=None,
    ) -> Dict:
        """
        Recebe arquivos SPED enviados (File objects).
        Detecta o tipo automaticamente pelo conteúdo. Grava em Sped_Arquivo e cada registro
        na sua tabela específica (quando existir) ou em Sped_Registro.
        """
        from app.db_GDF.Sped.models import Sped_Arquivo

        success = []
        errors = []

        for f in arquivos:
            if not getattr(f, 'name', None):
                errors.append({'file': '(sem nome)', 'error': 'Arquivo sem nome'})
                continue
            nome = f.name
            if not any(nome.lower().endswith(ext) for ext in self.EXTENSOES_SPED):
                errors.append({'file': nome, 'error': 'Arquivo deve ser .txt (SPED)'})
                continue
            if getattr(f, 'size', 0) > 10 * 1024 * 1024 * 1024:
                errors.append({'file': nome, 'error': 'Arquivo muito grande (máx 10GB)'})
                continue
            try:
                conteudo = b''
                if hasattr(f, 'read'):
                    conteudo = f.read()
                    if hasattr(f, 'seek'):
                        f.seek(0)
                texto = _decode_sped_text(conteudo)
                tipo_char = _detectar_tipo_sped_pelo_conteudo(texto) or 'F'
                competencia = self._extrair_competencia(texto)
                empresa_eff = empresa
                if empresa_eff is None and cod_cliente:
                    _, _, cnpj_0000 = self._extrair_0000_assinatura(texto)
                    empresa_eff = self._resolver_empresa_por_cnpj(cod_cliente, cnpj_0000)
                ok_dup, msg_dup = self._validar_duplicata_sped(
                    conteudo, texto, nome, tipo_char, empresa_eff, competencia,
                )
                if not ok_dup:
                    errors.append({'file': nome, 'error': msg_dup})
                    continue
                hash_conteudo = hashlib.sha256(conteudo).hexdigest()
                arq = Sped_Arquivo.objects.create(
                    tipo=tipo_char,
                    empresa=empresa_eff,
                    competencia=competencia,
                    nome_arquivo=nome,
                    hash_conteudo=hash_conteudo,
                    data_carga=timezone.localtime(),
                )
                linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
                last_c100 = None
                for num, ln in enumerate(linhas, start=1):
                    if not ln.startswith('|'):
                        continue
                    partes = [p.strip() for p in ln.split('|') if p.strip()]
                    if not partes:
                        continue
                    last_c100 = self._gravar_linha(arq, partes, num, last_c100)
                success.append(nome)
            except Exception as e:
                errors.append({'file': nome, 'error': str(e)})
        return {
            'success': success,
            'errors': errors,
            'pendentes': [],
        }

    def _extrair_competencia(self, texto: str):
        """Tenta extrair competência (primeiro dia do mês) do conteúdo SPED. Retorna None se não achar."""
        from datetime import datetime
        # Ex.: |0001|001|01012024|... ou linha com período
        for linha in texto.splitlines()[:200]:
            if '|' not in linha:
                continue
            partes = linha.split('|')
            for p in partes:
                p = (p or '').strip()
                if len(p) == 8 and p.isdigit():
                    try:
                        return datetime.strptime(p, '%d%m%Y').date()
                    except ValueError:
                        pass
                if len(p) == 6 and p.isdigit():
                    try:
                        return datetime.strptime(p + '01', '%Y%m%d').date()
                    except ValueError:
                        pass
        return None

    def _extrair_0000_assinatura(self, texto: str) -> Tuple[Optional[Any], Optional[Any], Optional[str]]:
        """Extrai dt_ini, dt_fin e cnpj da primeira linha |0000| do conteúdo. Retorna (dt_ini, dt_fin, cnpj)."""
        from datetime import datetime
        for linha in texto.splitlines()[:500]:
            if '|' not in linha or '|0000|' not in linha:
                continue
            partes = [p.strip() for p in linha.split('|') if p.strip()]
            if not partes or (partes[0] or '').strip() != '0000':
                continue
            # 0000: cod_ver(1), cod_fin(2), dt_ini(3), dt_fin(4), nome(5), cnpj(6), cpf(7), ...
            dt_ini = self._p_date(partes, 3) if len(partes) > 3 else None
            dt_fin = self._p_date(partes, 4) if len(partes) > 4 else None
            cnpj = (self._p(partes, 6) or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14] or None
            return (dt_ini, dt_fin, cnpj)
        return (None, None, None)

    def _resolver_empresa_por_cnpj(self, cod_cliente: str, cnpj: Optional[str]):
        """Busca Empresas do cliente pelo CNPJ (14 dígitos). Retorna a empresa ou None."""
        if not cod_cliente or not cnpj or len(cnpj) < 14:
            return None
        cnpj_14 = (cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
        if len(cnpj_14) < 14:
            return None
        try:
            from app.db_GDF.Public.models import Empresas
            return Empresas.objects.filter(cliente__cod_cliente=cod_cliente, cnpj=cnpj_14).first()
        except Exception:
            return None

    def _validar_duplicata_sped(
        self,
        conteudo: bytes,
        texto: str,
        nome: str,
        tipo_char: str,
        empresa,
        competencia,
    ) -> Tuple[bool, str]:
        """
        Valida se o arquivo SPED já foi carregado (evitar duplicatas).
        Retorna (True, '') se pode carregar; (False, mensagem) se for duplicata.
        Validações: 1) mesmo nome + empresa + competência; 2) mesmo hash do conteúdo; 3) mesmo 0000 (dt_ini, dt_fin, cnpj).
        """
        from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Reg_0000

        # 1) Mesmo nome, empresa, competência e tipo
        q = Sped_Arquivo.objects.filter(tipo=tipo_char, nome_arquivo=nome)
        if empresa is not None:
            q = q.filter(empresa=empresa)
        if competencia is not None:
            q = q.filter(competencia=competencia)
        else:
            q = q.filter(competencia__isnull=True)
        if q.exists():
            return (False, 'Arquivo SPED já foi carregado (mesmo nome, empresa e competência). Evite duplicata no banco.')

        # 2) Mesmo conteúdo (hash SHA256)
        hash_conteudo = hashlib.sha256(conteudo).hexdigest()
        if Sped_Arquivo.objects.filter(hash_conteudo=hash_conteudo).exists():
            return (False, 'Este arquivo SPED (mesmo conteúdo) já foi carregado anteriormente. Evite duplicata no banco.')

        # 3) Mesmo registro 0000 (período + CNPJ) para a mesma empresa
        dt_ini, dt_fin, cnpj = self._extrair_0000_assinatura(texto)
        if empresa is not None and dt_ini is not None and dt_fin is not None and cnpj:
            q0000 = Sped_Reg_0000.objects.filter(
                arquivo__empresa=empresa,
                arquivo__tipo=tipo_char,
                dt_ini=dt_ini,
                dt_fin=dt_fin,
                cnpj=cnpj,
            )
            if q0000.exists():
                return (False, 'Já existe carga SPED com o mesmo período e CNPJ (registro 0000) para esta empresa. Evite duplicata no banco.')

        return (True, '')

    def processar_pasta_temp(
        self,
        caminho_pasta: str,
        cod_cliente: str,
        empresa=None,
    ) -> Dict:
        """
        Processa todos os arquivos .txt em uma pasta (ex.: temp de upload).
        Detecta o tipo de cada arquivo automaticamente. Grava cada registro na sua tabela
        específica (quando existir) ou em Sped_Registro.
        """
        import re
        from app.db_GDF.Sped.models import Sped_Arquivo

        path = Path(caminho_pasta)
        if not path.is_dir():
            return {'success': [], 'errors': [{'file': caminho_pasta, 'error': 'Pasta não encontrada'}], 'pendentes': []}

        success = []
        errors = []

        for arq_path in sorted(path.glob('*.txt')):
            if not arq_path.is_file():
                continue
            nome = re.sub(r'^\d+_', '', arq_path.name) or arq_path.name
            try:
                with open(arq_path, 'rb') as f:
                    conteudo = f.read()
            except Exception as e:
                errors.append({'file': nome, 'error': str(e)})
                continue
            if len(conteudo) > 10 * 1024 * 1024 * 1024:
                errors.append({'file': nome, 'error': 'Arquivo muito grande (máx 10GB)'})
                continue
            try:
                texto = _decode_sped_text(conteudo)
                tipo_char = _detectar_tipo_sped_pelo_conteudo(texto) or 'F'
                competencia = self._extrair_competencia(texto)
                empresa_eff = empresa
                if empresa_eff is None and cod_cliente:
                    _, _, cnpj_0000 = self._extrair_0000_assinatura(texto)
                    empresa_eff = self._resolver_empresa_por_cnpj(cod_cliente, cnpj_0000)
                ok_dup, msg_dup = self._validar_duplicata_sped(
                    conteudo, texto, nome, tipo_char, empresa_eff, competencia,
                )
                if not ok_dup:
                    errors.append({'file': nome, 'error': msg_dup})
                    continue
                hash_conteudo = hashlib.sha256(conteudo).hexdigest()
                arq = Sped_Arquivo.objects.create(
                    tipo=tipo_char,
                    empresa=empresa_eff,
                    competencia=competencia,
                    nome_arquivo=nome,
                    hash_conteudo=hash_conteudo,
                    data_carga=timezone.localtime(),
                )
                linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
                last_c100 = None
                for num, ln in enumerate(linhas, start=1):
                    if not ln.startswith('|'):
                        continue
                    partes = [p.strip() for p in ln.split('|') if p.strip()]
                    if not partes:
                        continue
                    last_c100 = self._gravar_linha(arq, partes, num, last_c100)
                success.append(nome)
            except Exception as e:
                errors.append({'file': nome, 'error': str(e)})
        return {'success': success, 'errors': errors, 'pendentes': []}

    def listar_arquivos_diretorio(self, diretorio: str) -> List[str]:
        """Lista arquivos .txt no diretório (para job automático)."""
        path = Path(diretorio)
        if not path.is_dir():
            return []
        return [p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() == '.txt']
