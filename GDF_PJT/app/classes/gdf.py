from django.db.models               import Prefetch
from django.utils.timezone          import now
from psycopg2                       import IntegrityError
from django.conf                    import settings
from app.db_GDF.Public.models       import AuthUser, Empresas, Clientes, Cert, UserEmpresas
from app.db_GDF.Public.models       import AuthGroup, AuthUserGroups, GrupoCliente, GrpEmpresas 
from app.db_GDF.Public.models       import Solucoes, Subsolucoes, SolucoesAcesso, SubsolucoesAcesso
from datetime                       import datetime
from django.db.utils                import OperationalError
from django.contrib.auth.hashers    import make_password
from datetime                       import timedelta
from django.utils                   import timezone
from dataclasses                    import dataclass
from typing                         import List, Dict
import jwt

class Cl_Gdf():
    def __init__(self):
        self.Cliente: int = None
        self.Empresas: List[Dict] = []
        self.AuthGroups: List[str] = []
        self.solucoes_acesso: List[Dict] = []
        self.subsolucoes_acesso: List[Dict] = []

#--------------------------------------------------------------------------------
#           Gerar - Token JWT (Dashboard) 
#--------------------------------------------------------------------------------
    @staticmethod
    def Gerar_token(request, user): 
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
#           GET - consultas
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#           GET - Dados iniciais
#--------------------------------------------------------------------------------
    def get_dados(self, I_User):
        self.Retorn = []
        try:
            Q_user = AuthUser.objects.filter(id=I_User.id).first()

            # Empresas do usuário
            self.Empresas = Empresas.objects.filter(
                userempresas__user=Q_user
            ).distinct()
            
            # Grupos do usuário
            self.AuthGroups = AuthGroup.objects.filter(
                authusergroups__user=Q_user
            )

            # Cliente associado às empresas do usuário
            self.Cliente = Clientes.objects.filter(
                empresas__in=self.Empresas
            ).distinct().first()

            # Soluções liberadas para o cliente
            self.solucoes_acesso = SolucoesAcesso.objects.filter(
                clientess=self.Cliente,
                is_active=True
            ).select_related('solucoes')
            print(self.solucoes_acesso)

            # Subsoluções liberadas via grupo
            self.subsolucoes_acesso = SubsolucoesAcesso.objects.filter(
                group__in=self.AuthGroups
            ).select_related('subsolucoes')
            print(self.subsolucoes_acesso)
        
        except OperationalError as e:
            print(str(e))
        except Exception as e:
            print(str(e))

#--------------------------------------------------------------------------------
#           GET - Soluções e Subsoluções
#--------------------------------------------------------------------------------
    def get_solucoes(self):
        self.Retorn = []
        try:
            if not hasattr(self, 'subsolucoes_acesso') or not hasattr(self, 'solucoes_acesso'):
                return []

            solucoes_data = []

            # 🔹 Subsoluções permitidas via grupo
            sub_ids = {
                acesso.subsolucoes.cod_subsolucoes
                for acesso in self.subsolucoes_acesso
                if acesso.subsolucoes
            }

            if not sub_ids:
                return []

            # 🔹 Soluções liberadas para o cliente
            solucoes = Solucoes.objects.filter(
                solucoesacesso__in=self.solucoes_acesso
            ).distinct()

            for solucao in solucoes:
                subsolucoes = Subsolucoes.objects.filter(
                    solucoes=solucao,
                    cod_subsolucoes__in=sub_ids
                ).values(
                    'cod_subsolucoes',
                    'descricao'
                )

                if not subsolucoes:
                    continue

                solucoes_data.append({
                    "codigo": solucao.cod_solucoes,
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

#--------------------------------------------------------------------------------
#           GET - Usuarios
#--------------------------------------------------------------------------------
    def get_usuarios(self, i_cod_Cliente=None):
        try:
            if not i_cod_Cliente:
                self._registrar_log(type='E', id='E001', Values='Cliente')
                return [], [], []

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
                empresas__in=empresas_data
            ).values_list('user_id', flat=True)

            usuarios_qs = AuthUser.objects.filter(
                id__in=user_ids
            ).distinct()

            # -------------------------------------------------
            # Empresa de referência do usuário (primeiro vínculo)
            # -------------------------------------------------
            user_empresa_map = {}

            vinculos = UserEmpresas.objects.filter(
                empresas__in=empresas_data,
                user__in=usuarios_qs
            ).select_related('empresas')

            for v in vinculos:
                # pega a primeira empresa encontrada por usuário
                user_empresa_map.setdefault(
                    v.user_id,
                    v.empresas.cod_empresa
                )

            # -------------------------------------------------
            # Grupos dos usuários
            # -------------------------------------------------
            grupo_map = {
                g.id: g.name
                for g in AuthGroup.objects.all()
            }

            user_group_map = {}

            grupos_user = AuthUserGroups.objects.filter(
                user_id__in=user_ids
            )

            for ug in grupos_user:
                nome = grupo_map.get(ug.group_id)
                if nome:
                    user_group_map.setdefault(
                        ug.user_id, []
                    ).append(nome)

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
                    "empresa_id": user_empresa_map.get(u.id),
                    "groups": user_group_map.get(u.id, []),
                })

            # -------------------------------------------------
            # Grupos disponíveis do cliente (modal)
            # -------------------------------------------------
            AuthGroups_data = GrupoCliente.objects.filter(
                cliente_id=i_cod_Cliente
            ).distinct()

            return usuarios_data, empresas_data, AuthGroups_data

        except Exception as e:
            print(str(e))
            return [], [], []
        
#--------------------------------------------------------------------------------
#           GET - Empresas
#--------------------------------------------------------------------------------
    def get_empresas(self):
        self.Retorn = []
        try:
            empresas_data = []
            Q_GrpEmpresas = None

            if not self.q_cleinte:
                self._registrar_log(type='E', id='E001', Values='Cliente')
                return [], []
            
            q_empresas = empresas.objects.filter(cliente=self.q_cleinte).distinct()
            for emp in q_empresas:
        
                list_cert = Cert.objects.filter(raiz_cnpj=emp.cert_id)
                dt_atual = datetime.today().date()

                empresas_data.append({
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
                "grp_empresa": emp.grp_empresa_id,
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
            
            Q_GrpEmpresas = GrpEmpresas.objects.filter(cliente=self.q_cleinte).distinct() 
         
        except empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Cert.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except GrpEmpresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004',msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')
  
        return empresas_data, Q_GrpEmpresas

#--------------------------------------------------------------------------------
#           GET - Clientes
#--------------------------------------------------------------------------------
    def get_clientes(self):
        self.Retorn = []
        try:
            clientes_data = []
            Solucoes_data = []

            q_clientes = clientes.objects.all()
            q_solucoes = SolucoesAcesso.objects.filter(clientess__in=q_clientes)
            Solucoes_data = Solucoes.objects.all()
            
            for clie in q_clientes:
                 clientes_data.append({
                "cod_cliente": clie.cod_cliente,
                "razao": clie.razao,
                "cnpj": clie.cnpj,
                "is_active": clie.is_active,
                "date_joined": clie.date_joined,
                "solucoes_acesso": [
                    {
                        "solucoes_id": sa.solucoes.cod_solucoes,
                        "clientess_id": sa.clientess_id,
                        "is_active": sa.is_active
                    }
                    for sa in q_solucoes if sa.clientess_id == clie.cod_cliente
                ]   
                })

        except clientes.DoesNotExist:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            return [], []
        except SolucoesAcesso.DoesNotExist:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            return [], []
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004', msg=f"Erro: {str(e)}")
            return [], []
        except Exception as e:
            self._registrar_log(type='E', id='E000')
            return [], []
        
        return clientes_data, Solucoes_data

#********************************************************************************
#--------------------------------------------------------------------------------
#           SET - inserção
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#           SET - Usuarios
#--------------------------------------------------------------------------------
    def set_user(self, empresa, Usernome, firstname, lastname, email, senha, grpacesso):
        self.Retorn = []
        try:
            user_instance = User.objects.create(
                username=Usernome,
                first_name=firstname,
                last_name=lastname,
                password=make_password(senha),
                email=email,
                is_superuser=False,
                is_staff=False,
                is_active=True,
                date_joined=now()
            )
            
            user_instance.save()
            cod_empresa = empresas.objects.get(cod_empresa=empresa)
            cod_empresa.user.add(user_instance)

            group = Group.objects.get(id=grpacesso)
            user_instance.groups.add(group)
            
            self._registrar_log(type='S', id='S001', Values='Usuario: '+Usernome)
        
        except empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")   
        except Group.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")   
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004',msg=f"Erro: {str(e)}", Values='Usuario : '+Usernome)
        except Exception as e:
            self._registrar_log(type='E', id='E000')      


#--------------------------------------------------------------------------------
#           SET - Usuario Grupo
#--------------------------------------------------------------------------------
    def set_userGruop(self, user_id, Group_id):
        self.Retorn = []
        try:
            user  = User.objects.get(id=user_id)
            group = Group.objects.get(id=Group_id)

            # Verifica se o usuário já está no grupo
            if not user.groups.filter(id=group.id).exists():
                user.groups.add(group)
                user.save()

                self._registrar_log(type='S', id='S001', Values=f"Usuário: '{user.username}' Grupo: '{group.name}'.") 
            else:
                self._registrar_log(type='E', id='E002', msg="Usuário já pertence a este grupo.")  

        except User.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")   
        except Group.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")   
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004',msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')    
    
#--------------------------------------------------------------------------------
#           SET -  Empresa
#--------------------------------------------------------------------------------
    def set_empresa(self, cod_empresa, razao, cnpj, fantasia, grp_empresa):
        self.Retorn = []
        Cert_obj = Cert.objects.filter(raiz_cnpj=cnpj[:8]).first()
        try:
            q_grpempresa = GrpEmpresas.objects.get(grp_empresa=grp_empresa)
            if not Cert_obj:
                cert_instance = Cert.objects.create(
                    raiz_cnpj = cnpj[:8],
                    cpf_cnpj  = cnpj,
                )
                cert_instance.save()

            Cert_obj = Cert.objects.get(raiz_cnpj=cnpj[:8])
            empresas_instance = empresas.objects.create(
                cod_empresa = cod_empresa,
                razao       = razao,
                cnpj        = cnpj,
                fantasia    = fantasia,
                grp_empresa = q_grpempresa, 
                cliente     = self.q_cleinte,
                cert        = Cert_obj,
                )
            empresas_instance.save()

            self._registrar_log(type='S', id='S001', Values='Empresa: '+cod_empresa)
        except GrpEmpresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Cert.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')  

#--------------------------------------------------------------------------------
#           SET - Cliente
#--------------------------------------------------------------------------------
    def set_cliente(self, cod_cliente, razao, cnpj):
        self.Retorn = []
        try:
            cliente_instance = clientes.objects.create(
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
                
            self._registrar_log(type='S', id='S001', Values='Cliente: '+cod_cliente)
        except clientes.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Solucoes.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except IntegrityError:
            self._registrar_log(type='E', id='E004',msg=f"Erro: Cliente já existe.")
        except Exception as e:
            self._registrar_log(type='E', id='E000')
    
#********************************************************************************
#--------------------------------------------------------------------------------
#           ALTER - alterações
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#           ALTER - Certificado
#--------------------------------------------------------------------------------
    def alter_certificado(self, raiz, cert_file, emissor, cnpj, dt_inicial,dt_fim ):
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

            self._registrar_log(type='S', id='S002', Values='Certificado: '+raiz)
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004',msg=f"Erro: {str(e)}")
        except Cert.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except ValueError as e:
            self._registrar_log(type='E', id='E003', msg=f"Erro: {str(e)}")
        except OperationalError as e:
            self._registrar_log(type='E', id='E002', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')
        
#--------------------------------------------------------------------------------
#           ALTER - Usuario
#--------------------------------------------------------------------------------
    def alter_usuario(self, id, Senha,firstName, lastName, Email, is_active):
        self.Retorn = []
        try:
            if Senha == "" or Senha is None:
                created = User.objects.update_or_create(
                    id=id,
                    defaults={
                        'first_name': firstName,
                        'last_name': lastName,
                        'email': Email,
                        'is_active': is_active 
                    }
                )
            else:
                created = User.objects.update_or_create(
                    id=id,
                    defaults={
                        'password': make_password(Senha),
                        'first_name': firstName,
                        'last_name': lastName,
                        'email': Email,
                        'is_active': is_active 
                    }
                )
            self._registrar_log(type='S', id='S002', Values='Usuario: '+firstName)
        except User.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000', msg=f"Erro: {str(e)}")
    
#--------------------------------------------------------------------------------
#           ALTER - Cliente
#--------------------------------------------------------------------------------
    def alter_cliente(self, id_cliente, razao, cnpj):   
        self.Retorn = []
        try:
            created = clientes.objects.update_or_create(
                cod_cliente=id_cliente,
                defaults={
                    'razao': razao,
                    'cnpj': cnpj
                }
            )

            self._registrar_log(type='S', id='S002', Values='Cliente: '+id_cliente)
        except clientes.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')
        
#--------------------------------------------------------------------------------
#           ALTER - Empresa
#--------------------------------------------------------------------------------
    def alter_empresa(self, cod_empresa, cnpj, razao, fantasia, ie, im, tipo,
                        matriz, crt, cnae, iest, suframa, grp_empresa, chave_acesso):
        self.Retorn = []
        try:
            q_grpempresa = GrpEmpresas.objects.get(grp_empresa=grp_empresa)

            created = empresas.objects.update_or_create(
            cod_empresa=cod_empresa,
            defaults={
                'cnpj': cnpj,
                'razao': razao,
                'fantasia': fantasia,
                'ie': ie,
                'im': im,
                'tipo': tipo,
                'matriz': matriz,
                'crt': crt,
                'cnae': cnae,
                'iest': iest,
                'suframa': suframa,
                'grp_empresa': q_grpempresa,
                'chave_acesso': chave_acesso,
            })
            
            self._registrar_log(type='S', id='S002', Values='Cliente: '+cod_empresa)
        except GrpEmpresas.DoesNotExist:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')

        
        return self.Retorn

#********************************************************************************
#--------------------------------------------------------------------------------
#           DEL - DELETAR
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#           DEL - Usuario Grupo
#--------------------------------------------------------------------------------
    def del_userGruop(self, grp_name, User_id):
        self.Retorn = []
        try:
            q_user = AuthUser.objects.get(id=User_id)
            Q_group = AuthGroup.objects.filter(name=grp_name).first()
            user_group = AuthUserGroups.objects.get(group_id=Q_group.id, user_id=q_user.id)
            
            #delete the user from the group
            user_group.delete()

            self._registrar_log(type='S', id='S003', Values='Grupo: '+grp_name)
        except AuthUserGroups.DoesNotExist:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except AuthUser.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except AuthGroup.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
        except IntegrityError as e:
            self._registrar_log(type='E', id='E004', msg=f"Erro: {str(e)}")
        except Exception as e:
            self._registrar_log(type='E', id='E000')

#--------------------------------------------------------------------------------
#           registrar log interno
#--------------------------------------------------------------------------------
    def _registrar_log(self, type, id, msg=None, Values=None):
        self.Retorn = []

        # Verifica se há mensagem no JSON
        #msg_json = self.log_codes.get(id)

        # Prioridade: JSON > mensagem passada > fallback padrão
        mensagem = msg_json or "Erro não especificado."

        self.Retorn.append({
                        "type": type,
                        "id": id,
                        "msg": mensagem,
                        "Values": Values or {}
                        })
        
        return self.Retorn