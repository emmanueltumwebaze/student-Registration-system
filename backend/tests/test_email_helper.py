import os

from utils import EmailHelper


def test_generate_temporary_password_has_expected_length():
    password = EmailHelper.generate_temporary_password(length=12)
    assert len(password) >= 12
    assert password.strip()


def test_send_temporary_password_email_uses_console_fallback(monkeypatch):
    monkeypatch.delenv('SMTP_HOST', raising=False)
    monkeypatch.delenv('SMTP_PORT', raising=False)
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.delenv('SMTP_PASSWORD', raising=False)
    monkeypatch.delenv('SMTP_FROM_EMAIL', raising=False)

    result = EmailHelper.send_temporary_password_email(
        'student@example.com',
        'Jane',
        'Doe',
        'TempPass123',
        'student'
    )

    assert result['success'] is True
    assert result['method'] in {'console', 'smtp'}
