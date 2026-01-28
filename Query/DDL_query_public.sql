-- Relacionamentos / tabelas de junção
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS user_empresas CASCADE;
DROP TABLE IF EXISTS subsolucoes_acesso CASCADE;
DROP TABLE IF EXISTS solucoes_acesso CASCADE;
DROP TABLE IF EXISTS grupo_cliente CASCADE;

-- Tabelas principais de domínio
DROP TABLE IF EXISTS subsolucoes CASCADE;
DROP TABLE IF EXISTS solucoes CASCADE;
DROP TABLE IF EXISTS empresas CASCADE;
DROP TABLE IF EXISTS grp_empresas CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS cert CASCADE;

-- Django auth
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;

-- Django system tables (recomendado para reset total)
DROP TABLE IF EXISTS django_admin_log CASCADE;
DROP TABLE IF EXISTS django_content_type CASCADE;
DROP TABLE IF EXISTS django_migrations CASCADE;
DROP TABLE IF EXISTS django_session CASCADE;

DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;

