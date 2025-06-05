# src/llm_client.py

import os
import requests


class LLMClient:
    """
    Cliente genérico para chamadas ao Flow Orchestration API (OpenAI chat completions),
    incluindo obtenção de token via Auth Engine.
    """

    def __init__(self, flow_agent: str):
        self.flow_agent = flow_agent

        # Carrega variáveis de autenticação do Auth Engine
        self.client_id = os.getenv("AUTH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("AUTH_CLIENT_SECRET", "").strip()
        self.app_to_access = os.getenv("AUTH_APP_TO_ACCESS", "").strip()
        self.auth_url = os.getenv("AUTH_ENGINE_URL", "").strip()
        self.tenant = os.getenv("FLOW_TENANT", "").strip()

        if not all([self.client_id, self.client_secret, self.app_to_access, self.auth_url, self.tenant]):
            raise RuntimeError(
                "Faltando (ou vazias) as variáveis: "
                "AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, AUTH_APP_TO_ACCESS, AUTH_ENGINE_URL ou FLOW_TENANT."
            )

        # Obtém o token LLM do Auth Engine
        self.token = self._get_token()

        # Endpoint de chat completions (pode ser sobrescrito por LLM_API_URL)
        self.chat_url = os.getenv(
            "LLM_API_URL",
            "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        )

    def _get_token(self) -> str:
        """
        Chama o Auth Engine para obter um token de acesso LLM.
        """
        payload = {
            "clientId":     self.client_id,
            "clientSecret": self.client_secret,
            "appToAccess":  self.app_to_access
        }
        headers = {
            "FlowTenant":   self.tenant,
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
        access_token = data.get("access_token") or data.get("accessToken") or data.get("token")
        if not access_token:
            raise RuntimeError(f"Resposta JSON inesperada do auth-engine: {data}")

        return access_token

    def chat(self, prompt: str, flow_lang: str, max_tokens: int = 1000, model: str = "gpt-4o-mini") -> str:
        """
        Realiza a chamada ao endpoint de chat completions e retorna o conteúdo da resposta.
        - prompt: string com o prompt a ser enviado
        - flow_lang: idioma para instruir o LLM (usado na mensagem do system)
        - max_tokens: limite de tokens na resposta
        - model: modelo a ser usado
        """
        system_content = f"You are an assistant that responds in {flow_lang}."
        headers = {
            "FlowTenant":    self.tenant,
            "FlowAgent":     self.flow_agent,
            "Content-Type":  "application/json",
            "Accept":        "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        payload = {
            "stream": False,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": max_tokens,
            "model": model
        }

        response = requests.post(self.chat_url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except Exception:
            raise RuntimeError(f"Erro LLMClient.chat: HTTP {response.status_code} - {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()