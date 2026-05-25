"""
Serviço de envio de e-mail para notificações de workflow.

Usa stdlib smtplib — sem dependências externas.
Desabilitado por padrão (EMAIL_ENABLED=false no .env).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from api.config import get_settings

logger = logging.getLogger(__name__)


def _enviar(assunto: str, corpo_html: str, destinatarios: list[str]) -> None:
    """Envia um e-mail HTML. Silencioso em caso de falha (apenas loga)."""
    settings = get_settings()

    if not settings.email_enabled:
        logger.info("EMAIL_ENABLED=false — não enviado: %s", assunto)
        return

    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        logger.info("Sem destinatários — e-mail não enviado: %s", assunto)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(destinatarios)
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, destinatarios, msg.as_string())
        logger.info("E-mail enviado: '%s' → %s", assunto, destinatarios)
    except Exception as exc:
        logger.error("Falha ao enviar e-mail '%s': %s", assunto, exc)


def _aprovadores() -> list[str]:
    settings = get_settings()
    return [e.strip() for e in settings.email_aprovadores.split(",") if e.strip()]


def notificar_envio_para_revisao(
    versao_nome: str,
    empresa_nome: str,
    enviado_por: str,
) -> None:
    """Notifica aprovadores quando um orçamento é submetido para revisão."""
    _enviar(
        assunto=f"[FP&A] Orçamento enviado para revisão: {versao_nome}",
        corpo_html=f"""
        <html><body style="font-family: sans-serif; color: #1e293b;">
        <h2 style="color:#2563eb;">📋 Orçamento aguardando aprovação</h2>
        <table style="border-collapse:collapse;">
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Versão:</td>
              <td><strong>{versao_nome}</strong></td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Empresa:</td>
              <td>{empresa_nome}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Enviado por:</td>
              <td>{enviado_por}</td></tr>
        </table>
        <p style="margin-top:16px;">
          Acesse o sistema FP&amp;A para <strong>aprovar</strong> ou <strong>reprovar</strong>.
        </p>
        </body></html>
        """,
        destinatarios=_aprovadores(),
    )


def notificar_aprovado(
    versao_nome: str,
    empresa_nome: str,
    aprovado_por: str,
    comentario: str | None,
    email_responsavel: str | None,
) -> None:
    """Notifica o responsável quando seu orçamento é aprovado."""
    if not email_responsavel:
        return
    comentario_bloco = (
        f'<p><strong>Comentário:</strong> {comentario}</p>'
        if comentario
        else ""
    )
    _enviar(
        assunto=f"[FP&A] Orçamento APROVADO: {versao_nome}",
        corpo_html=f"""
        <html><body style="font-family: sans-serif; color: #1e293b;">
        <h2 style="color:#16a34a;">✅ Orçamento aprovado</h2>
        <table style="border-collapse:collapse;">
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Versão:</td>
              <td><strong>{versao_nome}</strong></td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Empresa:</td>
              <td>{empresa_nome}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Aprovado por:</td>
              <td>{aprovado_por}</td></tr>
        </table>
        {comentario_bloco}
        <p style="margin-top:16px;color:#16a34a;">
          A versão foi <strong>bloqueada para edição</strong>.
        </p>
        </body></html>
        """,
        destinatarios=[email_responsavel],
    )


def notificar_reprovado(
    versao_nome: str,
    empresa_nome: str,
    reprovado_por: str,
    comentario: str,
    email_responsavel: str | None,
) -> None:
    """Notifica o responsável quando seu orçamento é reprovado."""
    if not email_responsavel:
        return
    _enviar(
        assunto=f"[FP&A] Orçamento REPROVADO: {versao_nome}",
        corpo_html=f"""
        <html><body style="font-family: sans-serif; color: #1e293b;">
        <h2 style="color:#dc2626;">❌ Orçamento reprovado</h2>
        <table style="border-collapse:collapse;">
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Versão:</td>
              <td><strong>{versao_nome}</strong></td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Empresa:</td>
              <td>{empresa_nome}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Reprovado por:</td>
              <td>{reprovado_por}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;color:#64748b;">Motivo:</td>
              <td><strong>{comentario}</strong></td></tr>
        </table>
        <p style="margin-top:16px;">
          Corrija o orçamento e envie novamente para revisão.
        </p>
        </body></html>
        """,
        destinatarios=[email_responsavel],
    )
