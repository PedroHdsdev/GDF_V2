# -*- coding: utf-8 -*-
"""
Comando: python manage.py diagnostico_reprocessamento --competencia 2022-08 [--empresa COD]

Diagnóstico para reprocessamento: lista SPED e NF-e disponíveis para a competência/empresa.
Útil quando o confronto retorna vazio e não se sabe se falta SPED, XML ou há problema de vínculo.
"""
from django.core.management.base import BaseCommand
from datetime import datetime


class Command(BaseCommand):
    help = 'Diagnóstico SPED e NF-e para reprocessamento (competência e empresa).'

    def add_arguments(self, parser):
        parser.add_argument('--competencia', required=True, help='Competência YYYY-MM (ex: 2022-08)')
        parser.add_argument('--empresa', help='Código da empresa (opcional; se omitido, lista todas)')

    def handle(self, *args, **options):
        from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Reg_C100, Sped_Reg_0000
        from app.db_GDF.NFe.models import NFe
        from app.db_GDF.Public.models import Empresas

        comp_str = options['competencia'].strip()
        try:
            dt = datetime.strptime(comp_str + '-01', '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write(self.style.ERROR(f'Competência inválida: {comp_str}. Use YYYY-MM.'))
            return

        cod_empresa = options.get('empresa')
        empresas = Empresas.objects.all()
        if cod_empresa:
            empresas = empresas.filter(cod_empresa=cod_empresa)
        if not empresas.exists():
            self.stderr.write(self.style.ERROR(f'Empresa não encontrada: {cod_empresa}'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n=== Diagnóstico reprocessamento {comp_str} ===\n'))

        for emp in empresas:
            self.stdout.write(f'\nEmpresa: {emp.cod_empresa} - {emp.fantasia or emp.razao}')
            self.stdout.write(f'  CNPJ: {emp.cnpj}')

            # SPED (Fiscal e Contribuições — ambos têm C100 com chaves NF-e)
            arqs = Sped_Arquivo.objects.filter(
                empresa=emp,
                tipo__in=['F', 'C'],
                competencia__year=dt.year,
                competencia__month=dt.month,
            )
            arqs_sem_emp = Sped_Arquivo.objects.filter(
                empresa__isnull=True,
                tipo__in=['F', 'C'],
                competencia__year=dt.year,
                competencia__month=dt.month,
            )
            cnpj_emp = (emp.cnpj or '').replace('.', '').replace('/', '').replace('-', '')[:14]
            ids_match_cnpj = []
            for a in arqs_sem_emp:
                r = Sped_Reg_0000.objects.filter(arquivo=a).first()
                if r and r.cnpj:
                    cnpj_a = (r.cnpj or '').replace('.', '').replace('/', '').replace('-', '')[:14]
                    if cnpj_a == cnpj_emp:
                        ids_match_cnpj.append(a.id_arquivo)

            total_sped = arqs.count() + len(ids_match_cnpj)
            self.stdout.write(f'  SPED (empresa vinculada): {arqs.count()} arquivo(s)')
            for a in arqs:
                n_c100 = Sped_Reg_C100.objects.filter(arquivo=a).count()
                self.stdout.write(f'    - id={a.id_arquivo} competencia={a.competencia} C100={n_c100}')
            if ids_match_cnpj:
                self.stdout.write(f'  SPED (empresa=None, CNPJ match): {len(ids_match_cnpj)} arquivo(s)')
                for aid in ids_match_cnpj:
                    a = Sped_Arquivo.objects.get(id_arquivo=aid)
                    n_c100 = Sped_Reg_C100.objects.filter(arquivo=a).count()
                    self.stdout.write(f'    - id={a.id_arquivo} competencia={a.competencia} C100={n_c100}')

            # NF-e
            nfe_count = NFe.objects.filter(
                empresa_id=emp.cod_empresa,
                identificacao__emissao__year=dt.year,
                identificacao__emissao__month=dt.month,
            ).count()
            nfe_sem_emp = NFe.objects.filter(
                empresa__isnull=True,
                identificacao__emissao__year=dt.year,
                identificacao__emissao__month=dt.month,
            ).count()
            self.stdout.write(f'  NF-e (empresa vinculada): {nfe_count}')
            if nfe_sem_emp:
                self.stdout.write(self.style.WARNING(f'  NF-e sem empresa no mês: {nfe_sem_emp} (não entram no confronto)'))

            if total_sped == 0 and nfe_count == 0:
                self.stdout.write(self.style.WARNING('  >>> Nenhum SPED nem NF-e. Confronto ficará vazio.'))

        self.stdout.write('')
