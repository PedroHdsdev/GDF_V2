# -*- coding: utf-8 -*-
"""
Comando: python manage.py backfill_sped_reg_0000

Preenche sped_reg_0000 para Sped_Arquivo que têm registro em sped_arquivo
mas não têm correspondente em sped_reg_0000. Usa dados de Sped_Registro
(registro='0000') quando disponível, ou re-lê o arquivo se não houver.

Útil após correção que passou a gravar 0000 também para SPED Contribuição.
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

    def handle(self, *args, **options):
        from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Reg_0000, Sped_Registro

        dry_run = options.get('dry_run', False)
        if dry_run:
            self.stdout.write('Modo dry-run: nenhuma alteração será feita.')

        # Arquivos que não têm reg_0000
        ids_com_0000 = set(
            Sped_Reg_0000.objects.values_list('arquivo_id', flat=True).distinct()
        )
        arquivos_sem_0000 = Sped_Arquivo.objects.exclude(id_arquivo__in=ids_com_0000)
        total = arquivos_sem_0000.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Todos os arquivos SPED já têm sped_reg_0000.'))
            return

        self.stdout.write(f'Arquivos sem sped_reg_0000: {total}')

        criados = 0
        sem_dados = 0

        for arq in arquivos_sem_0000:
            # Tentar obter 0000 de Sped_Registro
            reg0000 = Sped_Registro.objects.filter(
                arquivo=arq, registro='0000'
            ).first()

            if reg0000 and reg0000.campos:
                campos = reg0000.campos
                cnpj_raw = (campos.get('6') or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]

                if not dry_run:
                    Sped_Reg_0000.objects.create(
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
                self.stdout.write(f'  OK: {arq.nome_arquivo} (id={arq.id_arquivo}) - criado a partir de Sped_Registro')
            else:
                sem_dados += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  Sem dados: {arq.nome_arquivo} (id={arq.id_arquivo}) - '
                        'não há Sped_Registro 0000. Recarregue o arquivo SPED.'
                    )
                )

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Criados {criados} registros sped_reg_0000.'))
        else:
            self.stdout.write(f'Seriam criados {criados} registros.')

        if sem_dados:
            self.stdout.write(
                self.style.WARNING(
                    f'{sem_dados} arquivo(s) sem dados de 0000 em Sped_Registro - '
                    'recarregue esses arquivos para preencher.'
                )
            )
