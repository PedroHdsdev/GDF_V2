# Merge dos heads: 0001_initial e 0054_reprocessamento_por_grupo.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
        ('app', '0054_reprocessamento_por_grupo'),
    ]

    operations = []
