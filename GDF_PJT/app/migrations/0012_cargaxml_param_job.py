from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_rename_nfe_doc_nfe_3fb2bf_idx_nfe_documen_nfe_id_143e75_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CargaXmlParam',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('ativo', models.BooleanField(default=True)),
                ('horario', models.TimeField()),
                ('origem_dados', models.CharField(choices=[('LOCAL', 'Maquina Local'), ('SAP', 'Importacao SAP'), ('SPED', 'Importacao SPED'), ('OUTROS', 'Outros')], default='LOCAL', max_length=10)),
                ('diretorio', models.CharField(max_length=500)),
                ('modelos', models.CharField(blank=True, max_length=200, null=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('ultima_execucao', models.DateTimeField(blank=True, null=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.clientes')),
                ('usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cargaxml_params', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'managed': True,
                'db_table': 'cargaxml_param',
            },
        ),
        migrations.CreateModel(
            name='CargaXmlJob',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('RUNNING', 'Executando'), ('SUCCESS', 'Sucesso'), ('ERROR', 'Erro')], default='PENDING', max_length=10)),
                ('total_arquivos', models.IntegerField(default=0)),
                ('total_sucesso', models.IntegerField(default=0)),
                ('total_erro', models.IntegerField(default=0)),
                ('mensagem', models.TextField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.clientes')),
                ('parametro', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.cargaxmlparam')),
                ('usuario_execucao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cargaxml_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'managed': True,
                'db_table': 'cargaxml_job',
            },
        ),
        migrations.AddIndex(
            model_name='cargaxmlparam',
            index=models.Index(fields=['cliente', 'ativo'], name='cargaxml_pa_cliente_33e08f_idx'),
        ),
        migrations.AddIndex(
            model_name='cargaxmljob',
            index=models.Index(fields=['cliente', 'status'], name='cargaxml_jo_cliente_5f0b4a_idx'),
        ),
    ]
