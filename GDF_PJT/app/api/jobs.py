"""
Jobs em background: Carga XML e Carga SPED.
Executados em thread; usam app.classes (CargaXml, CargaSped).
"""
import os
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from app.db_GDF.Public.models import Empresa


def processar_job_xml_background(job_id, temp_dir, type_xml, origem_dados, user_id, cod_cliente, empresa_id):
    """Executa em thread: processa XMLs da pasta temp e atualiza o job."""
    from django.db import connection
    from app.db_GDF.Public.models import JobCargaXml
    from app.classes.CargaXml import CargaXml

    try:
        from django.contrib.auth.models import User as AuthUser
        job = JobCargaXml.objects.get(id=job_id)
        user = AuthUser.objects.filter(id=user_id).first()
        username = user.username if user else "SYSTEM"

        xml_files = []
        for fname in sorted(os.listdir(temp_dir)):
            if not fname.lower().endswith(".xml"):
                continue
            path = os.path.join(temp_dir, fname)
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as f:
                xml_bytes = f.read()
            nome = fname.split("_", 1)[-1] if "_" in fname else fname
            xml_files.append(SimpleUploadedFile(nome, xml_bytes))

        if not xml_files:
            job.status = "ERROR"
            job.mensagem = "Nenhum arquivo XML encontrado na pasta temporária."
            job.finished_at = timezone.localtime()
            job.save(update_fields=["status", "mensagem", "finished_at"])
            return

        cl_xml = CargaXml()
        upload_result = cl_xml.set_upload_xml(
            xml_files, type_xml, origem_dados, username, cod_cliente
        )

        mensagem_lines = []
        for err in upload_result.get("errors", []):
            mensagem_lines.append(f"ERRO: {err.get('file', '')} - {err.get('error', '')}")
        for p in upload_result.get("pendentes", []):
            mensagem_lines.append(f"PENDENTES (empresa não cadastrada): {p.get('file', '')} - {p.get('motivo', '')}")
        for name in upload_result.get("success", []):
            mensagem_lines.append(f"OK: {name}")
        resumo = "\n".join(mensagem_lines)[:5000]

        empresa_prefixo = ""
        if empresa_id:
            try:
                empresa = Empresa.objects.get(
                    cod_empresa=empresa_id,
                    gdfcliente__cod_cliente=cod_cliente,
                )
                nome_emp = empresa.fantasia or empresa.razao or empresa.cod_empresa
                empresa_prefixo = f"EMPRESA: {empresa.cod_empresa} - {nome_emp}\n"
            except Empresa.DoesNotExist:
                empresa_prefixo = f"EMPRESA: {empresa_id} (não encontrada)\n"

        total_arquivos = (
            len(upload_result["success"])
            + len(upload_result["errors"])
            + len(upload_result.get("pendentes", []))
        )
        job.total_arquivos = total_arquivos
        job.total_sucesso = len(upload_result["success"])
        job.total_erro = len(upload_result["errors"])
        job.status = "ERROR" if upload_result["errors"] else "SUCCESS"
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
        connection.close()


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
