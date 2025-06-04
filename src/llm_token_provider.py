# llm_token_provider.py

import os
import requests


class LLMTokenProvider:
    """
    Classe responsável por obter o llm_token chamando o endpoint de autenticação.
    Lê as seguintes variáveis de ambiente:
      - AUTH_CLIENT_ID
      - AUTH_CLIENT_SECRET
      - AUTH_APP_TO_ACCESS
      - AUTH_ENGINE_URL
      - FLOW_TENANT

    Uso:
        provider = LLMTokenProvider()
        token = provider.get_token()
    """

    def __init__(self):
        self.client_id     = os.getenv("AUTH_CLIENT_ID", "")
        self.client_secret = os.getenv("AUTH_CLIENT_SECRET", "")
        self.app_to_access = os.getenv("AUTH_APP_TO_ACCESS", "")
        self.auth_url      = os.getenv("AUTH_ENGINE_URL", "")
        self.flow_tenant   = os.getenv("FLOW_TENANT", "")

        if not all([self.client_id, self.client_secret, self.app_to_access, self.auth_url, self.flow_tenant]):
            raise RuntimeError(
                "Faltando variáveis de ambiente para autenticação: "
                "AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, AUTH_APP_TO_ACCESS, AUTH_ENGINE_URL ou FLOW_TENANT."
            )

    def get_token(self) -> str:
        """
        Faz a requisição ao serviço de autenticação e retorna o access_token.
        Raise RuntimeError em caso de falha.
        """
        payload = {
            "clientId":     self.client_id,
            "clientSecret": self.client_secret,
            "appToAccess":  self.app_to_access
        }
        headers = {
            "FlowTenant":   self.flow_tenant,
            "Content-Type": "application/json",
            "Accept":       "application/json"
        }

        resp = requests.post(self.auth_url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except Exception:
            raise RuntimeError(
                f"Erro ao obter llm_token: HTTP {resp.status_code} - {resp.text}"
            )

        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise RuntimeError(f"Resposta inesperada do auth-engine: {data}")

        return access_token
