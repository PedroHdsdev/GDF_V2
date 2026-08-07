from django.db import migrations


COD_SUBSOLUCAO = "Con_Fiscal_Material"
DESC_SUBSOLUCAO = "Consulta Fiscal Material"


def _get_solucao_ferramentas(Solucao, Subsolucao):
    sol = Solucao.objects.filter(descricao="Ferramentas").first()
    if sol:
        return sol

    sub_confronto = (
        Subsolucao.objects.filter(cod_subsolucao="Confronto_Sped_Xml")
        .select_related("solucao")
        .first()
    )
    if sub_confronto and sub_confronto.solucao:
        return sub_confronto.solucao

    sub_rfc = (
        Subsolucao.objects.filter(cod_subsolucao="Int_Rfc")
        .select_related("solucao")
        .first()
    )
    if sub_rfc and sub_rfc.solucao:
        return sub_rfc.solucao

    return None


def aplicar(apps, schema_editor):
    Solucao = apps.get_model("app", "Solucao")
    Subsolucao = apps.get_model("app", "Subsolucao")

    sol_ferramentas = _get_solucao_ferramentas(Solucao, Subsolucao)
    if not sol_ferramentas:
        return

    sub = Subsolucao.objects.filter(cod_subsolucao=COD_SUBSOLUCAO).first()
    if sub:
        changed_fields = []
        if sub.solucao_id != sol_ferramentas.pk:
            sub.solucao = sol_ferramentas
            changed_fields.append("solucao")
        if (sub.descricao or "").strip() != DESC_SUBSOLUCAO:
            sub.descricao = DESC_SUBSOLUCAO
            changed_fields.append("descricao")
        if changed_fields:
            sub.save(update_fields=changed_fields)
        return

    Subsolucao.objects.create(
        cod_subsolucao=COD_SUBSOLUCAO,
        descricao=DESC_SUBSOLUCAO,
        solucao=sol_ferramentas,
    )


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao=COD_SUBSOLUCAO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0093_rename_clientegdf_table_to_mandante"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
