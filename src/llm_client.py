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
        self.url = os.getenv(
            "LLM_API_URL",
            "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        )

    def chat(self, prompt: str, flow_lang: str, max_tokens: int = 1000, model: str = "gpt-4o-mini") -> str:
        """
        Realiza a chamada ao endpoint de chat completions e retorna o conteúdo da resposta.
        - prompt: string com o prompt a ser enviado
        - flow_lang: idioma para instruir o LLM (usado no system message)
        - max_tokens: limite de tokens na resposta
        - model: modelo a ser usado
        """
        # Define a mensagem de sistema para instruir o idioma de resposta
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

        response = requests.post(self.url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except Exception:
            raise RuntimeError(f"Erro LLMClient.chat: HTTP {response.status_code} - {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()