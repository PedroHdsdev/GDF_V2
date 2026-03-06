# -*- coding: utf-8 -*-
"""
Comando: python manage.py associar_sped_empresa

Associa empresa aos arquivos SPED (fiscal e contribuição) que têm empresa=None,
usando o CNPJ do registro 0000 para buscar a Empresas correspondente.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Associa empresa aos arquivos SPED sem empresa, usando CNPJ do registro 0000.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista o que seria feito, sem gravar.',
        )

    def _processar_arquivos(self, Arquivo, Reg_0000, dry_run):
        from app.db_GDF.Public.models import Empresa

        arquivos_sem_empresa = Arquivo.objects.filter(empresa__isnull=True)
        atualizados = 0
        sem_cnpj = 0
        empresa_nao_encontrada = 0

        for arq in arquivos_sem_empresa:
            reg0000 = Reg_0000.objects.filter(arquivo=arq).first()
            if not reg0000 or not reg0000.cnpj:
                sem_cnpj += 1
                self.stdout.write(
                    self.style.WARNING(f'  Sem CNPJ: {arq.nome_arquivo} (id={arq.id_arquivo})')
                )
                continue

            cnpj = (reg0000.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
            if len(cnpj) < 14:
                sem_cnpj += 1
                continue

            empresa = Empresas.objects.filter(cnpj=cnpj).first()
            if not empresa:
                empresa_nao_encontrada += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  Empresa não encontrada (CNPJ {cnpj}): {arq.nome_arquivo} (id={arq.id_arquivo})'
                    )
                )
                continue

            if not dry_run:
                arq.empresa = empresa
                arq.save(update_fields=['empresa'])

            atualizados += 1
            self.stdout.write(f'  OK: {arq.nome_arquivo} → {empresa.cod_empresa} ({empresa.fantasia or empresa.razao})')

        return atualizados, sem_cnpj, empresa_nao_encontrada

    def handle(self, *args, **options):
        from app.db_GDF.sped_fiscal.models import (
            SpedFiscalArquivo, SpedFiscalReg_0000,
        )
        from app.db_GDF.sped_contribuicao.models import (
            SpedContribuicaoArquivo, SpedContribuicaoReg_0000,
        )

        dry_run = options.get('dry_run', False)
        if dry_run:
            self.stdout.write('Modo dry-run: nenhuma alteração será feita.')

        total = SpedFiscalArquivo.objects.filter(empresa__isnull=True).count()
        total += SpedContribuicaoArquivo.objects.filter(empresa__isnull=True).count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Todos os arquivos SPED já têm empresa associada.'))
            return

        self.stdout.write(f'Arquivos SPED sem empresa: {total}')

        at_f, sc_f, en_f = self._processar_arquivos(SpedFiscalArquivo, SpedFiscalReg_0000, dry_run)
        self.stdout.write('---')
        at_c, sc_c, en_c = self._processar_arquivos(SpedContribuicaoArquivo, SpedContribuicaoReg_0000, dry_run)

        atualizados = at_f + at_c
        sem_cnpj = sc_f + sc_c
        empresa_nao_encontrada = en_f + en_c

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Atualizados {atualizados} arquivos SPED.'))
        else:
            self.stdout.write(f'Seriam atualizados {atualizados} arquivos.')

        if sem_cnpj or empresa_nao_encontrada:
            self.stdout.write(
                self.style.WARNING(
                    f'{sem_cnpj} sem CNPJ; {empresa_nao_encontrada} com CNPJ sem empresa cadastrada. '
                    'Cadastre a empresa em Clientes/Empresas para que apareça no relatório.'
                )
            )
