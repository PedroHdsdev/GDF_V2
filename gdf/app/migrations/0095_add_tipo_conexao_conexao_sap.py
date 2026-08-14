from django.db import migrations, models


def backfill_tipo_conexao(apps, schema_editor):
    ConexaoSap = apps.get_model('app', 'ConexaoSap')
    ConexaoSap.objects.filter(tipo_conexao__isnull=True).update(tipo_conexao='RFC')
    ConexaoSap.objects.filter(tipo_conexao='').update(tipo_conexao='RFC')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0094_add_subsolucao_consulta_fiscal_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='conexaosap',
            name='tipo_conexao',
            field=models.CharField(
                choices=[('RFC', 'RFC'), ('REST', 'REST')],
                default='RFC',
                max_length=4,
            ),
        ),
        migrations.RunPython(backfill_tipo_conexao, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='conexaosap',
            index=models.Index(fields=['gdfcliente', 'tipo_conexao', 'active'], name='conexao_sap_gdf_tipo_24f592_idx'),
        ),
    ]
