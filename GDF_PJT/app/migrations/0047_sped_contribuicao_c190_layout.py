# Migração: Ajusta C190 EFD Contribuições para layout correto (COD_ITEM, PIS/COFINS)
# O C190 da Contribuições é "Consolidação por item", diferente do C190 Fiscal (analítico ICMS)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0046_sped_schemas_contribuicao_fiscal'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE sped_contribuicao.sped_reg_c190
                ADD COLUMN IF NOT EXISTS cod_item VARCHAR(60) NULL,
                ADD COLUMN IF NOT EXISTS cst_pis VARCHAR(2) NULL,
                ADD COLUMN IF NOT EXISTS vl_bc_pis NUMERIC(15,2) NULL,
                ADD COLUMN IF NOT EXISTS vl_pis NUMERIC(15,2) NULL,
                ADD COLUMN IF NOT EXISTS cst_cofins VARCHAR(2) NULL,
                ADD COLUMN IF NOT EXISTS vl_bc_cofins NUMERIC(15,2) NULL,
                ADD COLUMN IF NOT EXISTS vl_cofins NUMERIC(15,2) NULL;
            CREATE INDEX IF NOT EXISTS idx_sc_c190_coditem ON sped_contribuicao.sped_reg_c190(cod_item);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS sped_contribuicao.idx_sc_c190_coditem;
            ALTER TABLE sped_contribuicao.sped_reg_c190
                DROP COLUMN IF EXISTS cod_item,
                DROP COLUMN IF EXISTS cst_pis,
                DROP COLUMN IF EXISTS vl_bc_pis,
                DROP COLUMN IF EXISTS vl_pis,
                DROP COLUMN IF EXISTS cst_cofins,
                DROP COLUMN IF EXISTS vl_bc_cofins,
                DROP COLUMN IF EXISTS vl_cofins;
            """,
        ),
    ]
