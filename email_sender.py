"""
将总结内容通过邮件发送到指定邮箱。
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_summary_email(
    to_email: str,
    subject: str,
    html_body: str,
    *,
    smtp_host: str | None = None,
    smtp_port: int = 465,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
    use_tls: bool = True,
) -> None:
    """
    发送 HTML 邮件。
    :param to_email: 收件人邮箱
    :param subject: 邮件主题
    :param html_body: HTML 正文
    :param smtp_host: SMTP 服务器（默认从环境变量 SMTP_HOST 读取）
    :param smtp_port: 端口，465 为 SSL
    :param smtp_user: 发件账号（环境变量 SMTP_USER）
    :param smtp_password: 发件密码/授权码（环境变量 SMTP_PASSWORD）
    :param use_tls: 是否使用 SSL/TLS
    """
    host = smtp_host or os.environ.get("SMTP_HOST", "")
    user = smtp_user or os.environ.get("SMTP_USER", "")
    password = smtp_password or os.environ.get("SMTP_PASSWORD", "")
    if not host or not user or not password:
        raise ValueError("请配置 SMTP_HOST、SMTP_USER、SMTP_PASSWORD（或传入参数）")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if use_tls and smtp_port == 465:
        with smtplib.SMTP_SSL(host, smtp_port) as server:
            server.login(user, password)
            server.sendmail(user, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(host, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_email], msg.as_string())
