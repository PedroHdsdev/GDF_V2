# Remove coluna duplicada: uma única condição SAP (condicao_pagamento_sap)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0029_condicao_pagamento_lote'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='condicaopagamentolote',
            name='condicao_pagamento_sap_retorno',
        ),
    ]
