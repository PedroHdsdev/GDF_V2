from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0085_create_all_missing_tables"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelTable(
                    name="empresas",
                    table="empresas",
                ),
            ],
        ),
    ]
