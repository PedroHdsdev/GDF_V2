from django.db.models               import Prefetch
from django.utils.timezone          import now
from psycopg2                       import IntegrityError
from django.conf                    import settings
from django.contrib.auth.models     import User, Group
from app.db_GDF.Public.models       import Empresas, Clientes, Cert, UserEmpresas
from app.db_GDF.Public.models       import GrupoCliente, GrpEmpresas 
from app.db_GDF.Public.models       import Solucoes, Subsolucoes, SolucoesAcesso, SubsolucoesAcesso
from datetime                       import datetime
from django.db.utils                import OperationalError
from django.contrib.auth.hashers    import make_password
from datetime                       import timedelta
from django.utils                   import timezone
from django.db                      import transaction
from dataclasses                    import dataclass
from typing                         import List, Dict
import time

# ✅ PyJWT import com fallback
try:
    from jwt import encode as jwt_encode
except ImportError:
    try:
        # Fallback para PyJWT se a primeira falhar
        import jwt as jwt_module
        jwt_encode = jwt_module.encode
    except (ImportError, AttributeError):
        jwt_encode = None                          

class ClGdf():
    def __init__(self):
        self.Cliente: int = None
        self.Empresas: List[Dict] = []
        self.Groups: List[str] = []
        self.solucoes_acesso: List[Dict] = []
        self.subsolucoes_acesso: List[Dict] = []

#********************************************************************************
#--------------------------------------------------------------------------------
#           Calcular Status Certificado
#--------------------------------------------------------------------------------
    @staticmethod
    def calcular_status_certificado(fim_validade):
        if not fim_validade:
            return "INDEFINIDO"
        
        # Normalizar para date se for datetime
        if hasattr(fim_validade, 'date'):
            data_validade = fim_validade.date()
        else:
            data_validade = fim_validade
        
        data_atual = datetime.today().date()
        dias_restantes = (data_validade - data_atual).days
        
        if dias_restantes <= 0:
            return "VERMELHO"  # Vencido ou vence hoje
        elif dias_restantes <= 30:
            return "AMARELO"   # Vence nos próximos 30 dias
        else:
            return "VERDE"     # Mais de 30 dias para vencer

#********************************************************************************
#--------------------------------------------------------------------------------
#           Gerar - Token JWT (Dashboard) 
#--------------------------------------------------------------------------------
    @staticmethod
    def gerar_token(request, user, tipo_relatorio='Vendas'): 
        if not user.is_active:
            return None 
        
        if jwt_encode is None:
            print("[ERROR] PyJWT não disponível")
            return None
        
        # Timestamps Unix (segundos) - obrigatório para JWT
        g_v_iat = int(time.time())
        g_v_exp = g_v_iat + (30 * 60)  # +30 minutos em segundos
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "tipo_relatorio": tipo_relatorio,
            "iat": g_v_iat,
            "exp": g_v_exp,
        }

        try:
            g_og_token = jwt_encode(payload, settings.SECRET_KEY, algorithm='HS256')
            return g_og_token
        except Exception as fn_e:
            print(f"[ERROR] JWT encode failed: {str(fn_e)}")
            return None
        
#********************************************************************************
#--------------------------------------------------------------------------------
#           GET - Dados iniciais
#--------------------------------------------------------------------------------
    def get_dados(self, I_User):
        self.Retorn = []
        try:
            l_v_query_user = User.objects.filter(id=I_User.id).first()

            # Empresas do usuário
            self.Empresas = Empresas.objects.filter(
                userempresas__user=l_v_query_user
            ).distinct()

            # Grupos do usuário
            self.Groups = Group.objects.filter(
                user=l_v_query_user
            )

            # Cliente associado às empresas do usuário
            self.Cliente = Clientes.objects.filter(
                empresas__in=self.Empresas
            ).distinct().first()

            # Soluções liberadas para o cliente
            self.solucoes_acesso = SolucoesAcesso.objects.filter(
                cliente=self.Cliente,
                is_active=True
            ).select_related('solucao')

            # Subsoluções liberadas via grupo
            self.subsolucoes_acesso = SubsolucoesAcesso.objects.filter(
                group__in=self.Groups
            ).select_related('subsolucao')
        
        except OperationalError as e:
            print(str(e))
        except Exception as e:
            print(str(e))

#********************************************************************************
#--------------------------------------------------------------------------------
#           GET - Soluções e Subsoluções
#--------------------------------------------------------------------------------
    def get_solucoes(self):
        self.Retorn = []
        try:
            if not hasattr(self, 'subsolucoes_acesso') or not hasattr(self, 'solucoes_acesso'):
                return []

            lsl_dados_solucoes = []

            # 🔹 Subsoluções permitidas via grupo
            lsl_ids_subsolucoes = {
                acesso.subsolucao.cod_subsolucao
                for acesso in self.subsolucoes_acesso
                if getattr(acesso, "subsolucao", None) is not None
            }

            if not lsl_ids_subsolucoes:
                return []

            # 🔹 Soluções liberadas para o cliente
            l_v_queryset_solucoes = Solucoes.objects.filter(
                solucoesacesso__in=self.solucoes_acesso
            ).distinct()

            for l_v_solucao in l_v_queryset_solucoes:
                l_v_queryset_subsolucoes = Subsolucoes.objects.filter(
                    solucao=l_v_solucao,
                    cod_subsolucao__in=lsl_ids_subsolucoes
                ).values(
                    'cod_subsolucao',
                    'descricao'
                )

                if not l_v_queryset_subsolucoes:
                    continue

                lsl_dados_solucoes.append({
                    "codigo": l_v_solucao.cod_solucao,
                    "descricao": l_v_solucao.descricao,
                    "sub_solucoes": list(l_v_queryset_subsolucoes)
                })

            #Ordenação customizada: "Soluções ADM" primeiro, "Dashboard" último
            def sort_key(sol):
                if sol["descricao"].lower() == "Adiministração":
                    return -1  # menor que tudo → primeiro
                elif sol["descricao"].lower() == "dashboard":
                    return 9999  # maior que tudo → último
                return 0  # o resto fica no meio

            lsl_dados_solucoes.sort(key=sort_key)
            return lsl_dados_solucoes

        except AttributeError as e:
            print(str(e))
            return []
        except OperationalError as e:
            print(str(e))
            return []
        except Exception as e:
            print(str(e))
            return []

#********************************************************************************
#--------------------------------------------------------------------------------
#           GET - Clientes
#--------------------------------------------------------------------------------
    def get_clientes(self):
        self.Retorn = []
        try:
            lsl_dados_clientes = []

            # Buscar todos os clientes
            l_v_query_clientes = Clientes.objects.all()

            for l_v_cliente in l_v_query_clientes:
                lsl_dados_clientes.append({
                    "cod_cliente": l_v_cliente.cod_cliente,
                    "razao": l_v_cliente.razao,
                    "cnpj": l_v_cliente.cnpj,
                    "is_active": l_v_cliente.is_active,
                    "date_joined": l_v_cliente.date_joined, 
                })

        except Clientes.DoesNotExist as e:
            print(f"[ERROR] Clientes não encontrados: {str(e)}")
            return []
        except SolucoesAcesso.DoesNotExist as e:
            print(f"[ERROR] SolucoesAcesso não encontradas: {str(e)}")
            return []
        except IntegrityError as e:
            print(f"[ERROR] Erro de integridade: {str(e)}")
            return []
        except Exception as e:
            print(f"[ERROR] Erro ao buscar clientes: {str(e)}")
            return []
        
        return lsl_dados_clientes

#--------------------------------------------------------------------------------
    """Retorna dados do cliente para edição no modal"""
    def get_cliente_upd(self, i_v_cliente_id):
        self.Retorn = {}
        try:
            l_v_cliente = Clientes.objects.get(cod_cliente=i_v_cliente_id)

            # Soluções já atribuídas ao cliente
            l_v_query_solucoes_acesso = SolucoesAcesso.objects.filter(
                    cliente=l_v_cliente
            ).select_related('solucao')
            
            # Todas as soluções cadastradas
            l_v_queryset_todas_solucoes = Solucoes.objects.all()
            
            # Soluções disponíveis (não atribuídas)
            l_v_queryset_solucoes_disponiveis = l_v_queryset_todas_solucoes.exclude(
                cod_solucao__in=l_v_query_solucoes_acesso.values_list('solucao__cod_solucao', flat=True)
            )
            
            self.Retorn = {
                "cod_cliente": l_v_cliente.cod_cliente,
                "razao": l_v_cliente.razao,
                "cnpj": l_v_cliente.cnpj,
                "is_active": l_v_cliente.is_active,
                "solucoes_acesso": [
                        {
                            "cod_solucao": sa.solucao.cod_solucao,
                            "solucao_descricao": sa.solucao.descricao,
                            "is_active": sa.is_active
                        }
                        for sa in l_v_query_solucoes_acesso
                    ],
                "solucoes_disponiveis": list(l_v_queryset_solucoes_disponiveis.values('cod_solucao', 'descricao'))
            }

        except Clientes.DoesNotExist as e:
            print(f"[ERROR] Cliente {i_v_cliente_id} não encontrado: {str(e)}")
            return {"erro": "Cliente não encontrado"}
        except Exception as e:
            print(f"[ERROR] Erro ao buscar cliente: {str(e)}")
            return {"erro": str(e)}
        
        return self.Retorn
#--------------------------------------------------------------------------------
    """Cadastro de Clientes"""
    def set_cliente(self, i_cliente, i_razao, i_cnpj):
        try:
            with transaction.atomic():
                l_v_cliente_instance, l_v_created = Clientes.objects.get_or_create(
                    cod_cliente=i_cliente,
                    defaults={
                        'razao': i_razao,
                        'cnpj': i_cnpj,
                        'is_active': True,
                        'date_joined': now()
                    }
                )

                if not l_v_created:
                    return {"success": False, "message": "Cliente já existe"}

                # Criar vínculos de soluções (todas inativas inicialmente)
                l_v_queryset_solucoes = Solucoes.objects.all()
                SolucoesAcesso.objects.bulk_create([
                    SolucoesAcesso(cliente=l_v_cliente_instance, solucao=sol, is_active=False)
                    for sol in l_v_queryset_solucoes
                ])

            return {"success": True, "message": "Cliente cadastrado com sucesso"}

        except Solucoes.DoesNotExist:
            return {"success": False, "message": "Soluções não encontradas"}
        except IntegrityError:
            return {"success": False, "message": "Cliente já existe"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao criar cliente: {str(e)}"}

#--------------------------------------------------------------------------------
    """Atualiza cliente e seus vínculos de soluções com transação atômica"""
    def upd_cliente(self, i_cliente, i_razao, i_cnpj, i_is_active):   
        try:
            # ✅ Validações
            if not i_cliente or not i_razao or not i_cnpj:
                raise ValueError("Todos os campos são obrigatórios")
            
            # ✅ Transação atômica: tudo ou nada
            with transaction.atomic():
                # Atualizar dados básicos do cliente
                cliente = Clientes.objects.select_for_update().get(cod_cliente=i_cliente)
                cliente.razao = i_razao
                cliente.cnpj = i_cnpj
                cliente.is_active = i_is_active
                cliente.save(update_fields=['razao', 'cnpj', 'is_active'])
                
            
            print(f"[OK] Cliente {i_cliente} atualizado com sucesso")
            return {"success": True, "message": "Cliente atualizado com sucesso"}
        
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar cliente: {str(e)}")
            return {"success": False, "message": f"Erro inesperado: {str(e)}"}

    def set_cliente_solucoes(self, i_v_cod_cliente, ls_solucoes):
        """Atualiza vínculos de soluções de um cliente a partir de string "COD:STATUS""" 
        try:
            # ✅ Buscar instância do cliente
            cliente = Clientes.objects.get(cod_cliente=i_v_cod_cliente)
            # ✅ Se nada foi enviado, considerar sem alterações
            if not ls_solucoes:
                return {"success": True, "message": "Nenhuma alteração de soluções"}

            # ✅ Parse do formato "COD:STATUS"
            solucoes_dict = {}  # {cod_solucao: is_active}
            for item in ls_solucoes.split(','):
                if ':' in item:
                    cod, status = item.split(':')
                    solucoes_dict[cod.strip()] = status.strip() == '1'

            # ✅ Transação atômica
            with transaction.atomic():
                # Atualizar/criar vínculos
                for cod_sol, is_active_sol in solucoes_dict.items():
                    solucao = Solucoes.objects.get(cod_solucao=cod_sol)
                    SolucoesAcesso.objects.update_or_create(
                        cliente=cliente,
                        solucao=solucao,
                        defaults={'is_active': is_active_sol}
                    )

                # Remover vínculos não listados
                SolucoesAcesso.objects.filter(
                    cliente=cliente
                ).exclude(
                    solucao__cod_solucao__in=solucoes_dict.keys()
                ).delete()

            return {"success": True, "message": "Soluções atualizadas com sucesso"}

        except Clientes.DoesNotExist:
            return {"success": False, "message": "Cliente não encontrado"}
        except Solucoes.DoesNotExist:
            return {"success": False, "message": "Solução inválida"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar soluções: {str(e)}"}

#********************************************************************************
#--------------------------------------------------------------------------------
# Empresas (Dm_Empresas)
#--------------------------------------------------------------------------------
    def get_empresas(self,i_v_cod_cliente=None, i_busca=None):
        self.Retorn = []
        try:
            lsl_dados_empresas = []

            # -------------------------------------------------
            # Empresas do cliente COM OTIMIZAÇÃO
            # -------------------------------------------------
            # ✅ OTIMIZAÇÃO: select_related evita N+1 queries (FK direto)
            l_v_queryset_empresas = Empresas.objects.filter(
                cliente_id=i_v_cod_cliente
            ).select_related('cert').distinct()
            
            l_v_data_atual = datetime.today().date()
            
            for l_v_empresa in l_v_queryset_empresas:
                # ✅ Certificado é FK direto (objeto único, não queryset)
                l_v_cert = l_v_empresa.cert
                
                # Montar dados do certificado se existir
                l_v_cert_data = None
                if l_v_cert:
                    l_v_cert_data = {
                        "raiz": l_v_cert.raiz_cnpj,
                        "ini_validade": l_v_cert.ini_validade.strftime("%d/%m/%Y") if l_v_cert.ini_validade else None,
                        "fim_validade": l_v_cert.fim_validade.strftime("%d/%m/%Y") if l_v_cert.fim_validade else None,
                        "emissor": l_v_cert.proprietario,
                        "cpf_cnpj": l_v_cert.cpf_cnpj,
                        "cert_file": bool(l_v_cert.arquivo_cert),
                        "status": ClGdf.calcular_status_certificado(l_v_cert.fim_validade)
                    }

                lsl_dados_empresas.append({
                    "cod_empresa": l_v_empresa.cod_empresa,
                    "cnpj": l_v_empresa.cnpj,
                    "razao": l_v_empresa.razao,
                    "fantasia": l_v_empresa.fantasia,
                    "ie": l_v_empresa.ie,
                    "im": l_v_empresa.im,
                    "tipo": l_v_empresa.tipo,
                    "matriz": l_v_empresa.matriz,
                    "crt": l_v_empresa.crt,
                    "cnae": l_v_empresa.cnae,
                    "iest": l_v_empresa.iest,
                    "suframa": l_v_empresa.suframa,
                    "chave_acesso": l_v_empresa.chave_acesso,
                    "cliente": l_v_empresa.cliente_id,
                    "cert_emp": l_v_cert_data
                })
            
            print(f"[Get_Empresas] Carregadas {len(lsl_dados_empresas)} empresas com certificados otimizados")
         
        except Empresas.DoesNotExist as e:
            print(f"[ERROR] Empresas nao encontradas: {str(e)}")
        except Cert.DoesNotExist as e:
            print(f"[ERROR] Certificados nao encontrados: {str(e)}")
        except GrpEmpresas.DoesNotExist as e:
            print(f"[ERROR] Grupos de empresas nao encontrados: {str(e)}")
        except IntegrityError as e:
            print(f"[ERROR] Erro de integridade: {str(e)}")
        except Exception as e:
            print(f"[ERROR] Erro ao buscar empresas: {str(e)}")
  
        return lsl_dados_empresas 
    
#--------------------------------------------------------------------------------
    """Retorna todas as empresas e grupos disponíveis para o cliente"""
    def get_empresa_dados_ins(self, i_v_cod_cliente):
        try:
            # ✅ Validação
            if not i_v_cod_cliente:
                raise ValueError("Cliente não identificado")
            
            print(f"[DEBUG] Get_Empresas_ins - cod_cliente: {i_v_cod_cliente}")

            # ✅ Todos os grupos do cliente
            l_v_queryset_todos_grupos = GrpEmpresas.objects.filter(
                cliente__cod_cliente=i_v_cod_cliente
            ).values('grp_empresa', 'descricao').distinct()
            
            print(f"[DEBUG] Grupos encontrados: {l_v_queryset_todos_grupos.count()}")
            for l_v_grupo in l_v_queryset_todos_grupos:
                print(f"  - {l_v_grupo['grp_empresa']}: {l_v_grupo['descricao']}")

            lsl_grupos = [
                {
                    "grp_empresa": g['grp_empresa'],
                    "descricao": g['descricao']
                }
                for g in l_v_queryset_todos_grupos
            ]
            
            ol_resultado = {"todos_grupos": lsl_grupos}
            print(f"[DEBUG] Retornando: {ol_resultado}")
            
            return ol_resultado

        except Exception as e:
            print(f"[ERROR] Erro ao buscar dados para inscrição de empresa: {str(e)}")
            return {"erro": f"Erro ao buscar dados: {str(e)}"}

#--------------------------------------------------------------------------------
    """Retorna dados da empresa para edição no modal"""
    def get_empresa_upd(self, i_v_cod_empresa, i_v_cod_cliente):
        """Buscar detalhes da empresa para modal - seguindo padrão Usuario/Cliente"""
        try:
            # ✅ Validações
            if not i_v_cod_empresa or not i_v_cod_cliente:
                raise ValueError("Empresa não informada")
            
            # ✅ IDOR: Empresa deve pertencer ao cliente
            l_v_empresa = Empresas.objects.select_related(
                'cert', 'grp_empresa', 'cliente'
            ).get(
                cod_empresa=i_v_cod_empresa,
                cliente__cod_cliente=i_v_cod_cliente
            )
            
            # ✅ Retornar dados completos da empresa
            return {
                "cod_empresa": l_v_empresa.cod_empresa,
                "razao": l_v_empresa.razao,
                "cnpj": l_v_empresa.cnpj,
                "fantasia": l_v_empresa.fantasia,
                "ie": l_v_empresa.ie or "",
                "im": l_v_empresa.im or "",
                "iest": l_v_empresa.iest or "",
                "tipo": l_v_empresa.tipo or "",
                "crt": l_v_empresa.crt or "",
                "cnae": l_v_empresa.cnae or "",
                "suframa": l_v_empresa.suframa or "",
                "chave_acesso": l_v_empresa.chave_acesso or "",
                "matriz": l_v_empresa.matriz or False,
                "grp_empresa": l_v_empresa.grp_empresa.grp_empresa if l_v_empresa.grp_empresa else None,
                "cert_empresa": {
                    "raiz": l_v_empresa.cert.raiz_cnpj if l_v_empresa.cert else None,
                    "ini_validade": l_v_empresa.cert.ini_validade.strftime("%d/%m/%Y") if l_v_empresa.cert and l_v_empresa.cert.ini_validade else None,
                    "fim_validade": l_v_empresa.cert.fim_validade.strftime("%d/%m/%Y") if l_v_empresa.cert and l_v_empresa.cert.fim_validade else None,
                    "emissor": l_v_empresa.cert.proprietario if l_v_empresa.cert else None,
                    "cpf_cnpj": l_v_empresa.cert.cpf_cnpj if l_v_empresa.cert else None,
                } if l_v_empresa.cert else None
            }
            
        except Empresas.DoesNotExist:
            return {"erro": "Empresa não encontrada"}
        except ValueError as e:
            return {"erro": str(e)}
        except Exception as e:
            print(f"[ERROR] Erro ao buscar dados para edição de empresa: {str(e)}")
            return {"erro": f"Erro ao buscar dados: {str(e)}"}
        
#--------------------------------------------------------------------------------
    """Cadastro de Empresas"""
    def set_empresa(
        self,
        i_v_cod_empresa,
        i_v_razao,
        i_v_cnpj,
        i_v_fantasia,
        i_v_grp_empresa,
        i_v_cod_cliente,
        i_b_matriz=False,
        i_v_ie="",
        i_v_im="",
        i_v_iest="",
        i_v_crt="",
        i_v_cnae="",
        i_v_suframa="",
        i_v_chave_acesso=""
    ) -> dict:

        try:
            # ✅ Validações obrigatórias
            if not i_v_cod_empresa or not i_v_razao or not i_v_cnpj or not i_v_fantasia or not i_v_grp_empresa:
                raise ValueError("Todos os campos são obrigatórios")
            
            if not i_v_cod_cliente:
                raise ValueError("Cliente não identificado")
            
            # ✅ Verificar se grupo de empresa existe
            try:
                q_grpempresa = GrpEmpresas.objects.get(grp_empresa=i_v_grp_empresa)
            except GrpEmpresas.DoesNotExist:
                raise ValueError(f"Grupo de empresa '{i_v_grp_empresa}' não encontrado")
            
            # ✅ Transação atômica: certificado + empresa
            with transaction.atomic():
                # Buscar ou criar certificado (baseado nos 8 primeiros dígitos do CNPJ)
                cert_obj, created = Cert.objects.get_or_create(
                    raiz_cnpj=i_v_cnpj[:8],
                    defaults={
                        'cpf_cnpj': i_v_cnpj,
                    }
                )
                
                # Buscar cliente
                try:
                    cliente = Clientes.objects.get(cod_cliente=i_v_cod_cliente)
                except Clientes.DoesNotExist:
                    raise ValueError("Cliente não encontrado")
                
                # Criar nova empresa
                empresa = Empresas.objects.create(
                    cod_empresa=i_v_cod_empresa,
                    razao=i_v_razao,
                    cnpj=i_v_cnpj,
                    fantasia=i_v_fantasia,
                    grp_empresa=q_grpempresa,
                    cliente=cliente,
                    cert=cert_obj,
                    matriz=i_b_matriz,
                    ie=i_v_ie,
                    im=i_v_im,
                    iest=i_v_iest,
                    crt=i_v_crt,
                    cnae=i_v_cnae,
                    suframa=i_v_suframa,
                    chave_acesso=i_v_chave_acesso
                )
                empresa.save()

            return {"success": True, "message": "Empresa cadastrada com sucesso"}
        
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            print(f"[ERROR] Empresa_ins - Erro: {str(e)}")
            return {"success": False, "message": f"Erro ao criar empresa: {str(e)}"}

#--------------------------------------------------------------------------------
    """Atualização de Empresas"""
    def upd_empresa(
        self,
        i_v_cod_empresa,
        i_v_razao,
        i_v_fantasia,
        i_v_grp_empresa,
        i_v_cod_cliente,
        i_b_matriz=False,
        i_v_ie="",
        i_v_im="",
        i_v_iest="",
        i_v_crt="",
        i_v_cnae="",
        i_v_suframa="",
        i_v_chave_acesso=""
    ) -> dict:
        try:
            print(f"[DEBUG] Empresa_upd - cod_empresa: {i_v_cod_empresa}, cod_cliente: {i_v_cod_cliente}")
            
            # ✅ Validações obrigatórias
            if not i_v_razao or not i_v_fantasia:
                raise ValueError("Razão social e fantasia são obrigatórios")
            
            if not i_v_cod_cliente:
                raise ValueError("Cliente não identificado")
            
            # ✅ Validar IDOR: Empresa deve pertencer ao cliente
            empresa = Empresas.objects.get(
                cod_empresa=i_v_cod_empresa,
                cliente__cod_cliente=i_v_cod_cliente
            )
            
            # ✅ Se grupo foi informado, validar
            if i_v_grp_empresa:
                try:
                    q_grpempresa = GrpEmpresas.objects.get(grp_empresa=i_v_grp_empresa)
                    empresa.grp_empresa = q_grpempresa
                except GrpEmpresas.DoesNotExist:
                    raise ValueError(f"Grupo de empresa '{i_v_grp_empresa}' não encontrado")
            
            # ✅ Atualizar campos
            empresa.razao = i_v_razao
            empresa.fantasia = i_v_fantasia
            empresa.matriz = i_b_matriz
            empresa.ie = i_v_ie or None
            empresa.im = i_v_im or None
            empresa.iest = i_v_iest or None
            empresa.crt = i_v_crt or None
            empresa.cnae = i_v_cnae or None
            empresa.suframa = i_v_suframa or None
            empresa.chave_acesso = i_v_chave_acesso or None
            
            empresa.save(update_fields=[
                'razao', 'fantasia', 'matriz', 'ie', 'im', 'iest', 
                'crt', 'cnae', 'suframa', 'chave_acesso', 'grp_empresa'
            ])
            
            print(f"[OK] Empresa {i_v_cod_empresa} atualizada com sucesso")
            return {"success": True, "message": "Empresa atualizada com sucesso"}
        
        except Empresas.DoesNotExist:
            print(f"[ERROR] Empresa {i_v_cod_empresa} não encontrada para cliente {i_v_cod_cliente}")
            return {"success": False, "message": "Empresa não encontrada"}
        except ValueError as e:
            print(f"[ERROR] Empresa_upd - Validação: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            print(f"[ERROR] Empresa_upd - Erro: {str(e)}")
            return {"success": False, "message": f"Erro ao atualizar empresa: {str(e)}"}

#--------------------------------------------------------------------------------
    """Atualizar certificado digital"""
    def upd_certificado(self, i_v_arquivo_cert=None, i_v_cod_empresa=None, i_v_emissor="", i_v_cpf_cnpj="", i_v_ini_validade="", i_v_fim_validade=""):
        
        try:

            if not i_v_cod_empresa:
                raise ValueError("Empresa não identificada")

            empresa = Empresas.objects.get(
                cod_empresa=i_v_cod_empresa,
            )
            
            # ✅ Se nenhum dado foi fornecido, erro
            if not i_v_arquivo_cert and not (i_v_emissor or i_v_cpf_cnpj or i_v_ini_validade or i_v_fim_validade):
                raise ValueError("Nenhum dado para atualizar")
            
            # ✅ Empresa deve ter certificado (criado junto com a empresa)
            if not empresa.cert:
                raise ValueError("Empresa não possui certificado vinculado")
            
            # ✅ Preparar dados para atualizar
            l_v_defaults = {}
            
            # ✅ Processar arquivo se fornecido
            if i_v_arquivo_cert:
                l_v_cert_content = i_v_arquivo_cert.read()
                l_v_file_name = i_v_arquivo_cert.name
                print(f"[DEBUG] Processando certificado: {l_v_file_name}, tamanho: {len(l_v_cert_content)} bytes")
                l_v_defaults['nm_arquivo_pfx'] = l_v_file_name
                l_v_defaults['arquivo_cert'] = l_v_cert_content
            
            # ✅ Adicionar campos opcionais se fornecidos
            if i_v_emissor:
                l_v_defaults['emissor'] = i_v_emissor
            if i_v_cpf_cnpj:
                l_v_defaults['cpf_cnpj'] = i_v_cpf_cnpj
            
            # ✅ Converter datas se fornecidas
            if i_v_ini_validade:
                try:
                    # Tentar formato DD/MM/YYYY primeiro
                    if "/" in i_v_ini_validade:
                        dt_ini = datetime.strptime(i_v_ini_validade[:10], "%d/%m/%Y").date()
                    else:
                        dt_ini = datetime.strptime(i_v_ini_validade[:10], "%Y-%m-%d").date()
                    l_v_defaults['ini_validade'] = dt_ini
                    print(f"[OK] Data início convertida: {dt_ini}")
                except Exception as e:
                    print(f"[WARN] Data início inválida: {i_v_ini_validade} - {str(e)}")
            
            if i_v_fim_validade:
                try:
                    # Tentar formato DD/MM/YYYY primeiro
                    if "/" in i_v_fim_validade:
                        dt_fim = datetime.strptime(i_v_fim_validade[:10], "%d/%m/%Y").date()
                    else:
                        dt_fim = datetime.strptime(i_v_fim_validade[:10], "%Y-%m-%d").date()
                    l_v_defaults['fim_validade'] = dt_fim
                    print(f"[OK] Data fim convertida: {dt_fim}")
                except Exception as e:
                    print(f"[WARN] Data fim inválida: {i_v_fim_validade} - {str(e)}")
            
            # ✅ Atualizar APENAS o certificado existente da empresa
            certificado = empresa.cert
            for campo, valor in l_v_defaults.items():
                setattr(certificado, campo, valor)
            certificado.save()
            
            print(f"[OK] Certificado atualizado: raiz_cnpj={certificado.raiz_cnpj}")
            print(f"[OK] Dados salvos - Emissor: {i_v_emissor}, CNPJ: {i_v_cpf_cnpj}, Datas: {i_v_ini_validade} a {i_v_fim_validade}")
            
            return {"success": True, "message": "Certificado atualizado com sucesso"}
        
        except ValueError as e:
            print(f"[ERROR] Cert_upd - Validação: {str(e)}")
            return {"success": False, "message": str(e)}
        except Empresas.DoesNotExist:
            print("[ERROR] Cert_upd - Empresa não encontrada")
            return {"success": False, "message": "Empresa não encontrada"}
        except Exception as e:
            print(f"[ERROR] Cert_upd - Erro: {str(e)}")
            return {"success": False, "message": f"Erro ao salvar certificado: {str(e)}"}

#********************************************************************************
#--------------------------------------------------------------------------------
# Usuarios (DM_Usuarios)
#--------------------------------------------------------------------------------
    """ Lista de Usuários vinculados às empresas do cliente """
    def get_usuarios(self, i_v_cod_cliente=None):
        try:
            if not i_v_cod_cliente:
                self._registrar_log(type='E', id='E001', Values='Cliente')
                return []

            # -------------------------------------------------
            # Empresas do cliente (para tabela e modal)
            # -------------------------------------------------
            l_v_queryset_empresas = Empresas.objects.filter(
                cliente_id=i_v_cod_cliente
            ).distinct()

            # -------------------------------------------------
            # Usuários vinculados às empresas do cliente
            # -------------------------------------------------
            lsl_ids_usuarios = UserEmpresas.objects.filter(
                empresa__in=l_v_queryset_empresas
            ).values_list('user_id', flat=True)

            l_v_queryset_usuarios = User.objects.filter(
                id__in=lsl_ids_usuarios
            ).distinct()

            # -------------------------------------------------
            # Montagem da tabela de usuários
            # -------------------------------------------------
            lsl_dados_usuarios = []

            for l_v_usuario in l_v_queryset_usuarios:
                lsl_dados_usuarios.append({
                    "id": l_v_usuario.id,
                    "username": l_v_usuario.username,
                    "first_name": l_v_usuario.first_name,
                    "last_name": l_v_usuario.last_name,
                    "email": l_v_usuario.email,
                    "is_active": l_v_usuario.is_active,
                    "date_joined": l_v_usuario.date_joined,
                    "Aglomerado": i_v_cod_cliente,
                })

            return lsl_dados_usuarios

        except Exception as e:
            print(str(e))
            return []

#--------------------------------------------------------------------------------
    """Retorna todas as empresas e grupos disponíveis para o cliente"""
    def get_usuario_dados_ins(self, i_v_cod_cliente):
        self.Retorn = {}
        try:
            # ✅ Empresas do cliente
            l_v_queryset_todas_empresas = Empresas.objects.filter(
                cliente__cod_cliente=i_v_cod_cliente
            ).distinct()

            # ✅ Todos os grupos do cliente (via relacionamento Group)
            l_v_queryset_todos_grupos = GrupoCliente.objects.filter(
                cliente__cod_cliente=i_v_cod_cliente
            ).values('group__id', 'group__name').distinct()

            # ✅ Formatando grupos para retorno
            lsl_grupos_formatados = [
                {"id": g['group__id'], "name": g['group__name']}
                for g in l_v_queryset_todos_grupos
            ]

            self.Retorn = {
                "todas_empresas": list(l_v_queryset_todas_empresas.values('cod_empresa', 'fantasia', 'razao')),
                "todos_grupos": lsl_grupos_formatados
            }

        except Exception as e:
            print(f"[ERROR] Erro ao buscar dados para inscrição de usuário: {str(e)}")
            self.Retorn = {"erro": f"Erro ao buscar dados: {str(e)}"}

        return self.Retorn

#--------------------------------------------------------------------------------
    """Retorna dados do usuário para edição no modal"""
    def get_usuario_upd(self, i_v_user_id, i_v_cod_cliente):
        self.Retorn = {}
        try:
            # ✅ Validar user_id
            if not i_v_user_id or not isinstance(i_v_user_id, int):
                raise ValueError(f"ID de usuário inválido: {i_v_user_id}")

            # ✅ Empresas do cliente
            l_v_queryset_todas_empresas = Empresas.objects.filter(
                cliente__cod_cliente=i_v_cod_cliente
            ).distinct()

            # ✅ Todos os grupos do cliente (via relacionamento Group)
            todos_grupos = GrupoCliente.objects.filter(
                cliente__cod_cliente=i_v_cod_cliente
            ).distinct()

            q_user = User.objects.get(id=i_v_user_id)
            q_groups = q_user.groups.all()
            
            # ✅ Buscar APENAS as empresas do usuário
            q_empresas = Empresas.objects.filter(
                userempresas__user_id=q_user.id,
                cliente_id=i_v_cod_cliente
            ).distinct()

            # ✅ Empresas DISPONÍVEIS (não atribuídas)
            empresas_disponiveis = l_v_queryset_todas_empresas.exclude(
                cod_empresa__in=q_empresas.values_list('cod_empresa', flat=True)
            )

            # ✅ Grupos DISPONÍVEIS (não atribuídos)
            grupos_disponiveis = todos_grupos.exclude(
                group__in=q_groups
            )
            
            # ✅ Transformar grupos_disponiveis para o formato esperado pelo JS
            ls_grupos_disponiveis = []
            for grp in grupos_disponiveis:
                ls_grupos_disponiveis.append({
                    'id': grp.group.id,
                    'name': grp.group.name
                })
            
            self.Retorn = {
                "id": q_user.id,
                "username": q_user.username,
                "email": q_user.email,
                "first_name": q_user.first_name,
                "last_name": q_user.last_name,
                "is_active": q_user.is_active,
                "grupos": list(q_groups.values('id', 'name')),
                "empresas": list(q_empresas.values('cod_empresa', 'fantasia', 'razao')),
                "empresas_disponiveis": list(empresas_disponiveis.values('cod_empresa', 'fantasia', 'razao')),
                "grupos_disponiveis": ls_grupos_disponiveis
            }

        except User.DoesNotExist as e:
            print(f"[ERROR] Usuário {i_v_user_id} não encontrado: {str(e)}")
            self.Retorn = {"erro": "Usuário não encontrado"}
        except ValueError as e:
            print(f"[ERROR] Validação falhou: {str(e)}")
            self.Retorn = {"erro": str(e)}
        except Exception as e:
            print(f"[ERROR] Erro ao buscar usuário: {str(e)}")
            self.Retorn = {"erro": f"Erro ao buscar usuário: {str(e)}"}

        return self.Retorn

#--------------------------------------------------------------------------------
    """Método legado - manter para compatibilidade"""
    def set_usuario(self, i_v_username, i_v_email, i_v_password, i_v_first_name="", i_v_last_name="", 
                    i_lsl_empresas_ids=None, i_lsl_grupos_ids=None, i_v_cod_cliente=None):
       
        self.Retorn = {"success": False, "message": ""}
        
        try:
            # ✅ Validações obrigatórias
            if not i_v_username or not i_v_email or not i_v_password:
                raise ValueError("Username, email e senha são obrigatórios")
            
            if not i_lsl_empresas_ids or not i_lsl_grupos_ids:
                raise ValueError("Pelo menos 1 empresa e 1 grupo são obrigatórios")
            
            if not i_v_cod_cliente:
                raise ValueError("Cliente não identificado")
            
            # ✅ Converter strings em listas se necessário
            if isinstance(i_lsl_empresas_ids, str):
                i_lsl_empresas_ids = [int(e) for e in i_lsl_empresas_ids.split(',') if e.strip()]
            
            if isinstance(i_lsl_grupos_ids, str):
                i_lsl_grupos_ids = [int(g) for g in i_lsl_grupos_ids.split(',') if g.strip()]
            
            if not i_lsl_empresas_ids or not i_lsl_grupos_ids:
                raise ValueError("Nenhuma empresa ou grupo selecionado")
            
            # ✅ Validar que todas as empresas pertencem ao cliente
            l_v_empresas_validas = Empresas.objects.filter(
                cod_empresa__in=i_lsl_empresas_ids,
                cliente__cod_cliente=i_v_cod_cliente
            ).count()
            
            if l_v_empresas_validas != len(i_lsl_empresas_ids):
                raise ValueError("Uma ou mais empresas selecionadas não pertencem ao cliente")
            
            # ✅ Validar que todos os grupos pertencem ao cliente
            l_v_grupos_validos = GrupoCliente.objects.filter(
                group_id__in=i_lsl_grupos_ids,
                cliente__cod_cliente=i_v_cod_cliente
            ).count()
            
            if l_v_grupos_validos != len(i_lsl_grupos_ids):
                raise ValueError("Um ou mais grupos selecionados não pertencem ao cliente")
            
            # ✅ Criar usuário Django
            l_v_user_instance = User.objects.create_user(
                username=i_v_username,
                email=i_v_email,
                password=i_v_password,
                first_name=i_v_first_name,
                last_name=i_v_last_name,
                is_superuser=False,
                is_staff=False,
                is_active=True
            )
            
            # ✅ Vincular empresas
            l_v_queryset_empresas = Empresas.objects.filter(cod_empresa__in=i_lsl_empresas_ids)
            for l_v_empresa in l_v_queryset_empresas:
                UserEmpresas.objects.create(
                    user=l_v_user_instance,
                    empresa=l_v_empresa
                )
            
            # ✅ Vincular grupos
            l_v_queryset_grupos = Group.objects.filter(id__in=i_lsl_grupos_ids)
            l_v_user_instance.groups.set(l_v_queryset_grupos)
            
            print(f"[OK] Usuário '{i_v_username}' criado com sucesso (ID: {l_v_user_instance.id})")
            self.Retorn = {
                "success": True,
                "message": f"Usuário '{i_v_username}' criado com sucesso",
                "user_id": l_v_user_instance.id
            }
        
        except ValueError as e:
            self.Retorn = {"success": False, "message": str(e)}
            print(f"[ERROR] Usuario_ins - Validação: {str(e)}")
        except IntegrityError as e:
            self.Retorn = {"success": False, "message": f"Usuário ou email já existe"}
            print(f"[ERROR] Usuario_ins - Duplicado: {str(e)}")
        except Exception as e:
            self.Retorn = {"success": False, "message": f"Erro ao criar usuário: {str(e)}"}
            print(f"[ERROR] Usuario_ins - Erro geral: {str(e)}")
        
        return self.Retorn

#--------------------------------------------------------------------------------
    """Atualiza usuário, suas empresas e grupos com transação atômica"""
    def upd_usuario(self, i_v_user_id: int, i_v_first_name: str, i_v_last_name: str, i_v_email: str, 
                    i_v_is_active: bool, i_lsl_empresa_ids: list[str], i_lsl_grupo_ids: list[int], 
                    i_v_cod_cliente: str) -> dict:
        self.Retorn = []
        try:
            # ✅ Validações
            if not i_v_cod_cliente:
                raise ValueError("Cliente não informado")
            
            if not i_v_user_id or not isinstance(i_v_user_id, int):
                raise ValueError(f"ID de usuário inválido: {i_v_user_id}")
            
            if not i_v_email:
                raise ValueError("Email obrigatório")
            
            if not i_lsl_empresa_ids:
                raise ValueError("Pelo menos 1 empresa é obrigatória")
            
            if not i_lsl_grupo_ids:
                raise ValueError("Pelo menos 1 grupo é obrigatório")
            
            # ✅ Validar que empresas pertencem ao cliente
            l_v_queryset_empresas_validas = Empresas.objects.filter(
                cod_empresa__in=i_lsl_empresa_ids,
                cliente__cod_cliente=i_v_cod_cliente
            )
            
            if l_v_queryset_empresas_validas.count() != len(i_lsl_empresa_ids):
                raise ValueError("Uma ou mais empresas não pertencem ao cliente")
            
            # ✅ Validar que grupos pertencem ao cliente
            l_v_queryset_grupos_validos = GrupoCliente.objects.filter(
                group_id__in=i_lsl_grupo_ids,
                cliente__cod_cliente=i_v_cod_cliente
            )
            
            if l_v_queryset_grupos_validos.count() != len(i_lsl_grupo_ids):
                raise ValueError("Um ou mais grupos não pertencem ao cliente")
            
            # ✅ Transação atômica: tudo ou nada
            with transaction.atomic():
                # Buscar usuário
                l_v_user = User.objects.select_for_update().get(id=i_v_user_id)
                
                # Atualizar campos
                l_v_user.first_name = i_v_first_name
                l_v_user.last_name = i_v_last_name
                l_v_user.email = i_v_email
                l_v_user.is_active = i_v_is_active
                l_v_user.save(update_fields=['first_name', 'last_name', 'email', 'is_active'])
                
                # Atualizar empresas (substituir todas)
                UserEmpresas.objects.filter(user=l_v_user).delete()
                UserEmpresas.objects.bulk_create([
                    UserEmpresas(user=l_v_user, empresa=emp)
                    for emp in l_v_queryset_empresas_validas
                ])
                
                # Atualizar grupos (substituir todos)
                l_v_user.groups.set(i_lsl_grupo_ids)
            
            print(f"[OK] Usuário {i_v_user_id} atualizado com sucesso")
            return {"success": True, "message": "Usuário atualizado com sucesso"}
        
        except User.DoesNotExist:
            print(f"[ERROR] Usuário {i_v_user_id} não encontrado")
            self.Retorn = [{"erro": "Usuário não encontrado"}]
            return {"success": False, "message": "Usuário não encontrado"}
        except ValueError as e:
            print(f"[ERROR] Validação falhou: {str(e)}")
            self.Retorn = [{"erro": str(e)}]
            return {"success": False, "message": str(e)}
        except IntegrityError as e:
            print(f"[ERROR] Erro de integridade: {str(e)}")
            self.Retorn = [{"erro": f"Erro de integridade: {str(e)}"}]
            return {"success": False, "message": "Email já está em uso"}
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar usuário: {str(e)}")
            self.Retorn = [{"erro": str(e)}]
            return {"success": False, "message": f"Erro inesperado: {str(e)}"}


#********************************************************************************


    