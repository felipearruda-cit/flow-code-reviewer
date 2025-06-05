# src/llm_client.py

import os
import requests
from llm_token_provider import LLMTokenProvider


class LLMClient:
    """
    Cliente genérico para chamadas ao Flow Orchestration API (OpenAI chat completions).
    Usa LLMTokenProvider para obter o token e adiciona cabeçalhos necessários.
    """

    def __init__(self, flow_agent: str):
        self.flow_agent = flow_agent
        provider = LLMTokenProvider()
        self.token = provider.get_token()
        self.tenant = os.getenv("FLOW_TENANT", "")
        # Se preferir, torne a URL configurável via variável de ambiente LLM_API_URL
        self.url = os.getenv(
            "LLM_API_URL",
            "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        )

    def chat(self, prompt: str, flow_lang: str, max_tokens: int = 1000, model: str = "gpt-4o-mini") -> str:
        """
        Realiza a chamada ao endpoint de chat completions e retorna o conteúdo da resposta.
        - prompt: string com o prompt a ser enviado
        - flow_lang: idioma para instruir o LLM (usado no prompt)
        - max_tokens: limite de tokens na resposta
        - model: modelo a ser usado
        """
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
                {"role": "system", "content": f"You are a helpful assistant that speaks {flow_lang}."},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": max_tokens,
            "model": model
        }

        response = requests.post(self.url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except Exception:
            raise RuntimeError(f"Erro LLMClient.chat: HTTP {response.status_code} - {response.text}")

        data = response.json()
        # Extrai a string do primeiro choice
        return data["choices"][0]["message"]["content"].strip()
