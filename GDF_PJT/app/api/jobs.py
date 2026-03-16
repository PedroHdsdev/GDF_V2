"""
Jobs em background: Carga XML e Carga SPED.
Executados em thread ou Celery; usam app.classes (CargaXml, CargaSped).
"""
import os
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from django.conf import settings

from app.db_GDF.Public.models import Empresa

# Processar XMLs em chunks para limitar memória; tamanho configurável em settings.CARGAXML_CHUNK_SIZE
def _get_chunk_size():
    return getattr(settings, 'CARGAXML_CHUNK_SIZE', 50)


def processar_job_xml_background(job_id, temp_dir, type_xml, origem_dados, user_id, cod_cliente, empresa_id):
    """Executa em thread/Celery: processa XMLs da pasta temp e atualiza o job."""
    from django.db import connection
    from app.db_GDF.Public.models import JobCargaXml
    from app.classes.CargaXml import CargaXml

    cod_cliente = (cod_cliente or "").strip() or None
    empresa_id = (empresa_id or "").strip() or None

    try:
        from django.contrib.auth.models import User as AuthUser
        job = JobCargaXml.objects.get(id=job_id)
        user = AuthUser.objects.filter(id=user_id).first()
        username = user.username if user else "SYSTEM"

        # Listar apenas caminhos; ler e processar em chunks para não estourar memória
        entries = []
        for fname in sorted(os.listdir(temp_dir)):
            if not fname.lower().endswith(".xml"):
                continue
            path = os.path.join(temp_dir, fname)
            if not os.path.isfile(path):
                continue
            nome = fname.split("_", 1)[-1] if "_" in fname else fname
            entries.append((path, nome))

        if not entries:
            job.status = "ERROR"
            job.mensagem = "Nenhum arquivo XML encontrado na pasta temporária."
            job.finished_at = timezone.localtime()
            job.save(update_fields=["status", "mensagem", "finished_at"])
            return

        type_xml = (type_xml or "NFe").strip() or "NFe"
        origem_dados = (origem_dados or "LOCAL").strip() or "LOCAL"

        merged = {"success": [], "errors": [], "pendentes": [], "avisos": []}
        cl_xml = CargaXml()
        chunk_size = _get_chunk_size()

        total_entries = len(entries)
        for i in range(0, total_entries, chunk_size):
            chunk = entries[i : i + chunk_size]
            xml_files = []
            for path, nome in chunk:
                with open(path, "rb") as f:
                    xml_bytes = f.read()
                xml_files.append(SimpleUploadedFile(nome, xml_bytes))
            result = cl_xml.set_upload_xml(
                xml_files, type_xml, origem_dados, username, cod_cliente
            )
            for key in merged:
                merged[key].extend(result.get(key) or [])

            # Atualizar progresso no job para monitoramento em tempo real
            processed = min(i + len(chunk), total_entries)
            n_ok = len(merged.get("success", []))
            n_err = len(merged.get("errors", []))
            n_pend = len(merged.get("pendentes", []))
            job.mensagem = (
                f"Processando... {processed}/{total_entries} arquivos | "
                f"{n_ok} sucesso, {n_err} erros, {n_pend} pendentes"
            )
            job.total_sucesso = n_ok
            job.total_erro = n_err
            job.save(update_fields=["mensagem", "total_sucesso", "total_erro"])

        mensagem_lines = []
        for err in merged.get("errors", []):
            mensagem_lines.append(f"ERRO: {err.get('file', '')} - {err.get('error', '')}")
        for p in merged.get("pendentes", []):
            mensagem_lines.append(f"PENDENTES (empresa não cadastrada): {p.get('file', '')} - {p.get('motivo', '')}")
        for a in merged.get("avisos", []):
            mensagem_lines.append(f"AVISO: {a.get('file', '')} - {a.get('message', '')}")
        for name in merged.get("success", []):
            mensagem_lines.append(f"OK: {name}")
        resumo = "\n".join(mensagem_lines)[:5000]

        empresa_prefixo = ""
        if empresa_id and cod_cliente:
            try:
                empresa = Empresa.objects.get(
                    cod_empresa=empresa_id,
                    gdfcliente__cod_cliente=cod_cliente,
                )
                nome_emp = empresa.fantasia or empresa.razao or empresa.cod_empresa
                empresa_prefixo = f"EMPRESA: {empresa.cod_empresa} - {nome_emp}\n"
            except Empresa.DoesNotExist:
                empresa_prefixo = f"EMPRESA: {empresa_id} (não encontrada)\n"

        success_list = merged.get("success", [])
        errors_list = merged.get("errors", [])
        pendentes_list = merged.get("pendentes", [])
        total_arquivos = len(success_list) + len(errors_list) + len(pendentes_list)
        job.total_arquivos = total_arquivos
        job.total_sucesso = len(success_list)
        job.total_erro = len(errors_list)
        job.status = "ERROR" if errors_list else "SUCCESS"
        job.mensagem = (empresa_prefixo + resumo)[:5000]
        job.finished_at = timezone.localtime()
        job.save(
            update_fields=[
                "total_arquivos", "total_sucesso", "total_erro",
                "status", "mensagem", "finished_at",
            ]
        )
    except Exception as e:
        try:
            from app.db_GDF.Public.models import JobCargaXml
            job = JobCargaXml.objects.get(id=job_id)
            job.status = "ERROR"
            job.mensagem = str(e)[:5000]
            job.finished_at = timezone.localtime()
            job.save(update_fields=["status", "mensagem", "finished_at"])
        except Exception:
            pass
    finally:
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass


def processar_job_sped_background(job_id, temp_dir, cod_cliente, user_id):
    """Executa em thread: processa arquivos SPED na pasta temp e atualiza o job."""
    from django.db import connection
    from app.db_GDF.Public.models import JobCargaSped, ClienteGdf
    from app.classes.CargaSped import CargaSped

    try:
        job = JobCargaSped.objects.get(id=job_id)
        ClienteGdf.objects.get(cod_cliente=cod_cliente)
        cl_sped = CargaSped()
        result = cl_sped.processar_pasta_temp(temp_dir, cod_cliente, empresa=None)
        total = len(result["success"]) + len(result["errors"])
        job.total_arquivos = total
        job.total_sucesso = len(result["success"])
        job.total_erro = len(result["errors"])
        job.status = "ERROR" if result["errors"] else "SUCCESS"
        log_lines = (
            [f"ERRO: {e.get('file', '')} - {e.get('error', '')}" for e in result["errors"]]
            + [f"OK: {n}" for n in result["success"]]
        )
        job.mensagem = (
            "\n".join(log_lines)[:5000]
            if log_lines
            else f"Processado: {total} arquivo(s). Sucesso: {len(result['success'])}, Erro: {len(result['errors'])}."
        )
        job.finished_at = timezone.localtime()
        job.save(
            update_fields=[
                "status", "total_arquivos", "total_sucesso", "total_erro",
                "mensagem", "finished_at",
            ]
        )
    except Exception as e:
        try:
            from app.db_GDF.Public.models import JobCargaSped
            job = JobCargaSped.objects.get(id=job_id)
            job.status = "ERROR"
            job.mensagem = str(e)[:5000]
            job.finished_at = timezone.localtime()
            job.save(update_fields=["status", "mensagem", "finished_at"])
        except Exception:
            pass
    finally:
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        connection.close()
