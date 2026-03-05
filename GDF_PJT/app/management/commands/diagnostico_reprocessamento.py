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
        from app.db_GDF.sped_fiscal.models import (
            SpedFiscalArquivo, SpedFiscalReg_C100, SpedFiscalReg_0000,
        )
        from app.db_GDF.sped_contribuicao.models import (
            SpedContribuicaoArquivo, SpedContribuicaoReg_C100, SpedContribuicaoReg_0000,
        )
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

            arqs_f = SpedFiscalArquivo.objects.filter(empresa=emp, competencia__year=dt.year, competencia__month=dt.month)
            arqs_c = SpedContribuicaoArquivo.objects.filter(empresa=emp, competencia__year=dt.year, competencia__month=dt.month)
            arqs_sem_f = SpedFiscalArquivo.objects.filter(empresa__isnull=True, competencia__year=dt.year, competencia__month=dt.month)
            arqs_sem_c = SpedContribuicaoArquivo.objects.filter(empresa__isnull=True, competencia__year=dt.year, competencia__month=dt.month)
            cnpj_emp = (emp.cnpj or '').replace('.', '').replace('/', '').replace('-', '')[:14]
            ids_match = []
            for a in arqs_sem_f:
                r = SpedFiscalReg_0000.objects.filter(arquivo=a).first()
                if r and r.cnpj:
                    cnpj_a = (r.cnpj or '').replace('.', '').replace('/', '').replace('-', '')[:14]
                    if cnpj_a == cnpj_emp:
                        ids_match.append(('F', a.id_arquivo))
            for a in arqs_sem_c:
                r = SpedContribuicaoReg_0000.objects.filter(arquivo=a).first()
                if r and r.cnpj:
                    cnpj_a = (r.cnpj or '').replace('.', '').replace('/', '').replace('-', '')[:14]
                    if cnpj_a == cnpj_emp:
                        ids_match.append(('C', a.id_arquivo))

            total_sped = arqs_f.count() + arqs_c.count() + len(ids_match)
            self.stdout.write(f'  SPED Fiscal (empresa vinculada): {arqs_f.count()} arquivo(s)')
            for a in arqs_f:
                n_c100 = SpedFiscalReg_C100.objects.filter(arquivo=a).count()
                self.stdout.write(f'    - id={a.id_arquivo} competencia={a.competencia} C100={n_c100}')
            self.stdout.write(f'  SPED Contribuição (empresa vinculada): {arqs_c.count()} arquivo(s)')
            for a in arqs_c:
                n_c100 = SpedContribuicaoReg_C100.objects.filter(arquivo=a).count()
                self.stdout.write(f'    - id={a.id_arquivo} competencia={a.competencia} C100={n_c100}')
            if ids_match:
                self.stdout.write(f'  SPED (empresa=None, CNPJ match): {len(ids_match)} arquivo(s)')
                for tipo, aid in ids_match:
                    if tipo == 'F':
                        a = SpedFiscalArquivo.objects.get(id_arquivo=aid)
                        n_c100 = SpedFiscalReg_C100.objects.filter(arquivo=a).count()
                    else:
                        a = SpedContribuicaoArquivo.objects.get(id_arquivo=aid)
                        n_c100 = SpedContribuicaoReg_C100.objects.filter(arquivo=a).count()
                    self.stdout.write(f'    - [{tipo}] id={a.id_arquivo} competencia={a.competencia} C100={n_c100}')

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
