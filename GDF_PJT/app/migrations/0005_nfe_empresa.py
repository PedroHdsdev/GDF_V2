# Generated manually on 2026-01-28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_nfe_endereco_nfe_emitente_nfe_destinatario_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfe',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nfe_docs', to='app.empresas'),
        ),
        migrations.AddIndex(
            model_name='nfe',
            index=models.Index(fields=['empresa'], name='nfe_empresa_idx'),
        ),
    ]
