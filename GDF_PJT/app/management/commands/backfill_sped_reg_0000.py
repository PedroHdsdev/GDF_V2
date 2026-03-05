# -*- coding: utf-8 -*-
"""
Comando: python manage.py backfill_sped_reg_0000

Preenche sped_reg_0000 para arquivos SPED (fiscal e contribuição) que não têm registro 0000.
Usa dados de SpedRegistro (registro='0000') quando disponível.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime


class Command(BaseCommand):
    help = 'Preenche sped_reg_0000 para arquivos SPED que não têm registro 0000.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista o que seria feito, sem gravar.',
        )

    def _p_date(self, s):
        """Converte string DDMMAAAA ou AAAAMMDD em date."""
        if not s or len(s) != 8 or not s.isdigit():
            return None
        try:
            return datetime.strptime(s, '%d%m%Y').date()
        except ValueError:
            try:
                return datetime.strptime(s, '%Y%m%d').date()
            except ValueError:
                pass
        return None

    def _processar(self, Arquivo, Reg_0000, Registro, dry_run):
        ids_com_0000 = set(Reg_0000.objects.values_list('arquivo_id', flat=True).distinct())
        arquivos_sem_0000 = Arquivo.objects.exclude(id_arquivo__in=ids_com_0000)
        criados = 0
        sem_dados = 0

        for arq in arquivos_sem_0000:
            reg0000 = Registro.objects.filter(arquivo=arq, registro='0000').first()

            if reg0000 and reg0000.campos:
                campos = reg0000.campos
                cnpj_raw = (campos.get('6') or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]

                if not dry_run:
                    Reg_0000.objects.create(
                        arquivo=arq,
                        linha=reg0000.linha,
                        cod_ver=(campos.get('1') or '')[:3],
                        cod_fin=(campos.get('2') or '')[:1],
                        dt_ini=self._p_date(campos.get('3') or ''),
                        dt_fin=self._p_date(campos.get('4') or ''),
                        nome=(campos.get('5') or '')[:100],
                        cnpj=cnpj_raw or None,
                        cpf=(campos.get('7') or '')[:11],
                        uf=(campos.get('8') or '')[:2],
                        ie=(campos.get('9') or '')[:14],
                        cod_mun=(campos.get('10') or '')[:7],
                        im=(campos.get('11') or '')[:15],
                        suframa=(campos.get('12') or '')[:9],
                        ind_perfil=(campos.get('13') or '')[:1],
                        ind_ativ=(campos.get('14') or '')[:1],
                    )

                criados += 1
                self.stdout.write(f'  OK: {arq.nome_arquivo} (id={arq.id_arquivo}) - criado a partir de SpedRegistro')
            else:
                sem_dados += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  Sem dados: {arq.nome_arquivo} (id={arq.id_arquivo}) - '
                        'não há SpedRegistro 0000. Recarregue o arquivo SPED.'
                    )
                )

        return criados, sem_dados

    def handle(self, *args, **options):
        from app.db_GDF.sped_fiscal.models import (
            SpedFiscalArquivo, SpedFiscalReg_0000, SpedFiscalRegistro,
        )
        from app.db_GDF.sped_contribuicao.models import (
            SpedContribuicaoArquivo, SpedContribuicaoReg_0000, SpedContribuicaoRegistro,
        )

        dry_run = options.get('dry_run', False)
        if dry_run:
            self.stdout.write('Modo dry-run: nenhuma alteração será feita.')

        criados_f, sem_f = self._processar(SpedFiscalArquivo, SpedFiscalReg_0000, SpedFiscalRegistro, dry_run)
        self.stdout.write('---')
        criados_c, sem_c = self._processar(SpedContribuicaoArquivo, SpedContribuicaoReg_0000, SpedContribuicaoRegistro, dry_run)

        criados = criados_f + criados_c
        sem_dados = sem_f + sem_c

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Criados {criados} registros sped_reg_0000.'))
        else:
            self.stdout.write(f'Seriam criados {criados} registros.')

        if sem_dados:
            self.stdout.write(
                self.style.WARNING(
                    f'{sem_dados} arquivo(s) sem dados de 0000 em SpedRegistro - '
                    'recarregue esses arquivos para preencher.'
                )
            )
