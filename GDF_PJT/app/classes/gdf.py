#from django.contrib.auth.models     import User, Group
from django.db.models               import Prefetch
from django.utils.timezone          import now
from psycopg2                       import IntegrityError
from django.conf                    import settings
from app.models                     import AuthUser, Empresas, Clientes, Cert
from app.models                     import AuthGroup, AuthUserGroups, GrupoCliente, GrpEmpresas 
from app.models                     import Solucoes, Subsolucoes, SolucoesAcesso, SubsolucoesAcesso
from datetime                       import datetime
from django.db.utils                import OperationalError
from django.contrib.auth.hashers    import make_password
import os
import json

class cl_Gdf():
    #log_codes_path = os.path.join(
    #os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    #    'json',
    #    'log_codes.json'
    #)
    
    #with open(log_codes_path, encoding='utf-8') as f:
    #    log_codes = json.load(f)
    
    def __init__(self):
        self.q_user             = None
        self.q_cleinte          = None
        self.q_Empresas         = None
        self.q_grpempresa       = None
        self.q_Groups           = None
        self.q_subAcesso        = None
        self.q_solucaoAcesso    = None
        self.Retorn             = []

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
            self.q_user = AuthUser.objects.get(id=I_User.id, username=I_User.username, is_active=True)
            
            # Empresas do usuário
            self.q_Empresas = Empresas.objects.filter(
                userempresas__user=self.q_user
            ).distinct()
            
            # Grupos do usuário
            self.q_Groups = AuthGroup.objects.filter(
                authusergroups__user=self.q_user
            )

            # Cliente associado às empresas do usuário
            self.q_cleinte = Clientes.objects.filter(
                empresas__in=self.q_Empresas
            ).distinct().first()

            # Soluções liberadas para o cliente
            self.solucoes_acesso = SolucoesAcesso.objects.filter(
                clientess=self.q_cleinte,
                is_active=True
            ).select_related('solucoes')
            print(self.solucoes_acesso)

            # Subsoluções liberadas via grupo
            self.subsolucoes_acesso = SubsolucoesAcesso.objects.filter(
                group__in=self.q_Groups
            ).select_related('subsolucoes')
            print(self.subsolucoes_acesso)
        
        except Empresas.DoesNotExist as e:
            #self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            print(str(e))
        except Clientes.DoesNotExist as e:
            #self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            print(str(e))
        except GrpEmpresas.DoesNotExist as e:
            #self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            print(str(e))
        except SolucoesAcesso.DoesNotExist as e:
            #self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            print(str(e))
        except SubsolucoesAcesso.DoesNotExist as e:
            #self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            print(str(e))
        except OperationalError as e:
            #self._registrar_log(type='E', id='E002', msg=f"Erro: {str(e)}")
            print(str(e))
        except Exception as e:
            #self._registrar_log(type='E', id='E000', msg=f"Erro: {str(e)}")
            print(str(e))
#--------------------------------------------------------------------------------
#           Gerar - Token JWT (Dashboard) 
#--------------------------------------------------------------------------------

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
            #self._registrar_log(type='E', id='E002', msg=f"Erro: {str(e)}")
            return []
        except OperationalError as e:
            #self._registrar_log(type='E', id='E003', msg=f"Erro: {str(e)}")
            return []
        except Exception as e:
            #self._registrar_log(type='E', id='E000')
            return []

#--------------------------------------------------------------------------------
#           GET - Usuarios
#--------------------------------------------------------------------------------
    def get_usuarios(self):
        self.Retorn = []
        try:
            usuarios_data  = []
            empresa_data   = []
            grpacesso_data = []

            if not self.q_cleinte:
                self._registrar_log(type='E', id='E001', Values='Cliente')
                return [], [], []

            # Buscar todas as empresas vinculadas aos clientes acessíveis
            q_empresas = Empresas.objects.filter(cliente=self.q_cleinte).distinct()
            empresas_ids = list(q_empresas.values_list('cod_empresa', flat=True))

            # Filtra usuários vinculados às empresas
            user_ids = Empresas.user.through.objects.filter(
                empresas_id__in=empresas_ids
             ).values_list('user_id', flat=True)

            usuarios = AuthUser.objects.filter(id__in=user_ids).distinct()

            # Pega o primeiro cod_empresa por usuário
            user_emp_map = {}
            vinculos = Empresas.user.through.objects.filter(
                empresas_id__in=empresas_ids,
                user_id__in=usuarios.values_list('id', flat=True)
            )
            
            # Mapeia nome dos grupos
            grupo_map = {g.id: g.name for g in AuthGroup.objects.all()}

            # Mapeia os grupos dos usuários
            user_group_map = {}
            user_grupos = AuthUserGroups.objects.filter(user_id__in=user_ids)
            for ug in user_grupos:
                nome_grupo = grupo_map.get(ug.group_id)
                if nome_grupo:
                    user_group_map.setdefault(ug.user_id, []).append(nome_grupo)

            for v in vinculos:
                if v.user_id not in user_emp_map:
                    user_emp_map[v.user_id] = v.empresas_id  # primeiro cod_empresa

            for usuario in usuarios:
                user_dict = {
                    "id": usuario.id,
                    "username": usuario.username,
                    "first_name": usuario.first_name,
                    "last_name": usuario.last_name,
                    "email": usuario.email,
                    "is_active": usuario.is_active,
                    "date_joined": usuario.date_joined,
                    "empresa_id": user_emp_map.get(usuario.id),
                }

                # Adiciona grupos somente se houver
                grupos_usuario = user_group_map.get(usuario.id)
                if grupos_usuario:
                    user_dict["groups"] = grupos_usuario
                    

                usuarios_data.append(user_dict)
            
            # Buscar todas empresas vinculadas ao cliente
            empresa_data = Empresas.objects.filter(cliente=self.q_cleinte).distinct()
            
            # Buscar grupos de acesso vinculados aos usuários
            grpacesso_data = GrupoCliente.objects.filter(cliente=self.q_cleinte).distinct()
        
        except Empresas.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            return [], [], []
        except AuthGroup.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            return [], [], []
        except AuthUser.DoesNotExist as e:
            self._registrar_log(type='E', id='E001', msg=f"Erro: {str(e)}")
            return [], [], []
        except Exception as e:
            self._registrar_log(type='E', id='E000')
            return [], [], []
        
        return usuarios_data, empresa_data, grpacesso_data

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