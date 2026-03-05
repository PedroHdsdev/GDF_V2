# -*- coding: utf-8 -*-
"""
Comando: python manage.py sap_testar_conexao --cliente COD_CLIENTE [--todos]

Testa a conexão SAP para um ou todos os clientes com conexão configurada.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Testa conexão SAP (um cliente ou todos com conexão ativa).'

    def add_arguments(self, parser):
        parser.add_argument('--cliente', help='Código do cliente (ex: CLI001)')
        parser.add_argument('--todos', action='store_true', help='Testar todas as conexões SAP ativas')

    def handle(self, *args, **options):
        from app.classes.SapRfc import SapRfc

        if not SapRfc.is_available():
            self.stderr.write(self.style.ERROR(
                'PyRFC não disponível. Instale o SAP NetWeaver RFC SDK e: pip install pyrfc\n'
                'Ver DOCUMENTACAO_MD/SAP_RFC_SETUP.md'
            ))
            return

        cod_cliente = (options.get('cliente') or '').strip()
        todos = options.get('todos', False)

        if todos:
            conn_list = SapRfc.get_active_connections()
            if not conn_list:
                self.stdout.write(self.style.WARNING('Nenhuma conexão SAP ativa encontrada.'))
                return
            self.stdout.write(self.style.SUCCESS(f'\n=== Testando {len(conn_list)} conexão(ões) SAP ===\n'))
            for conn in conn_list:
                self._testar_uma(conn)
        elif cod_cliente:
            conn = SapRfc.get_connection(cod_cliente)
            if not conn:
                self.stderr.write(self.style.ERROR(
                    f'Nenhuma conexão SAP ativa para o cliente "{cod_cliente}". '
                    'Configure na aba Conexão SAP do cliente.'
                ))
                return
            self._testar_uma(conn)
        else:
            self.stderr.write(self.style.ERROR('Informe --cliente COD ou --todos'))

    def _testar_uma(self, conn):
        cliente_id = getattr(conn.cliente, 'cod_cliente', None) if conn.cliente else '?'
        self.stdout.write(f'Cliente: {cliente_id} | Host: {conn.ashost} | Client: {conn.client} ... ', ending='')
        success, result = SapRfc.call(conn, 'RFC_PING')
        if success:
            self.stdout.write(self.style.SUCCESS('OK'))
        else:
            self.stdout.write(self.style.ERROR(f'FALHOU: {result}'))
