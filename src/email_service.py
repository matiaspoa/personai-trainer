from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import requests


@dataclass(frozen=True)
class ResendEmailConfig:
    """
    Configuração de envio de e-mails via Resend API.

    Você só precisa preencher o .env com:
    - RESEND_API_KEY  (API key gerada no painel da Resend)
    - RESEND_FROM     (remetente autorizado, ex.: 'Seu Nome <you@seu-dominio.com>')
    - RESEND_TO       (destinatário; se não definido, usa RESEND_FROM)
    """

    api_key: str
    from_address: str
    to_address: str

    @classmethod
    def from_env(cls) -> "ResendEmailConfig":
        api_key = os.getenv("RESEND_API_KEY")
        from_address = os.getenv("RESEND_FROM")
        to_address = os.getenv("RESEND_TO") or from_address

        missing = [
            name
            for name, value in [
                ("RESEND_API_KEY", api_key),
                ("RESEND_FROM", from_address),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                "Configuração Resend incompleta. "
                "Defina RESEND_API_KEY e RESEND_FROM no .env para habilitar envio via Resend."
            )

        return cls(
            api_key=api_key,  # type: ignore[arg-type]
            from_address=from_address,  # type: ignore[arg-type]
            to_address=to_address,  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class EmailConfig:
    """
    Configuração de e-mail carregada de variáveis de ambiente.

    Espera as seguintes variáveis no ambiente ou .env:
    - EMAIL_SMTP_HOST
    - EMAIL_SMTP_PORT
    - EMAIL_USERNAME
    - EMAIL_PASSWORD
    - EMAIL_FROM
    """

    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_address: str
    use_starttls: bool = True

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Cria uma configuração a partir das variáveis de ambiente."""
        host = os.getenv("EMAIL_SMTP_HOST")
        port_raw = os.getenv("EMAIL_SMTP_PORT")
        username = os.getenv("EMAIL_USERNAME")
        password = os.getenv("EMAIL_PASSWORD")
        from_address = os.getenv("EMAIL_FROM")

        missing = [
            name
            for name, value in [
                ("EMAIL_SMTP_HOST", host),
                ("EMAIL_SMTP_PORT", port_raw),
                ("EMAIL_USERNAME", username),
                ("EMAIL_PASSWORD", password),
                ("EMAIL_FROM", from_address),
            ]
            if not value
        ]
        if missing:
            missing_str = ", ".join(missing)
            raise ValueError(
                f"Variáveis de ambiente de e-mail ausentes: {missing_str}. "
                "Defina-as no .env (sem commitar) para habilitar envio de relatórios."
            )

        try:
            port = int(port_raw) if port_raw is not None else 587
        except ValueError as exc:  # pragma: no cover - simples validação
            raise ValueError("EMAIL_SMTP_PORT deve ser um inteiro.") from exc

        return cls(
            smtp_host=host,
            smtp_port=port,
            username=username,  # type: ignore[arg-type]
            password=password,  # type: ignore[arg-type]
            from_address=from_address,  # type: ignore[arg-type]
        )


class EmailSender(Protocol):
    """Contrato mínimo para envio de e-mails."""

    def send_email(self, to_address: str, subject: str, body: str) -> None:  # pragma: no cover - interface
        ...


class SmtpEmailSender:
    """
    Implementação simples de envio de e-mail via SMTP.

    Focada em ser segura e fácil de entender, não em cobrir todos os casos.
    """

    def __init__(self, config: EmailConfig) -> None:
        self._config = config

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._config.from_address
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as server:
                if self._config.use_starttls:
                    server.starttls(context=context)
                server.login(self._config.username, self._config.password)
                server.send_message(message)
        except smtplib.SMTPException as exc:
            # De propósito, não incluímos senha/usuário em mensagens de erro.
            raise RuntimeError(f"Falha ao enviar e-mail para {to_address}: {exc}") from exc


class ResendEmailSender:
    """
    Implementação simples de envio de e-mail usando a API da Resend.

    Benefícios:
    - Você não expõe a senha do seu e-mail, só a API key.
    - A configuração é toda feita via variáveis de ambiente.
    """

    def __init__(self, config: ResendEmailConfig) -> None:
        self._config = config
        self._base_url = "https://api.resend.com/emails"

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": self._config.from_address,
            "to": [to_address],
            "subject": subject,
            "text": body,
        }

        try:
            response = requests.post(self._base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

        except requests.HTTPError as exc:
            raise RuntimeError(f"Falha HTTP ao enviar e-mail via Resend: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Erro de rede ao enviar e-mail via Resend: {exc}") from exc


