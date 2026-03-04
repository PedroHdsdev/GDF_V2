# -*- coding: utf-8 -*-
"""
Comando: python manage.py limpar_sped

Remove todos os dados das tabelas SPED (sped_arquivo e registros).
Ordem de exclusão respeitando FKs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Remove todos os dados das tabelas SPED.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não pedir confirmação (útil para scripts).',
        )

    def handle(self, *args, **options):
        from app.db_GDF.Sped.models import (
            Sped_Arquivo,
            Sped_Reg_C170, Sped_Reg_C190, Sped_Reg_D100, Sped_Reg_C100,
            Sped_Reg_C001, Sped_Reg_0005, Sped_Reg_0150, Sped_Reg_0190, Sped_Reg_0200,
            Sped_Reg_0001, Sped_Reg_0000, Sped_Registro,
        )

        if not options.get('no_input'):
            confirm = input('Confirma exclusão de TODOS os dados SPED? [y/N]: ')
            if (confirm or 'n').lower() != 'y':
                self.stdout.write('Operação cancelada.')
                return

        with transaction.atomic():
            self.stdout.write('Removendo SPED...')
            for model, name in [
                (Sped_Reg_C170, 'Sped_Reg_C170'), (Sped_Reg_C190, 'Sped_Reg_C190'),
                (Sped_Reg_D100, 'Sped_Reg_D100'), (Sped_Reg_C100, 'Sped_Reg_C100'),
                (Sped_Reg_C001, 'Sped_Reg_C001'), (Sped_Reg_0005, 'Sped_Reg_0005'),
                (Sped_Reg_0150, 'Sped_Reg_0150'), (Sped_Reg_0190, 'Sped_Reg_0190'),
                (Sped_Reg_0200, 'Sped_Reg_0200'), (Sped_Reg_0001, 'Sped_Reg_0001'),
                (Sped_Reg_0000, 'Sped_Reg_0000'), (Sped_Registro, 'Sped_Registro'),
            ]:
                c = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'  {name}: {c} registro(s) removido(s).')
            n = Sped_Arquivo.objects.count()
            Sped_Arquivo.objects.all().delete()
            self.stdout.write(f'  Sped_Arquivo: {n} registro(s) removido(s).')

        self.stdout.write(self.style.SUCCESS('Limpeza SPED concluída.'))
