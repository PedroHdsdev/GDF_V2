# Renomeia a tabela física de ClienteGdf para mandante.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0092_alter_clientegdf_verbose_name_mandante"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="clientegdf",
            table="mandante",
        ),
    ]