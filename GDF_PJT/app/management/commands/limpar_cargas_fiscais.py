# -*- coding: utf-8 -*-
"""
Comando: python manage.py limpar_cargas_fiscais

Remove todas as cargas de NFe, SPED, CTe, NFSe e as tabelas de log/job
(CargaXmlJob, CargaSpedJob, CargaXmlParam, CargaSpedParam).
Ordem de exclusão respeitando FKs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Remove todas as cargas de NFe, SPED, CTe, NFSe e tabelas de log/job (CargaXml e CargaSped).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não pedir confirmação (útil para scripts).',
        )

    def handle(self, *args, **options):
        from app.db_GDF.Public.models import CargaXmlJob, CargaSpedJob, CargaXmlParam, CargaSpedParam
        from app.db_GDF.NFe.models import (
            NFe_DocumentoItem, NFe_Documento, NFe,
            NFe_Identificacao, NFe_Emitente, NFe_Destinatario, NFe_Endereco,
        )
        from app.db_GDF.CTe.models import (
            CTe, CTe_Carga, CTe_Servico, CTe_Valor, CTe_Transporte,
            CTe_Veiculo, CTe_Motorista, CTe_Percurso, CTe_Fiscal,
            CTe_Identificacao, CTe_Emitente, CTe_Destinatario, CTe_Endereco,
        )
        from app.db_GDF.NFSe.models import (
            NFSe, NFSe_Identificacao, NFSe_Prestador, NFSe_Tomador, NFSe_Endereco,
        )
        from app.db_GDF.Sped.models import (
            Sped_Arquivo,
            Sped_Reg_C170, Sped_Reg_C190, Sped_Reg_D100, Sped_Reg_C100,
            Sped_Reg_C001, Sped_Reg_0005, Sped_Reg_0150, Sped_Reg_0190, Sped_Reg_0200,
            Sped_Reg_0001, Sped_Reg_0000, Sped_Registro,
        )

        if not options.get('no_input'):
            confirm = input('Confirma exclusão de TODAS as cargas (NFe, SPED, CTe, NFSe) e jobs/params? [y/N]: ')
            if (confirm or 'n').lower() != 'y':
                self.stdout.write('Operação cancelada.')
                return

        with transaction.atomic():
            # 1) Jobs e parâmetros de carga (log/job)
            self.stdout.write('Removendo jobs e parâmetros de carga XML e SPED...')
            n = CargaXmlJob.objects.count()
            CargaXmlJob.objects.all().delete()
            self.stdout.write(f'  CargaXmlJob: {n} registro(s) removido(s).')
            n = CargaSpedJob.objects.count()
            CargaSpedJob.objects.all().delete()
            self.stdout.write(f'  CargaSpedJob: {n} registro(s) removido(s).')
            n = CargaXmlParam.objects.count()
            CargaXmlParam.objects.all().delete()
            self.stdout.write(f'  CargaXmlParam: {n} registro(s) removido(s).')
            n = CargaSpedParam.objects.count()
            CargaSpedParam.objects.all().delete()
            self.stdout.write(f'  CargaSpedParam: {n} registro(s) removido(s).')

            # 2) NFe (ordem: itens doc -> documento -> NFe -> identificação [cascade produtos/total/transporte/etc] -> emitente/dest/endereco)
            self.stdout.write('Removendo NFe...')
            n = NFe_DocumentoItem.objects.count()
            NFe_DocumentoItem.objects.all().delete()
            self.stdout.write(f'  NFe_DocumentoItem: {n}.')
            n = NFe_Documento.objects.count()
            NFe_Documento.objects.all().delete()
            self.stdout.write(f'  NFe_Documento: {n}.')
            n = NFe.objects.count()
            NFe.objects.all().delete()
            self.stdout.write(f'  NFe: {n}.')
            n = NFe_Identificacao.objects.count()
            NFe_Identificacao.objects.all().delete()
            self.stdout.write(f'  NFe_Identificacao: {n}.')
            n = NFe_Emitente.objects.count()
            NFe_Emitente.objects.all().delete()
            self.stdout.write(f'  NFe_Emitente: {n}.')
            n = NFe_Destinatario.objects.count()
            NFe_Destinatario.objects.all().delete()
            self.stdout.write(f'  NFe_Destinatario: {n}.')
            n = NFe_Endereco.objects.count()
            NFe_Endereco.objects.all().delete()
            self.stdout.write(f'  NFe_Endereco: {n}.')

            # 3) CTe
            self.stdout.write('Removendo CTe...')
            n = CTe.objects.count()
            CTe.objects.all().delete()
            self.stdout.write(f'  CTe: {n}.')
            for model, name in [
                (CTe_Carga, 'CTe_Carga'), (CTe_Servico, 'CTe_Servico'), (CTe_Valor, 'CTe_Valor'),
                (CTe_Transporte, 'CTe_Transporte'), (CTe_Veiculo, 'CTe_Veiculo'),
                (CTe_Motorista, 'CTe_Motorista'), (CTe_Percurso, 'CTe_Percurso'), (CTe_Fiscal, 'CTe_Fiscal'),
            ]:
                c = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'  {name}: {c}.')
            n = CTe_Identificacao.objects.count()
            CTe_Identificacao.objects.all().delete()
            self.stdout.write(f'  CTe_Identificacao: {n}.')
            n = CTe_Emitente.objects.count()
            CTe_Emitente.objects.all().delete()
            self.stdout.write(f'  CTe_Emitente: {n}.')
            n = CTe_Destinatario.objects.count()
            CTe_Destinatario.objects.all().delete()
            self.stdout.write(f'  CTe_Destinatario: {n}.')
            n = CTe_Endereco.objects.count()
            CTe_Endereco.objects.all().delete()
            self.stdout.write(f'  CTe_Endereco: {n}.')

            # 4) NFSe
            self.stdout.write('Removendo NFSe...')
            n = NFSe.objects.count()
            NFSe.objects.all().delete()
            self.stdout.write(f'  NFSe: {n}.')
            n = NFSe_Identificacao.objects.count()
            NFSe_Identificacao.objects.all().delete()
            self.stdout.write(f'  NFSe_Identificacao: {n}.')
            n = NFSe_Prestador.objects.count()
            NFSe_Prestador.objects.all().delete()
            self.stdout.write(f'  NFSe_Prestador: {n}.')
            n = NFSe_Tomador.objects.count()
            NFSe_Tomador.objects.all().delete()
            self.stdout.write(f'  NFSe_Tomador: {n}.')
            n = NFSe_Endereco.objects.count()
            NFSe_Endereco.objects.all().delete()
            self.stdout.write(f'  NFSe_Endereco: {n}.')

            # 5) SPED (regs que referenciam outros regs primeiro, depois arquivo)
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
                self.stdout.write(f'  {name}: {c}.')
            n = Sped_Arquivo.objects.count()
            Sped_Arquivo.objects.all().delete()
            self.stdout.write(f'  Sped_Arquivo: {n}.')

        self.stdout.write(self.style.SUCCESS('Limpeza concluída.'))
