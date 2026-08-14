# Remove a subsolução legada Pro_Relatorio (relatório fiscal integrou-se a Carga XML / Carga SPED).

from django.db import migrations


def aplicar(apps, schema_editor):
    AcessoSubsolucaoGrupo = apps.get_model("app", "AcessoSubsolucaoGrupo")
    Subsolucao = apps.get_model("app", "Subsolucao")
    pro_rel = Subsolucao.objects.filter(cod_subsolucao="Pro_Relatorio").first()
    if not pro_rel:
        return
    AcessoSubsolucaoGrupo.objects.filter(subsolucao_id=pro_rel.pk).delete()
    pro_rel.delete()


def reverter(apps, schema_editor):
    """Recria Pro_Relatorio na mesma solução que Pro_CargaXml, se possível."""
    Subsolucao = apps.get_model("app", "Subsolucao")
    if Subsolucao.objects.filter(cod_subsolucao="Pro_Relatorio").exists():
        return
    ref = (
        Subsolucao.objects.filter(cod_subsolucao="Pro_CargaXml")
        .select_related("solucao")
        .first()
    )
    if not ref or not ref.solucao_id:
        return
    Subsolucao.objects.create(
        cod_subsolucao="Pro_Relatorio",
        descricao="Relatório fiscal (legado)",
        solucao_id=ref.solucao_id,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0081_remove_carga_automatica_parametros"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
