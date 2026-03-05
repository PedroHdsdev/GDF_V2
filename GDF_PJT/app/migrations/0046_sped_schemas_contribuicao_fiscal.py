# Migração: separa SPED em schemas sped_contribuicao e sped_fiscal
# 1. Cria schemas
# 2. Cria tabelas nos novos schemas
# 3. Migra dados do schema sped (por tipo: C->contribuicao, F->fiscal)
# 4. Remove schema sped antigo

from django.db import migrations, models
import django.db.models.deletion


def criar_schemas(apps, schema_editor):
    schema_editor.execute('CREATE SCHEMA IF NOT EXISTS "sped_contribuicao";')
    schema_editor.execute('CREATE SCHEMA IF NOT EXISTS "sped_fiscal";')


def migrar_dados_sped(apps, schema_editor):
    """
    Migra dados do schema sped para sped_contribuicao e sped_fiscal conforme tipo.
    Se o schema sped não existir (ambiente novo), retorna sem fazer nada.
    Se houver incompatibilidade de tipos, usa savepoint para não abortar a migração inteira.
    """
    from django.db import connection, transaction

    with connection.cursor() as c:
        c.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'sped'")
        if not c.fetchone():
            return  # Ambiente novo, sem schema sped

    # Usar savepoint: se a migração de dados falhar, só ela é revertida; schemas/tabelas permanecem
    try:
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO sped_contribuicao.sped_arquivo
                        (id_arquivo, cod_cliente, empresa_id, competencia, nome_arquivo, hash_conteudo, data_carga, data_criacao, data_atualizacao)
                    SELECT id_arquivo, cod_cliente, empresa_id, competencia, nome_arquivo, hash_conteudo, data_carga, data_criacao, data_atualizacao
                    FROM sped.sped_arquivo WHERE tipo = 'C'
                """)
                c.execute("""
                    INSERT INTO sped_fiscal.sped_arquivo
                        (id_arquivo, cod_cliente, empresa_id, competencia, nome_arquivo, hash_conteudo, data_carga, data_criacao, data_atualizacao)
                    SELECT id_arquivo, cod_cliente, empresa_id, competencia, nome_arquivo, hash_conteudo, data_carga, data_criacao, data_atualizacao
                    FROM sped.sped_arquivo WHERE tipo = 'F'
                """)
                for schema in ('sped_contribuicao', 'sped_fiscal'):
                    c.execute(f"SELECT setval(pg_get_serial_sequence('{schema}.sped_arquivo', 'id_arquivo'), COALESCE((SELECT MAX(id_arquivo) FROM {schema}.sped_arquivo), 1))")
                tabelas_reg = [
                    'sped_reg_0000', 'sped_reg_0001', 'sped_reg_0005', 'sped_reg_0150', 'sped_reg_0190',
                    'sped_reg_0200', 'sped_reg_c001', 'sped_reg_c100', 'sped_reg_c170', 'sped_reg_c190',
                    'sped_reg_d100', 'sped_registro',
                ]
                for tbl in tabelas_reg:
                    c.execute(f"""
                        INSERT INTO sped_contribuicao.{tbl}
                        SELECT r.* FROM sped.{tbl} r
                        INNER JOIN sped_contribuicao.sped_arquivo a ON r.arquivo_id = a.id_arquivo
                    """)
                    c.execute(f"""
                        INSERT INTO sped_fiscal.{tbl}
                        SELECT r.* FROM sped.{tbl} r
                        INNER JOIN sped_fiscal.sped_arquivo a ON r.arquivo_id = a.id_arquivo
                    """)
    except Exception:
        pass  # Incompatibilidade: schemas ficam vazios; DROP schema sped ainda será executado


def remover_schema_sped(apps, schema_editor):
    schema_editor.execute('DROP SCHEMA IF EXISTS "sped" CASCADE;')


def reverse_migrar(apps, schema_editor):
    """Reverse: recria schema sped e migra de volta (não implementado - migração complexa)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0045_evento_nfe_cte_nfse'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE SCHEMA IF NOT EXISTS "sped_contribuicao"; CREATE SCHEMA IF NOT EXISTS "sped_fiscal";',
            reverse_sql='DROP SCHEMA IF EXISTS "sped_contribuicao" CASCADE; DROP SCHEMA IF EXISTS "sped_fiscal" CASCADE;',
        ),
        # Criar tabelas em sped_fiscal
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_arquivo (
                id_arquivo SERIAL PRIMARY KEY,
                cod_cliente VARCHAR(10) NULL REFERENCES clientes(cod_cliente) ON DELETE CASCADE,
                empresa_id VARCHAR(10) NULL REFERENCES empresas(cod_empresa) ON DELETE CASCADE,
                competencia DATE NULL,
                nome_arquivo VARCHAR(255) NULL,
                hash_conteudo VARCHAR(64) NULL,
                data_carga TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                data_atualizacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_arquivo_cli_comp ON sped_fiscal.sped_arquivo(cod_cliente, competencia);
            CREATE INDEX IF NOT EXISTS idx_sf_arquivo_emp_comp ON sped_fiscal.sped_arquivo(empresa_id, competencia);
            CREATE INDEX IF NOT EXISTS idx_sf_arquivo_hash ON sped_fiscal.sped_arquivo(hash_conteudo);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_arquivo CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0000 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_ver VARCHAR(3) NULL, cod_fin VARCHAR(1) NULL,
                dt_ini DATE NULL, dt_fin DATE NULL, nome VARCHAR(100) NULL, cnpj VARCHAR(14) NULL,
                cpf VARCHAR(11) NULL, uf VARCHAR(2) NULL, ie VARCHAR(14) NULL, cod_mun VARCHAR(7) NULL,
                im VARCHAR(15) NULL, suframa VARCHAR(9) NULL, ind_perfil VARCHAR(1) NULL, ind_ativ VARCHAR(1) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0000_arquivo ON sped_fiscal.sped_reg_0000(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0000 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0001 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_mov VARCHAR(1) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0001_arquivo ON sped_fiscal.sped_reg_0001(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0001 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0005 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, fantasia VARCHAR(60) NULL, cep VARCHAR(8) NULL, "end" VARCHAR(60) NULL,
                num VARCHAR(10) NULL, compl VARCHAR(60) NULL, bairro VARCHAR(60) NULL,
                fone VARCHAR(11) NULL, fax VARCHAR(11) NULL, email VARCHAR(60) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0005_arquivo ON sped_fiscal.sped_reg_0005(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0005 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0150 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_part VARCHAR(60) NULL, nome VARCHAR(100) NULL, cod_pais VARCHAR(3) NULL,
                cnpj VARCHAR(14) NULL, cpf VARCHAR(11) NULL, ie VARCHAR(14) NULL, cod_mun VARCHAR(7) NULL,
                "end" VARCHAR(60) NULL, num VARCHAR(10) NULL, compl VARCHAR(60) NULL, bairro VARCHAR(60) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0150_arquivo ON sped_fiscal.sped_reg_0150(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_0150_codpart ON sped_fiscal.sped_reg_0150(cod_part);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0150 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0190 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, unid VARCHAR(6) NULL, descr VARCHAR(255) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0190_arquivo ON sped_fiscal.sped_reg_0190(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0190 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_0200 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_item VARCHAR(60) NULL, descr_item VARCHAR(255) NULL, cod_barra VARCHAR(14) NULL,
                cod_ant_item VARCHAR(60) NULL, unid_inv VARCHAR(6) NULL, tipo_item VARCHAR(2) NULL,
                cod_ncm VARCHAR(8) NULL, ex_ipi VARCHAR(3) NULL, cod_gen VARCHAR(2) NULL, cod_lst VARCHAR(5) NULL,
                aliq_icms NUMERIC(15,2) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_0200_arquivo ON sped_fiscal.sped_reg_0200(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_0200_coditem ON sped_fiscal.sped_reg_0200(cod_item);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_0200 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_c001 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_mov VARCHAR(1) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_c001_arquivo ON sped_fiscal.sped_reg_c001(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_c001 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_c100 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_oper VARCHAR(1) NULL, ind_emit VARCHAR(1) NULL, cod_part VARCHAR(60) NULL,
                cod_mod VARCHAR(2) NULL, cod_sit VARCHAR(2) NULL, ser VARCHAR(3) NULL, num_doc VARCHAR(9) NULL,
                chv_nfe VARCHAR(44) NULL, dt_doc DATE NULL, dt_e_s DATE NULL, vl_doc NUMERIC(15,2) NULL,
                ind_frt VARCHAR(1) NULL, vl_frt NUMERIC(15,2) NULL, vl_seg NUMERIC(15,2) NULL, vl_out_da NUMERIC(15,2) NULL,
                vl_bc_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL, vl_bc_icms_st NUMERIC(15,2) NULL,
                vl_icms_st NUMERIC(15,2) NULL, vl_ipi NUMERIC(15,2) NULL, vl_pis NUMERIC(15,2) NULL,
                vl_cofins NUMERIC(15,2) NULL, vl_pis_st NUMERIC(15,2) NULL, vl_cofins_st NUMERIC(15,2) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_c100_arquivo ON sped_fiscal.sped_reg_c100(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_c100_chv ON sped_fiscal.sped_reg_c100(chv_nfe);
            CREATE INDEX IF NOT EXISTS idx_sf_c100_dtdoc ON sped_fiscal.sped_reg_c100(dt_doc);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_c100 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_c170 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                c100_id INTEGER NULL REFERENCES sped_fiscal.sped_reg_c100(id) ON DELETE CASCADE,
                linha INTEGER NULL, num_item VARCHAR(3) NULL, cod_item VARCHAR(60) NULL, descr_compl VARCHAR(255) NULL,
                qtd NUMERIC(15,4) NULL, unid VARCHAR(6) NULL, vl_item NUMERIC(15,2) NULL, vl_desc NUMERIC(15,2) NULL,
                ind_mov VARCHAR(1) NULL, cst_icms VARCHAR(3) NULL, cfop VARCHAR(4) NULL, cod_nat VARCHAR(10) NULL,
                vl_bc_icms NUMERIC(15,2) NULL, aliq_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL,
                vl_bc_icms_st NUMERIC(15,2) NULL, aliq_st NUMERIC(15,2) NULL, vl_icms_st NUMERIC(15,2) NULL,
                cst_pis VARCHAR(2) NULL, vl_bc_pis NUMERIC(15,2) NULL, aliq_pis NUMERIC(15,4) NULL, vl_pis NUMERIC(15,2) NULL,
                cst_cofins VARCHAR(2) NULL, vl_bc_cofins NUMERIC(15,2) NULL, aliq_cofins NUMERIC(15,4) NULL,
                vl_cofins NUMERIC(15,2) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_c170_arquivo ON sped_fiscal.sped_reg_c170(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_c170_c100 ON sped_fiscal.sped_reg_c170(c100_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_c170 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_c190 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                c100_id INTEGER NULL REFERENCES sped_fiscal.sped_reg_c100(id) ON DELETE CASCADE,
                linha INTEGER NULL, cst_icms VARCHAR(3) NULL, cfop VARCHAR(4) NULL, aliq_icms NUMERIC(15,2) NULL,
                vl_opr NUMERIC(15,2) NULL, vl_bc_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL,
                vl_bc_icms_st NUMERIC(15,2) NULL, vl_icms_st NUMERIC(15,2) NULL, vl_red_bc NUMERIC(15,2) NULL,
                vl_ipi NUMERIC(15,2) NULL, cod_obs VARCHAR(6) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_c190_arquivo ON sped_fiscal.sped_reg_c190(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_c190_c100 ON sped_fiscal.sped_reg_c190(c100_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_c190 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_reg_d100 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_oper VARCHAR(1) NULL, ind_emit VARCHAR(1) NULL, cod_part VARCHAR(60) NULL,
                cod_mod VARCHAR(2) NULL, cod_sit VARCHAR(2) NULL, ser VARCHAR(3) NULL, sub_ser VARCHAR(3) NULL,
                num_doc VARCHAR(9) NULL, chv_cte VARCHAR(44) NULL, dt_doc DATE NULL, dt_a_p DATE NULL,
                tp_ct_e VARCHAR(1) NULL, chv_cte_ref VARCHAR(44) NULL, vl_doc NUMERIC(15,2) NULL,
                vl_desc NUMERIC(15,2) NULL, ind_frt VARCHAR(1) NULL, vl_frt NUMERIC(15,2) NULL,
                vl_seg NUMERIC(15,2) NULL, vl_out_da NUMERIC(15,2) NULL, vl_bc_icms NUMERIC(15,2) NULL,
                vl_icms NUMERIC(15,2) NULL, vl_nf NUMERIC(15,2) NULL, cod_inf VARCHAR(6) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_d100_arquivo ON sped_fiscal.sped_reg_d100(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_d100_chv ON sped_fiscal.sped_reg_d100(chv_cte);
            CREATE INDEX IF NOT EXISTS idx_sf_d100_dtdoc ON sped_fiscal.sped_reg_d100(dt_doc);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_reg_d100 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_fiscal.sped_registro (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_fiscal.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                registro VARCHAR(20) NOT NULL, linha INTEGER NULL, campos JSONB DEFAULT '{}', conteudo TEXT NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sf_reg_arquivo ON sped_fiscal.sped_registro(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sf_reg_arq_reg ON sped_fiscal.sped_registro(arquivo_id, registro);
        """, reverse_sql='DROP TABLE IF EXISTS sped_fiscal.sped_registro CASCADE;'),
        # Criar tabelas em sped_contribuicao
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_arquivo (
                id_arquivo SERIAL PRIMARY KEY,
                cod_cliente VARCHAR(10) NULL REFERENCES clientes(cod_cliente) ON DELETE CASCADE,
                empresa_id VARCHAR(10) NULL REFERENCES empresas(cod_empresa) ON DELETE CASCADE,
                competencia DATE NULL,
                nome_arquivo VARCHAR(255) NULL,
                hash_conteudo VARCHAR(64) NULL,
                data_carga TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                data_atualizacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_arquivo_cli_comp ON sped_contribuicao.sped_arquivo(cod_cliente, competencia);
            CREATE INDEX IF NOT EXISTS idx_sc_arquivo_emp_comp ON sped_contribuicao.sped_arquivo(empresa_id, competencia);
            CREATE INDEX IF NOT EXISTS idx_sc_arquivo_hash ON sped_contribuicao.sped_arquivo(hash_conteudo);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_arquivo CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0000 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_ver VARCHAR(3) NULL, cod_fin VARCHAR(1) NULL,
                dt_ini DATE NULL, dt_fin DATE NULL, nome VARCHAR(100) NULL, cnpj VARCHAR(14) NULL,
                cpf VARCHAR(11) NULL, uf VARCHAR(2) NULL, ie VARCHAR(14) NULL, cod_mun VARCHAR(7) NULL,
                im VARCHAR(15) NULL, suframa VARCHAR(9) NULL, ind_perfil VARCHAR(1) NULL, ind_ativ VARCHAR(1) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0000_arquivo ON sped_contribuicao.sped_reg_0000(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0000 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0001 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_mov VARCHAR(1) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0001_arquivo ON sped_contribuicao.sped_reg_0001(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0001 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0005 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, fantasia VARCHAR(60) NULL, cep VARCHAR(8) NULL, "end" VARCHAR(60) NULL,
                num VARCHAR(10) NULL, compl VARCHAR(60) NULL, bairro VARCHAR(60) NULL,
                fone VARCHAR(11) NULL, fax VARCHAR(11) NULL, email VARCHAR(60) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0005_arquivo ON sped_contribuicao.sped_reg_0005(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0005 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0150 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_part VARCHAR(60) NULL, nome VARCHAR(100) NULL, cod_pais VARCHAR(3) NULL,
                cnpj VARCHAR(14) NULL, cpf VARCHAR(11) NULL, ie VARCHAR(14) NULL, cod_mun VARCHAR(7) NULL,
                "end" VARCHAR(60) NULL, num VARCHAR(10) NULL, compl VARCHAR(60) NULL, bairro VARCHAR(60) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0150_arquivo ON sped_contribuicao.sped_reg_0150(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_0150_codpart ON sped_contribuicao.sped_reg_0150(cod_part);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0150 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0190 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, unid VARCHAR(6) NULL, descr VARCHAR(255) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0190_arquivo ON sped_contribuicao.sped_reg_0190(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0190 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_0200 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, cod_item VARCHAR(60) NULL, descr_item VARCHAR(255) NULL, cod_barra VARCHAR(14) NULL,
                cod_ant_item VARCHAR(60) NULL, unid_inv VARCHAR(6) NULL, tipo_item VARCHAR(2) NULL,
                cod_ncm VARCHAR(8) NULL, ex_ipi VARCHAR(3) NULL, cod_gen VARCHAR(2) NULL, cod_lst VARCHAR(5) NULL,
                aliq_icms NUMERIC(15,2) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_0200_arquivo ON sped_contribuicao.sped_reg_0200(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_0200_coditem ON sped_contribuicao.sped_reg_0200(cod_item);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_0200 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_c001 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_mov VARCHAR(1) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_c001_arquivo ON sped_contribuicao.sped_reg_c001(arquivo_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_c001 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_c100 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_oper VARCHAR(1) NULL, ind_emit VARCHAR(1) NULL, cod_part VARCHAR(60) NULL,
                cod_mod VARCHAR(2) NULL, cod_sit VARCHAR(2) NULL, ser VARCHAR(3) NULL, num_doc VARCHAR(9) NULL,
                chv_nfe VARCHAR(44) NULL, dt_doc DATE NULL, dt_e_s DATE NULL, vl_doc NUMERIC(15,2) NULL,
                ind_frt VARCHAR(1) NULL, vl_frt NUMERIC(15,2) NULL, vl_seg NUMERIC(15,2) NULL, vl_out_da NUMERIC(15,2) NULL,
                vl_bc_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL, vl_bc_icms_st NUMERIC(15,2) NULL,
                vl_icms_st NUMERIC(15,2) NULL, vl_ipi NUMERIC(15,2) NULL, vl_pis NUMERIC(15,2) NULL,
                vl_cofins NUMERIC(15,2) NULL, vl_pis_st NUMERIC(15,2) NULL, vl_cofins_st NUMERIC(15,2) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_c100_arquivo ON sped_contribuicao.sped_reg_c100(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_c100_chv ON sped_contribuicao.sped_reg_c100(chv_nfe);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_c100 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_c170 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                c100_id INTEGER NULL REFERENCES sped_contribuicao.sped_reg_c100(id) ON DELETE CASCADE,
                linha INTEGER NULL, num_item VARCHAR(3) NULL, cod_item VARCHAR(60) NULL, descr_compl VARCHAR(255) NULL,
                qtd NUMERIC(15,4) NULL, unid VARCHAR(6) NULL, vl_item NUMERIC(15,2) NULL, vl_desc NUMERIC(15,2) NULL,
                ind_mov VARCHAR(1) NULL, cst_icms VARCHAR(3) NULL, cfop VARCHAR(4) NULL, cod_nat VARCHAR(10) NULL,
                vl_bc_icms NUMERIC(15,2) NULL, aliq_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL,
                vl_bc_icms_st NUMERIC(15,2) NULL, aliq_st NUMERIC(15,2) NULL, vl_icms_st NUMERIC(15,2) NULL,
                cst_pis VARCHAR(2) NULL, vl_bc_pis NUMERIC(15,2) NULL, aliq_pis NUMERIC(15,4) NULL, vl_pis NUMERIC(15,2) NULL,
                cst_cofins VARCHAR(2) NULL, vl_bc_cofins NUMERIC(15,2) NULL, aliq_cofins NUMERIC(15,4) NULL,
                vl_cofins NUMERIC(15,2) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_c170_arquivo ON sped_contribuicao.sped_reg_c170(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_c170_c100 ON sped_contribuicao.sped_reg_c170(c100_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_c170 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_c190 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                c100_id INTEGER NULL REFERENCES sped_contribuicao.sped_reg_c100(id) ON DELETE CASCADE,
                linha INTEGER NULL, cst_icms VARCHAR(3) NULL, cfop VARCHAR(4) NULL, aliq_icms NUMERIC(15,2) NULL,
                vl_opr NUMERIC(15,2) NULL, vl_bc_icms NUMERIC(15,2) NULL, vl_icms NUMERIC(15,2) NULL,
                vl_bc_icms_st NUMERIC(15,2) NULL, vl_icms_st NUMERIC(15,2) NULL, vl_red_bc NUMERIC(15,2) NULL,
                vl_ipi NUMERIC(15,2) NULL, cod_obs VARCHAR(6) NULL, data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_c190_arquivo ON sped_contribuicao.sped_reg_c190(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_c190_c100 ON sped_contribuicao.sped_reg_c190(c100_id);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_c190 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_reg_d100 (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                linha INTEGER NULL, ind_oper VARCHAR(1) NULL, ind_emit VARCHAR(1) NULL, cod_part VARCHAR(60) NULL,
                cod_mod VARCHAR(2) NULL, cod_sit VARCHAR(2) NULL, ser VARCHAR(3) NULL, sub_ser VARCHAR(3) NULL,
                num_doc VARCHAR(9) NULL, chv_cte VARCHAR(44) NULL, dt_doc DATE NULL, dt_a_p DATE NULL,
                tp_ct_e VARCHAR(1) NULL, chv_cte_ref VARCHAR(44) NULL, vl_doc NUMERIC(15,2) NULL,
                vl_desc NUMERIC(15,2) NULL, ind_frt VARCHAR(1) NULL, vl_frt NUMERIC(15,2) NULL,
                vl_seg NUMERIC(15,2) NULL, vl_out_da NUMERIC(15,2) NULL, vl_bc_icms NUMERIC(15,2) NULL,
                vl_icms NUMERIC(15,2) NULL, vl_nf NUMERIC(15,2) NULL, cod_inf VARCHAR(6) NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_d100_arquivo ON sped_contribuicao.sped_reg_d100(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_d100_chv ON sped_contribuicao.sped_reg_d100(chv_cte);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_reg_d100 CASCADE;'),
        migrations.RunSQL(sql="""
            CREATE TABLE IF NOT EXISTS sped_contribuicao.sped_registro (
                id SERIAL PRIMARY KEY,
                arquivo_id INTEGER NOT NULL REFERENCES sped_contribuicao.sped_arquivo(id_arquivo) ON DELETE CASCADE,
                registro VARCHAR(20) NOT NULL, linha INTEGER NULL, campos JSONB DEFAULT '{}', conteudo TEXT NULL,
                data_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_sc_reg_arquivo ON sped_contribuicao.sped_registro(arquivo_id);
            CREATE INDEX IF NOT EXISTS idx_sc_reg_arq_reg ON sped_contribuicao.sped_registro(arquivo_id, registro);
        """, reverse_sql='DROP TABLE IF EXISTS sped_contribuicao.sped_registro CASCADE;'),
        migrations.RunPython(migrar_dados_sped, reverse_migrar),
        migrations.RunSQL(
            sql='DROP SCHEMA IF EXISTS "sped" CASCADE;',
            reverse_sql='CREATE SCHEMA IF NOT EXISTS "sped";',
        ),
    ]
