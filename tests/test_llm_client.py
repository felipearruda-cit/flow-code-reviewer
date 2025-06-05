import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from src.llm_client import LLMClient

@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv("AUTH_CLIENT_ID", "fake_id")
    monkeypatch.setenv("AUTH_CLIENT_SECRET", "fake_secret")
    monkeypatch.setenv("AUTH_APP_TO_ACCESS", "fake_app")
    monkeypatch.setenv("AUTH_ENGINE_URL", "https://fake-auth-url.com/token")
    monkeypatch.setenv("FLOW_TENANT", "fake_tenant")
    monkeypatch.setenv("LLM_API_URL", "https://fake-llm-url.com/chat")


def mock_token_response(*args, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "fake_token"}
    mock_resp.raise_for_status.return_value = None
    return mock_resp

def mock_chat_response(*args, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {"message": {"content": "Resposta do LLM"}}
        ]
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_init_and_get_token(env_vars):
    with patch("requests.post", side_effect=mock_token_response) as mock_post:
        client = LLMClient(flow_agent="test-agent")
        assert client.token == "fake_token"
        assert client.tenant == "fake_tenant"
        assert client.chat_url == "https://fake-llm-url.com/chat"
        mock_post.assert_called_once()


def test_chat_success(env_vars):
    with patch("requests.post", side_effect=[mock_token_response(), mock_chat_response()]) as mock_post:
        client = LLMClient(flow_agent="test-agent")
        resposta = client.chat(prompt="Olá!", flow_lang="pt-br", max_tokens=10, model="gpt-4o-mini")
        assert resposta == "Resposta do LLM"
        assert mock_post.call_count == 2
        # Verifica se o payload enviado está correto
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["messages"][1]["content"] == "Olá!"
        assert kwargs["json"]["model"] == "gpt-4o-mini"


def test_get_token_error(env_vars):
    def error_response(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_resp.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        return mock_resp

    with patch("requests.post", side_effect=error_response):
        with pytest.raises(RuntimeError) as exc:
            LLMClient(flow_agent="test-agent")
        assert "Erro ao obter llm_token" in str(exc.value)


def test_chat_error(env_vars):
    with patch("requests.post", side_effect=[mock_token_response(),
                                              MagicMock(status_code=500, text="Erro interno", raise_for_status=MagicMock(side_effect=requests.HTTPError("500")))
                                             ]):
        client = LLMClient(flow_agent="test-agent")
        with pytest.raises(RuntimeError) as exc:
            client.chat(prompt="fail", flow_lang="pt-br")
        assert "Erro LLMClient.chat" in str(exc.value)
