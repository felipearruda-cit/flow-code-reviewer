# src/llm_token_provider.py

import os
import requests


class LLMTokenProvider:
    """
    Classe responsável por obter o llm_token chamando o endpoint de autenticação.
    Lê as seguintes variáveis de ambiente (e aplica .strip()):
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
        # Usa .strip() para remover espaços ou quebras de linha inesperadas
        self.client_id     = os.getenv("AUTH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("AUTH_CLIENT_SECRET", "").strip()
        self.app_to_access = os.getenv("AUTH_APP_TO_ACCESS", "").strip()
        self.auth_url      = os.getenv("AUTH_ENGINE_URL", "").strip()
        self.flow_tenant   = os.getenv("FLOW_TENANT", "").strip()

        if not all([self.client_id, self.client_secret, self.app_to_access, self.auth_url, self.flow_tenant]):
            raise RuntimeError(
                "Faltando (ou vazias) as variáveis: "
                "AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, AUTH_APP_TO_ACCESS, AUTH_ENGINE_URL ou FLOW_TENANT."
            )

    def get_token(self) -> str:
        """
        Faz a requisição ao serviço de autenticação e retorna o access_token.
        Em caso de status code >=400, lança RuntimeError com detalhe.
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

        # Debug: imprima a URL exata antes de chamar, removendo eventuais espaços
        # (Evite deixar esta linha em produção, para não vazar a URL nos logs após resolver.)
        print(f"[llm_token_provider] Chamando AUTH_ENGINE_URL = '{self.auth_url}'")

        resp = requests.post(self.auth_url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except Exception:
            raise RuntimeError(
                f"Erro ao obter llm_token: HTTP {resp.status_code} - {resp.text}"
            )

        data = resp.json()
        # O auth-engine retorna {'access_token': '***', 'expires_in': 3599}
        access_token = data.get("access_token") or data.get("accessToken") or data.get("token")
        if not access_token:
            raise RuntimeError(f"Resposta JSON inesperada do auth-engine: {data}")

        return access_token
