"""
Carga de arquivos SPED (EFD ICMS/IPI, EFD Contribuições, etc.).
Mesma linha de raciocínio da Carga XML: parâmetros, diretório, jobs.
O processamento completo dos blocos SPED pode ser implementado posteriormente.
"""
from pathlib import Path
from typing import Dict, List
from django.utils import timezone


class Carga_sped:
    """Processador de carga de arquivos SPED. Estrutura alinhada à Carga XML."""

    EXTENSOES_SPED = ('.txt',)

    def __init__(self):
        pass

    def set_upload_sped(
        self,
        arquivos: List,
        tipo_sped: str,
        usuario: str,
        cod_cliente: str,
    ) -> Dict:
        """
        Recebe arquivos SPED enviados (File objects).
        Valida extensão e tamanho; retorna resumo de sucesso/erro.
        O parsing dos blocos pode ser implementado depois.
        """
        success = []
        errors = []
        for f in arquivos:
            if not f.name:
                errors.append({'file': '(sem nome)', 'error': 'Arquivo sem nome'})
                continue
            nome = f.name
            if not any(nome.lower().endswith(ext) for ext in self.EXTENSOES_SPED):
                errors.append({'file': nome, 'error': 'Arquivo deve ser .txt (SPED)'})
                continue
            if f.size > 50 * 1024 * 1024:
                errors.append({'file': nome, 'error': 'Arquivo muito grande (máx 50MB)'})
                continue
            try:
                # Por enquanto apenas registra como recebido; processamento pode gravar em tabelas depois
                f.read()
                f.seek(0)
                success.append(nome)
            except Exception as e:
                errors.append({'file': nome, 'error': str(e)})
        return {
            'success': success,
            'errors': errors,
            'pendentes': [],
        }

    def listar_arquivos_diretorio(self, diretorio: str) -> List[str]:
        """Lista arquivos .txt no diretório (para job automático)."""
        path = Path(diretorio)
        if not path.is_dir():
            return []
        return [p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() == '.txt']
