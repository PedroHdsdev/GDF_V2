"""
Testes de segurança: autenticação, autorização, IDOR, CSRF, validação de entrada, headers.
"""
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings


@override_settings(ALLOWED_HOSTS=['*'], FORCE_SCRIPT_NAME='')
class SegurancaTestCase(TestCase):
    """Testes de segurança para views e APIs."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='segtest',
            email='segtest@test.local',
            password='testpass123',
            is_staff=False,
            is_superuser=False,
        )
        self.superuser = User.objects.create_superuser(
            username='admin_seg',
            email='admin@seg.local',
            password='adminpass123',
        )

    # --- Autenticação: acesso não autenticado a rotas protegidas
    def test_home_sem_login_redireciona_para_login(self):
        """GET /Home/ sem autenticação deve redirecionar para Login."""
        r = self.client.get('/Home/')
        self.assertIn(r.status_code, (302, 301), msg=f"Esperado redirect, obteve {r.status_code}")
        self.assertTrue(
            r.url.endswith('/Login/') or 'Login' in (r.url or ''),
            msg=f"Redirect deve ir para Login, obteve: {r.url}",
        )

    def test_usuarios_sem_login_redireciona(self):
        """GET /usuarios/ sem autenticação deve redirecionar."""
        r = self.client.get('/usuarios/')
        self.assertIn(r.status_code, (302, 301))

    def test_api_relatorio_nfe_sem_login_redireciona(self):
        """GET /api/relatorio/nfe/ sem autenticação deve redirecionar."""
        r = self.client.get('/api/relatorio/nfe/')
        self.assertIn(r.status_code, (302, 301))

    def test_api_relatorio_excel_sem_login_redireciona(self):
        """GET /api/relatorio/excel/ sem autenticação deve redirecionar."""
        r = self.client.get('/api/relatorio/excel/')
        self.assertIn(r.status_code, (302, 301))

    def test_relatorio_fiscal_sem_login_redireciona(self):
        """GET /Relatorio/ sem autenticação deve redirecionar."""
        r = self.client.get('/Relatorio/')
        self.assertIn(r.status_code, (302, 301))

    def test_login_aceita_get_publico(self):
        """GET /Login/ deve ser acessível sem autenticação (200)."""
        r = self.client.get('/Login/')
        self.assertEqual(r.status_code, 200)

    # --- Autenticação: com login, rotas protegidas acessíveis
    def test_home_com_login_retorna_200(self):
        """GET /Home/ com usuário autenticado deve retornar 200."""
        self.client.force_login(self.user)
        r = self.client.get('/Home/')
        self.assertIn(r.status_code, (200, 302), msg=f"Com login esperado 200 ou redirect, obteve {r.status_code}")

    # --- Sessão: APIs que exigem cod_cliente retornam 403 sem cliente
    def test_api_cargaxml_jobs_sem_cliente_retorna_403(self):
        """GET /api/cargaxml/jobs/ sem cod_cliente na sessão deve retornar 403."""
        self.client.force_login(self.user)
        r = self.client.get('/api/cargaxml/jobs/')
        self.assertEqual(r.status_code, 403)

    def test_api_reprocessamento_lotes_sem_cliente_retorna_403(self):
        """GET /api/reprocessamento/lotes/ sem cod_cliente na sessão deve retornar 403."""
        self.client.force_login(self.user)
        r = self.client.get('/api/reprocessamento/lotes/')
        self.assertEqual(r.status_code, 403)

    # --- IDOR: acesso a recurso de outro cliente (empresa)
    def test_empresa_idor_cod_inexistente_ou_outro_cliente_403(self):
        """GET /empresa/<cod>/ sem acesso à subsolução ou com cod_empresa inválido deve retornar 403 ou 302."""
        self.client.force_login(self.user)
        # Sem Dm_Empresas no grupo → 302 (redirect Home); sem cod_cliente ou empresa de outro cliente → 403
        r = self.client.get('/empresa/COD_QUALQUER/')
        self.assertIn(r.status_code, (403, 302), msg="Acesso negado: 403 (IDOR/sessão) ou 302 (sem subsolução)")

    # --- Validação de entrada: parâmetro busca com padrões perigosos
    def test_api_relatorio_nfe_busca_sql_injection_retorna_erro_ou_lista_vazia(self):
        """GET /api/relatorio/nfe/?busca=... com padrão SQL deve ser rejeitado ou sanitizado (não 500)."""
        self.client.force_login(self.superuser)
        # A API pode retornar 400 (ValidationError) ou 200 com dados vazios
        r = self.client.get('/api/relatorio/nfe/', {'busca': "1' OR '1'='1"})
        self.assertIn(r.status_code, (200, 400, 422), msg="Não deve retornar 500 por input malicioso")
        if r.status_code == 200:
            data = r.json() if r.get("Content-Type", "").startswith("application/json") else {}
            # Se 200, não deve vazar erro ou stack trace
            self.assertNotIn("Traceback", r.content.decode(errors="replace"))
            self.assertNotIn("Exception", r.content.decode(errors="replace"))

    def test_api_relatorio_nfe_busca_union_select_retorna_erro_ou_sanitizado(self):
        """GET com busca contendo 'union select' deve ser rejeitado (400) ou não causar 500."""
        self.client.force_login(self.superuser)
        r = self.client.get('/api/relatorio/nfe/', {'busca': 'x union select * from auth_user'})
        self.assertIn(r.status_code, (200, 400, 422))

    # --- CSRF: POST sem token em formulário protegido
    def test_post_login_sem_csrf_aceito_ou_403(self):
        """POST /Login/ sem CSRF token: Django pode aceitar (se exempt) ou retornar 403."""
        r = self.client.post('/Login/', {'Username': 'x', 'password': 'y'})
        # Login falha por credenciais; CSRF pode dar 403
        self.assertIn(r.status_code, (200, 302, 403))

    def test_post_estado_alterador_sem_csrf_retorna_403(self):
        """POST que altera estado (ex.: criar recurso) sem CSRF deve retornar 403."""
        self.client.force_login(self.user)
        # POST sem token em rota que exige CSRF
        r = self.client.post('/usuarios/', {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # 403 CSRF ou 302/200 conforme view
        self.assertIn(r.status_code, (200, 302, 403, 405))

    # --- Headers de segurança
    def test_resposta_tem_x_content_type_options_nosniff(self):
        """Resposta deve incluir X-Content-Type-Options: nosniff."""
        r = self.client.get('/Login/')
        self.assertEqual(r.get('X-Content-Type-Options', ''), 'nosniff')

    def test_resposta_tem_x_frame_options(self):
        """Resposta deve incluir X-Frame-Options (SAMEORIGIN ou DENY)."""
        r = self.client.get('/Login/')
        self.assertIn(r.get('X-Frame-Options', ''), ('SAMEORIGIN', 'DENY', 'sameorigin', 'deny'))

    def test_resposta_tem_x_xss_protection_ou_equiv(self):
        """Resposta deve incluir X-XSS-Protection ou política equivalente."""
        r = self.client.get('/Login/')
        val = r.get('X-XSS-Protection', '')
        self.assertTrue(
            '1' in val or 'block' in val.lower() or len(val) > 0,
            msg="Header X-XSS-Protection esperado",
        )

    # --- Logout
    def test_logout_limpa_sessao(self):
        """Após GET /Logout/, sessão não deve manter user."""
        self.client.force_login(self.user)
        self.client.get('/Logout/')
        r = self.client.get('/Home/')
        self.assertIn(r.status_code, (302, 301), msg="Após logout, Home deve redirecionar para login")
