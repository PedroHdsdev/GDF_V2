# Alterar NFe.empresa: PROTECT -> CASCADE (ao apagar cliente/empresa, apaga NFe vinculadas)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_nfe_icms_excecao_tipi_cst_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfe',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='nfe_docs',
                to='app.empresas',
            ),
        ),
    ]
