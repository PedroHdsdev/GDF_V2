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
import jwt

class Cl_Gdf():
    def __init__(self):
        self.Cliente: int = None
        self.Empresas: List[Dict] = []
        self.Groups: List[str] = []
        self.solucoes_acesso: List[Dict] = []
        self.subsolucoes_acesso: List[Dict] = []

#********************************************************************************
#--------------------------------------------------------------------------------
#           Gerar - Token JWT (Dashboard) 
#--------------------------------------------------------------------------------
    @staticmethod
    def Gerar_Token(request, user): 
        if not user.is_active:
            return None 
        else:
            payload = {
                "user_id": user.id,
                "username": user.username,
                "iat": timezone.now(),
                "exp": timezone.now() + timedelta(minutes=30),
            }

            return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
#********************************************************************************
#--------------------------------------------------------------------------------
#           GET - Dados iniciais
#--------------------------------------------------------------------------------
    def Get_Dados(self, I_User):
        self.Retorn = []
        try:
            Q_user = User.objects.filter(id=I_User.id).first()

            # Empresas do usuário
            self.Empresas = Empresas.objects.filter(
                userempresas__user=Q_user
            ).distinct()

            # Grupos do usuário
            self.Groups = Group.objects.filter(
                user=Q_user
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
            print(self.solucoes_acesso)

            # Subsoluções liberadas via grupo
            self.subsolucoes_acesso = SubsolucoesAcesso.objects.filter(
                group__in=self.Groups
            ).select_related('subsolucao')
            print(self.subsolucoes_acesso)
        
        except OperationalError as e:
            print(str(e))
        except Exception as e:
            print(str(e))

#********************************************************************************
#--------------------------------------------------------------------------------
#           GET - Soluções e Subsoluções
#--------------------------------------------------------------------------------
    def Get_Solucoes(self):
        self.Retorn = []
        try:
            if not hasattr(self, 'subsolucoes_acesso') or not hasattr(self, 'solucoes_acesso'):
                return []

            solucoes_data = []

            # 🔹 Subsoluções permitidas via grupo
            sub_ids = {
                acesso.subsolucao.cod_subsolucao
                for acesso in self.subsolucoes_acesso
                if getattr(acesso, "subsolucao", None) is not None
            }

            if not sub_ids:
                return []

            # 🔹 Soluções liberadas para o cliente
            solucoes = Solucoes.objects.filter(
                solucoesacesso__in=self.solucoes_acesso
            ).distinct()

            for solucao in solucoes:
                subsolucoes = Subsolucoes.objects.filter(
                    solucao=solucao,
                    cod_subsolucao__in=sub_ids
                ).values(
                    'cod_subsolucao',
                    'descricao'
                )

                if not subsolucoes:
                    continue

                solucoes_data.append({
                    "codigo": solucao.cod_solucao,
                    "descricao": solucao.descricao,
                    "sub_solucoes": list(subsolucoes)
                })

            #Ordenação customizada: "Soluções ADM" primeiro, "Dashboard" último
            def sort_key(sol):
                if sol["descricao"].lower() == "Adiministração":
                    return -1  # menor que tudo → primeiro
                elif sol["descricao"].lower() == "dashboard":
                    return 9999  # maior que tudo → último
                return 0  # o resto fica no meio

            solucoes_data.sort(key=sort_key)

            print(solucoes_data)
            return solucoes_data

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
    def Get_Clientes(self):
        self.Retorn = []
        try:
            clientes_data = []

            # Buscar todos os clientes
            q_clientes = Clientes.objects.all()

            for clie in q_clientes:
                # Buscar soluções de acesso para este cliente
                q_solucoes_acesso = SolucoesAcesso.objects.filter(
                    cliente=clie
                ).select_related('solucao')

                clientes_data.append({
                    "cod_cliente": clie.cod_cliente,
                    "razao": clie.razao,
                    "cnpj": clie.cnpj,
                    "is_active": clie.is_active,
                    "date_joined": clie.date_joined,
                    "solucoes_acesso": [
                        {
                            "cod_solucao": sa.solucao.cod_solucao,
                            "solucao_descricao": sa.solucao.descricao,
                            "is_active": sa.is_active
                        }
                        for sa in q_solucoes_acesso
                    ]   
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
        
        return clientes_data
    
#--------------------------------------------------------------------------------
    """Cadastro de Clientes"""
    def Cliente_ins(self, cod_cliente, razao, cnpj):
        self.Retorn = []
        try:
            cliente_instance = Clientes.objects.create(
                cod_cliente=cod_cliente,
                razao=razao,
                cnpj=cnpj,
                is_active=True,
                date_joined=now()
            )
            cliente_instance.save()

            q_solucoes = Solucoes.objects.all()

            for sol in q_solucoes:
                SolucoesAcesso.objects.create(
                    clientess=cliente_instance,
                    solucoes=sol,
                    is_active=False
                )
                
        except Clientes.DoesNotExist as e:
            print(str(e))
        except Solucoes.DoesNotExist as e:
            print(str(e))
        except IntegrityError:
            print("Erro: Cliente já existe.")
        except Exception as e:
            print(str(e))

    def Cliente_upd(self, id_cliente, razao, cnpj):   
        self.Retorn = []
        try:
            created = Clientes.objects.update_or_create(
                cod_cliente=id_cliente,
                defaults={
                    'razao': razao,
                    'cnpj': cnpj
                }
            )

        except Clientes.DoesNotExist as e:
            print(str(e))
        except Exception as e:
            print(str(e))
        
#********************************************************************************
#--------------------------------------------------------------------------------
# Empresas (Dm_Empresas)
#--------------------------------------------------------------------------------
    def Get_Empresas(self,i_cod_Cliente=None, i_busca=None):
        self.Retorn = []
        try:
            Empresas_Data    = []

            # -------------------------------------------------
            # Empresas do cliente 
            # -------------------------------------------------
            tl_empresas = Empresas.objects.filter(
                cliente_id=i_cod_Cliente
            ).distinct()
            
            #q_empresas = Empresas.objects.filter(cliente=i_cod_Cliente).distinct()
            for emp in tl_empresas:
        
                list_cert = Cert.objects.filter(raiz_cnpj=emp.cert_id)
                dt_atual = datetime.today().date()

                Empresas_Data.append({
                "cod_empresa": emp.cod_empresa,
                "cnpj": emp.cnpj,
                "razao": emp.razao,
                "fantasia": emp.fantasia,
                "ie": emp.ie,
                "im": emp.im,
                "tipo": emp.tipo,
                "matriz": emp.matriz,
                "crt": emp.crt,
                "cnae": emp.cnae,
                "iest": emp.iest,
                "suframa": emp.suframa,
                "chave_acesso": emp.chave_acesso,
                "cliente": emp.cliente_id,
                "cert_emp": [
                    {
                    "raiz": cert.raiz_cnpj,
                    "ini_validade": cert.ini_validade.strftime("%d/%m/%Y") if cert.ini_validade else None,
                    "fim_validade": cert.fim_validade.strftime("%d/%m/%Y") if cert.fim_validade else None,
                    "emissor": cert.proprietario,
                    "cpf_cnpj": cert.cpf_cnpj,
                    "cert_file": cert.arquivo_cert,
                    "status": (
                        "VERMELHO" if (cert.fim_validade.date() - dt_atual).days <= 15 else 
                        "AMARELO" if (cert.fim_validade.date() - dt_atual).days <= 30 else 
                        "VERDE"  
                        ) if cert.fim_validade else "INDEFINIDO"
                }
                for cert in list_cert
                ]
                })
            
            #tl_GrpEmpresas = GrpEmpresas.objects.filter(cliente=i_cod_Cliente).distinct() 
         
        except Empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Cert.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except GrpEmpresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004',msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')
  
        return Empresas_Data 
    
#--------------------------------------------------------------------------------
    """Retorna todas as empresas e grupos disponíveis para o cliente"""
    def Get_Empresas_ins(self, cod_cliente):
        """Retorna dados necessários para modal de inserção de empresa"""
        try:
            # ✅ Validação
            if not cod_cliente:
                raise ValueError("Cliente não identificado")

            # ✅ Todos os grupos do cliente
            todos_grupos = GrpEmpresas.objects.filter(
                cliente__cod_cliente=cod_cliente
            ).values('grp_empresa', 'descricao').distinct()

            return {
                "todos_grupos": [
                    {
                        "grp_empresa": g['grp_empresa'],
                        "descricao": g['descricao']
                    }
                    for g in todos_grupos
                ]
            }

        except Exception as e:
            print(f"[ERROR] Erro ao buscar dados para inscrição de empresa: {str(e)}")
            return {"erro": f"Erro ao buscar dados: {str(e)}"}

#--------------------------------------------------------------------------------
    """Retorna dados da empresa para edição no modal"""
    def Get_Empresas_upd(self, i_Cod_empresas, cod_cliente):
        """Buscar detalhes da empresa para modal - seguindo padrão Usuario/Cliente"""
        try:
            # ✅ Validações
            if not i_Cod_empresas or not cod_cliente:
                raise ValueError("Empresa não informada")
            
            # ✅ IDOR: Empresa deve pertencer ao cliente
            empresa = Empresas.objects.select_related(
                'cert', 'grp_empresa', 'cliente'
            ).get(
                cod_empresa=i_Cod_empresas,
                cliente__cod_cliente=cod_cliente
            )
            
            # ✅ Retornar dados completos da empresa
            return {
                "cod_empresa": empresa.cod_empresa,
                "razao": empresa.razao,
                "cnpj": empresa.cnpj,
                "fantasia": empresa.fantasia,
                "ie": empresa.ie or "",
                "im": empresa.im or "",
                "iest": empresa.iest or "",
                "tipo": empresa.tipo or "",
                "crt": empresa.crt or "",
                "cnae": empresa.cnae or "",
                "suframa": empresa.suframa or "",
                "chave_acesso": empresa.chave_acesso or "",
                "matriz": empresa.matriz or False,
                "grp_empresa": empresa.grp_empresa.grp_empresa if empresa.grp_empresa else None,
                "cert_empresa": {
                    "raiz": empresa.cert.raiz_cnpj if empresa.cert else None,
                    "ini_validade": empresa.cert.ini_validade.strftime("%d/%m/%Y") if empresa.cert and empresa.cert.ini_validade else None,
                    "fim_validade": empresa.cert.fim_validade.strftime("%d/%m/%Y") if empresa.cert and empresa.cert.fim_validade else None,
                    "emissor": empresa.cert.proprietario if empresa.cert else None,
                    "cpf_cnpj": empresa.cert.cpf_cnpj if empresa.cert else None,
                } if empresa.cert else None
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
    def Empresa_ins(self, cod_empresa, razao, cnpj, fantasia, matriz, grp_empresa, cod_cliente) -> dict:

        try:
            # ✅ Validações obrigatórias
            if not cod_empresa or not razao or not cnpj or not fantasia or not grp_empresa:
                raise ValueError("Todos os campos são obrigatórios")
            
            if not cod_cliente:
                raise ValueError("Cliente não identificado")
            
            # ✅ Verificar se grupo de empresa existe
            try:
                q_grpempresa = GrpEmpresas.objects.get(grp_empresa=grp_empresa)
            except GrpEmpresas.DoesNotExist:
                raise ValueError(f"Grupo de empresa '{grp_empresa}' não encontrado")
            
            # ✅ Transação atômica: certificado + empresa
            with transaction.atomic():
                # Buscar ou criar certificado (baseado nos 8 primeiros dígitos do CNPJ)
                cert_obj, created = Cert.objects.get_or_create(
                    raiz_cnpj=cnpj[:8],
                    defaults={
                        'cpf_cnpj': cnpj,
                    }
                )
                
                # Buscar cliente
                try:
                    cliente = Clientes.objects.get(cod_cliente=cod_cliente)
                except Clientes.DoesNotExist:
                    raise ValueError("Cliente não encontrado")
                
                # Criar nova empresa
                empresa = Empresas.objects.create(
                    cod_empresa=cod_empresa,
                    razao=razao,
                    cnpj=cnpj,
                    fantasia=fantasia,
                    grp_empresa=q_grpempresa,
                    cliente=cliente,
                    cert=cert_obj,
                    is_active=True,
                    date_joined=now()
                )
                empresa.save()
            return {"success": True, "message": "Empresa cadastrada com sucesso"}
        
        except ValueError as e:
            return {"success": False, "message": str(e)}

        
        return self.Retorn   

#--------------------------------------------------------------------------------
    """Alteração de Certificado"""
    def Cert_upd(self, raiz, cert_file, emissor, cnpj, dt_inicial,dt_fim ):
        self.Retorn = []
        try:
            if isinstance(dt_inicial, str):
                dt_inicial = datetime.strptime(dt_inicial[:10], "%d/%m/%Y").date()

            if isinstance(dt_fim, str):
                dt_fim = datetime.strptime(dt_fim[:10], "%d/%m/%Y").date()

            created = Cert.objects.update_or_create(
                raiz_cnpj=raiz,
                defaults={
                    'proprietario': emissor,  
                    'cpf_cnpj': cnpj,
                    'ini_validade': dt_inicial,  
                    'fim_validade': dt_fim,
                    'conteudo_certificado': cert_file,  
                }
            )

        except IntegrityError as e:
            print(str(e))
        except Cert.DoesNotExist as e:
            print(str(e))
        except ValueError as e:
            print(str(e))
        except OperationalError as e:
            print(str(e))
        except Exception as e:
            print(str(e))
        

#********************************************************************************
#--------------------------------------------------------------------------------
# Usuarios (DM_Usuarios)
#--------------------------------------------------------------------------------
    """ Lista de Usuários vinculados às empresas do cliente """
    def Get_Usuarios(self, i_cod_Cliente=None):
        try:
            if not i_cod_Cliente:
                self._registrar_log(type='E', id='E001', Values='Cliente')
                return []

            # -------------------------------------------------
            # Empresas do cliente (para tabela e modal)
            # -------------------------------------------------
            empresas_data = Empresas.objects.filter(
                cliente_id=i_cod_Cliente
            ).distinct()

            # -------------------------------------------------
            # Usuários vinculados às empresas do cliente
            # -------------------------------------------------
            user_ids = UserEmpresas.objects.filter(
                empresa__in=empresas_data
            ).values_list('user_id', flat=True)

            usuarios_qs = User.objects.filter(
                id__in=user_ids
            ).distinct()

            # -------------------------------------------------
            # Montagem da tabela de usuários
            # -------------------------------------------------
            usuarios_data = []

            for u in usuarios_qs:
                usuarios_data.append({
                    "id": u.id,
                    "username": u.username,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "email": u.email,
                    "is_active": u.is_active,
                    "date_joined": u.date_joined,
                    "Aglomerado": i_cod_Cliente,
                })

            return usuarios_data

        except Exception as e:
            print(str(e))
            return []

#--------------------------------------------------------------------------------
    """Retorna todas as empresas e grupos disponíveis para o cliente"""
    def Get_Usuario_ins(self, cod_cliente):
        self.Retorn = {}
        try:
            # ✅ Empresas do cliente
            todas_empresas = Empresas.objects.filter(
                cliente__cod_cliente=cod_cliente
            ).distinct()

            # ✅ Todos os grupos do cliente (via relacionamento Group)
            todos_grupos = GrupoCliente.objects.filter(
                cliente__cod_cliente=cod_cliente
            ).values('group__id', 'group__name').distinct()

            # ✅ Formatando grupos para retorno
            grupos_formatted = [
                {"id": g['group__id'], "name": g['group__name']}
                for g in todos_grupos
            ]

            self.Retorn = {
                "todas_empresas": list(todas_empresas.values('cod_empresa', 'fantasia', 'razao')),
                "todos_grupos": grupos_formatted
            }

        except Exception as e:
            print(f"[ERROR] Erro ao buscar dados para inscrição de usuário: {str(e)}")
            self.Retorn = {"erro": f"Erro ao buscar dados: {str(e)}"}

        return self.Retorn

#--------------------------------------------------------------------------------
    """Retorna dados do usuário para edição no modal"""
    def Get_Usuario_upd(self, user_id, cod_cliente):
        self.Retorn = {}
        try:
            # ✅ Validar user_id
            if not user_id or not isinstance(user_id, int):
                raise ValueError(f"ID de usuário inválido: {user_id}")

            # ✅ Empresas do cliente
            todas_empresas = Empresas.objects.filter(
                cliente__cod_cliente=cod_cliente
            ).distinct()

            # ✅ Todos os grupos do cliente (via relacionamento Group)
            todos_grupos = GrupoCliente.objects.filter(
                cliente__cod_cliente=cod_cliente
            ).distinct()

            q_user = User.objects.get(id=user_id)
            q_groups = q_user.groups.all()
            
            # ✅ Buscar APENAS as empresas do usuário
            q_empresas = Empresas.objects.filter(
                userempresas__user_id=q_user.id,
                cliente_id=cod_cliente
            ).distinct()

            # ✅ Empresas DISPONÍVEIS (não atribuídas)
            empresas_disponiveis = todas_empresas.exclude(
                cod_empresa__in=q_empresas.values_list('cod_empresa', flat=True)
            )

            # ✅ Grupos DISPONÍVEIS (não atribuídos)
            grupos_disponiveis = todos_grupos.exclude(
                group__in=q_groups
            )
            
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
                "grupos_disponiveis": list(grupos_disponiveis.values('group__id', 'group__name'))
            }

        except User.DoesNotExist as e:
            print(f"[ERROR] Usuário {user_id} não encontrado: {str(e)}")
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
    def Usuario_ins(self, username, email, password, first_name="", last_name="", 
                    empresas_ids=None, grupos_ids=None, cod_cliente=None):
       
        self.Retorn = {"success": False, "message": ""}
        
        try:
            # ✅ Validações obrigatórias
            if not username or not email or not password:
                raise ValueError("Username, email e senha são obrigatórios")
            
            if not empresas_ids or not grupos_ids:
                raise ValueError("Pelo menos 1 empresa e 1 grupo são obrigatórios")
            
            if not cod_cliente:
                raise ValueError("Cliente não identificado")
            
            # ✅ Converter strings em listas se necessário
            if isinstance(empresas_ids, str):
                empresas_ids = [int(e) for e in empresas_ids.split(',') if e.strip()]
            
            if isinstance(grupos_ids, str):
                grupos_ids = [int(g) for g in grupos_ids.split(',') if g.strip()]
            
            if not empresas_ids or not grupos_ids:
                raise ValueError("Nenhuma empresa ou grupo selecionado")
            
            # ✅ Validar que todas as empresas pertencem ao cliente
            empresas_validas = Empresas.objects.filter(
                cod_empresa__in=empresas_ids,
                cliente__cod_cliente=cod_cliente
            ).count()
            
            if empresas_validas != len(empresas_ids):
                raise ValueError("Uma ou mais empresas selecionadas não pertencem ao cliente")
            
            # ✅ Validar que todos os grupos pertencem ao cliente
            grupos_validos = GrupoCliente.objects.filter(
                group_id__in=grupos_ids,
                cliente__cod_cliente=cod_cliente
            ).count()
            
            if grupos_validos != len(grupos_ids):
                raise ValueError("Um ou mais grupos selecionados não pertencem ao cliente")
            
            # ✅ Criar usuário Django
            user_instance = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_superuser=False,
                is_staff=False,
                is_active=True
            )
            
            # ✅ Vincular empresas
            empresas_obj = Empresas.objects.filter(cod_empresa__in=empresas_ids)
            for empresa in empresas_obj:
                UserEmpresas.objects.create(
                    user=user_instance,
                    empresa=empresa
                )
            
            # ✅ Vincular grupos
            grupos_obj = Group.objects.filter(id__in=grupos_ids)
            user_instance.groups.set(grupos_obj)
            
            print(f"[OK] Usuário '{username}' criado com sucesso (ID: {user_instance.id})")
            self.Retorn = {
                "success": True,
                "message": f"Usuário '{username}' criado com sucesso",
                "user_id": user_instance.id
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
    def Usuario_upd(self, user_id: int, first_name: str, last_name: str, email: str, 
                    is_active: bool, empresa_ids: list[str], grupo_ids: list[int], 
                    cod_cliente: str) -> dict:
        self.Retorn = []
        try:
            # ✅ Validações
            if not cod_cliente:
                raise ValueError("Cliente não informado")
            
            if not user_id or not isinstance(user_id, int):
                raise ValueError(f"ID de usuário inválido: {user_id}")
            
            if not email:
                raise ValueError("Email obrigatório")
            
            if not empresa_ids:
                raise ValueError("Pelo menos 1 empresa é obrigatória")
            
            if not grupo_ids:
                raise ValueError("Pelo menos 1 grupo é obrigatório")
            
            # ✅ Validar que empresas pertencem ao cliente
            empresas_validas = Empresas.objects.filter(
                cod_empresa__in=empresa_ids,
                cliente__cod_cliente=cod_cliente
            )
            
            if empresas_validas.count() != len(empresa_ids):
                raise ValueError("Uma ou mais empresas não pertencem ao cliente")
            
            # ✅ Validar que grupos pertencem ao cliente
            grupos_validos = GrupoCliente.objects.filter(
                group_id__in=grupo_ids,
                cliente__cod_cliente=cod_cliente
            )
            
            if grupos_validos.count() != len(grupo_ids):
                raise ValueError("Um ou mais grupos não pertencem ao cliente")
            
            # ✅ Transação atômica: tudo ou nada
            with transaction.atomic():
                # Buscar usuário
                q_user = User.objects.select_for_update().get(id=user_id)
                
                # Atualizar campos
                q_user.first_name = first_name
                q_user.last_name = last_name
                q_user.email = email
                q_user.is_active = is_active
                q_user.save(update_fields=['first_name', 'last_name', 'email', 'is_active'])
                
                # Atualizar empresas (substituir todas)
                UserEmpresas.objects.filter(user=q_user).delete()
                UserEmpresas.objects.bulk_create([
                    UserEmpresas(user=q_user, empresa=emp)
                    for emp in empresas_validas
                ])
                
                # Atualizar grupos (substituir todos)
                q_user.groups.set(grupo_ids)
            
            print(f"[OK] Usuário {user_id} atualizado com sucesso")
            return {"success": True, "message": "Usuário atualizado com sucesso"}
        
        except User.DoesNotExist:
            print(f"[ERROR] Usuário {user_id} não encontrado")
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


    