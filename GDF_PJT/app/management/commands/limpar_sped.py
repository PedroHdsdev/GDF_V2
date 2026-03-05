# -*- coding: utf-8 -*-
"""
Comando: python manage.py limpar_sped

Remove todos os dados das tabelas SPED (sped_fiscal e sped_contribuicao).
Ordem de exclusão respeitando FKs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Remove todos os dados das tabelas SPED (fiscal e contribuição).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não pedir confirmação (útil para scripts).',
        )

    def handle(self, *args, **options):
        from app.db_GDF.sped_fiscal.models import (
            SpedFiscalArquivo, SpedFiscalReg_C170, SpedFiscalReg_C190, SpedFiscalReg_D100,
            SpedFiscalReg_C100, SpedFiscalReg_C001, SpedFiscalReg_0005, SpedFiscalReg_0150,
            SpedFiscalReg_0190, SpedFiscalReg_0200, SpedFiscalReg_0001, SpedFiscalReg_0000,
            SpedFiscalRegistro,
        )
        from app.db_GDF.sped_contribuicao.models import (
            SpedContribuicaoArquivo, SpedContribuicaoReg_C170, SpedContribuicaoReg_C190,
            SpedContribuicaoReg_D100, SpedContribuicaoReg_C100, SpedContribuicaoReg_C001,
            SpedContribuicaoReg_0005, SpedContribuicaoReg_0150, SpedContribuicaoReg_0190,
            SpedContribuicaoReg_0200, SpedContribuicaoReg_0001, SpedContribuicaoReg_0000,
            SpedContribuicaoRegistro,
        )

        if not options.get('no_input'):
            confirm = input('Confirma exclusão de TODOS os dados SPED (fiscal + contribuição)? [y/N]: ')
            if (confirm or 'n').lower() != 'y':
                self.stdout.write('Operação cancelada.')
                return

        with transaction.atomic():
            self.stdout.write('Removendo SPED Fiscal...')
            for model, name in [
                (SpedFiscalReg_C170, 'SpedFiscalReg_C170'), (SpedFiscalReg_C190, 'SpedFiscalReg_C190'),
                (SpedFiscalReg_D100, 'SpedFiscalReg_D100'), (SpedFiscalReg_C100, 'SpedFiscalReg_C100'),
                (SpedFiscalReg_C001, 'SpedFiscalReg_C001'), (SpedFiscalReg_0005, 'SpedFiscalReg_0005'),
                (SpedFiscalReg_0150, 'SpedFiscalReg_0150'), (SpedFiscalReg_0190, 'SpedFiscalReg_0190'),
                (SpedFiscalReg_0200, 'SpedFiscalReg_0200'), (SpedFiscalReg_0001, 'SpedFiscalReg_0001'),
                (SpedFiscalReg_0000, 'SpedFiscalReg_0000'), (SpedFiscalRegistro, 'SpedFiscalRegistro'),
            ]:
                c = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'  {name}: {c} registro(s) removido(s).')
            n = SpedFiscalArquivo.objects.count()
            SpedFiscalArquivo.objects.all().delete()
            self.stdout.write(f'  SpedFiscalArquivo: {n} registro(s) removido(s).')

            self.stdout.write('Removendo SPED Contribuição...')
            for model, name in [
                (SpedContribuicaoReg_C170, 'SpedContribuicaoReg_C170'), (SpedContribuicaoReg_C190, 'SpedContribuicaoReg_C190'),
                (SpedContribuicaoReg_D100, 'SpedContribuicaoReg_D100'), (SpedContribuicaoReg_C100, 'SpedContribuicaoReg_C100'),
                (SpedContribuicaoReg_C001, 'SpedContribuicaoReg_C001'), (SpedContribuicaoReg_0005, 'SpedContribuicaoReg_0005'),
                (SpedContribuicaoReg_0150, 'SpedContribuicaoReg_0150'), (SpedContribuicaoReg_0190, 'SpedContribuicaoReg_0190'),
                (SpedContribuicaoReg_0200, 'SpedContribuicaoReg_0200'), (SpedContribuicaoReg_0001, 'SpedContribuicaoReg_0001'),
                (SpedContribuicaoReg_0000, 'SpedContribuicaoReg_0000'), (SpedContribuicaoRegistro, 'SpedContribuicaoRegistro'),
            ]:
                c = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'  {name}: {c} registro(s) removido(s).')
            n = SpedContribuicaoArquivo.objects.count()
            SpedContribuicaoArquivo.objects.all().delete()
            self.stdout.write(f'  SpedContribuicaoArquivo: {n} registro(s) removido(s).')

        self.stdout.write(self.style.SUCCESS('Limpeza SPED concluída.'))
