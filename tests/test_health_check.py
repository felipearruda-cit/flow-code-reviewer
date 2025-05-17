import requests
import pytest
from health_check import HealthChecker

class DummyResponse:
    def __init__(self, status_code):
        self.status_code = status_code

def test_is_healthy_success(monkeypatch):
    """Retorna True quando a resposta é 200."""
    monkeypatch.setattr(requests, "get", lambda url, timeout: DummyResponse(200))
    checker = HealthChecker("https://flow.ciandt.com/ai-orchestration-api/v1/health", timeout=1)
    assert checker.is_healthy() is True

def test_is_healthy_failure_status(monkeypatch):
    """Retorna False quando o status não é 200."""
    monkeypatch.setattr(requests, "get", lambda url, timeout: DummyResponse(500))
    checker = HealthChecker("https://flow.ciandt.com/ai-orchestration-api/v1/health", timeout=1)
    assert checker.is_healthy() is False

def test_is_healthy_exception(monkeypatch):
    """Retorna False em caso de exceção de rede."""
    def bad_get(url, timeout):
        raise requests.RequestException("Erro de conexão")
    monkeypatch.setattr(requests, "get", bad_get)
    checker = HealthChecker("https://flow.ciandt.com/ai-orchestration-api/v1/health", timeout=1)
    assert checker.is_healthy() is False
