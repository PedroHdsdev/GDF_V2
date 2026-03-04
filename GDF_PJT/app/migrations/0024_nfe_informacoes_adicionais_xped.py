# Campo xPed (número do pedido de compra) em dados adicionais da NFe

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_nfe_icms_cst_max_length_3'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfe_informacoes_adicionais',
            name='xped',
            field=models.CharField(blank=True, help_text='Número do pedido de compra (tag xPed do XML)', max_length=60, null=True),
        ),
    ]
