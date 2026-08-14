# Subsolução Int_Rfc (RFC SAP) passa a ficar sob a solução Ferramentas (com Reproc_Painel).
# Mescla acesso de cliente: quem tinha a solução "Integração" (Int) precisa de Ferramentas
# após a mudança. Remove a solução Int se ficar vazia.

from django.db import migrations


def _mesclar_is_active(a, b):
    if a is True or b is True:
        return True
    if a is False and b is False:
        return False
    return a if b is None else (b if a is None else None)


def aplicar(apps, schema_editor):
    Solucao = apps.get_model("app", "Solucao")
    Subsolucao = apps.get_model("app", "Subsolucao")
    AcessoSolucaoCliente = apps.get_model("app", "AcessoSolucaoCliente")

    sub_reproc = (
        Subsolucao.objects.filter(cod_subsolucao="Reproc_Painel")
        .select_related("solucao")
        .first()
    )
    sub_rfc = (
        Subsolucao.objects.filter(cod_subsolucao="Int_Rfc")
        .select_related("solucao")
        .first()
    )
    if not sub_reproc or not sub_reproc.solucao or not sub_rfc or not sub_rfc.solucao:
        return
    sol_ferramentas = sub_reproc.solucao
    sol_int = sub_rfc.solucao
    if str(sol_int.pk) == str(sol_ferramentas.pk):
        return

    for ac in AcessoSolucaoCliente.objects.filter(solucao=sol_int).select_related(
        "gdfcliente"
    ):
        ex, criado = AcessoSolucaoCliente.objects.get_or_create(
            gdfcliente_id=ac.gdfcliente_id,
            solucao_id=sol_ferramentas.pk,
            defaults={"is_active": ac.is_active},
        )
        if not criado:
            m = _mesclar_is_active(ex.is_active, ac.is_active)
            if m != ex.is_active:
                ex.is_active = m
                ex.save(update_fields=["is_active"])

    AcessoSolucaoCliente.objects.filter(solucao_id=sol_int.pk).delete()

    sub_rfc.solucao = sol_ferramentas
    sub_rfc.save(update_fields=["solucao"])

    if not Subsolucao.objects.filter(solucao_id=sol_int.pk).exists():
        Solucao.objects.filter(pk=sol_int.pk).delete()


def reverter(apps, schema_editor):
    """Recria solução Int, recoloca Int_Rfc; não desfaz merge de acesso a cliente (irreversível de forma fiel)."""
    Solucao = apps.get_model("app", "Solucao")
    Subsolucao = apps.get_model("app", "Subsolucao")

    sol_int, _ = Solucao.objects.get_or_create(
        cod_solucao="Int",
        defaults={"descricao": "Integração"},
    )
    sub = Subsolucao.objects.filter(cod_subsolucao="Int_Rfc").select_related("solucao").first()
    if sub and sub.solucao_id and str(sub.solucao_id) != "Int":
        sub.solucao = sol_int
        sub.save(update_fields=["solucao"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0078_solucao_reprocessamento_para_ferramentas"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
