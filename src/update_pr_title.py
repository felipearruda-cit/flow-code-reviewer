# src/update_pr_title.py

import os
import pickle
from github import Github
import openai
from llm_token_provider import LLMTokenProvider


class UpdatePRTitle:
    """
    Classe responsável por:
      1) Carregar informações da PR (via arquivo pr_<n>.pkl em RUNNER_TEMP)
      2) Chamar o LLM (via LLMTokenProvider) para obter um título padronizado
      3) Atualizar o título da PR no GitHub, se necessário
    """

    def __init__(self,
                 github_token: str,
                 runner_temp: str,
                 flow_lang: str = "en"):
        self.github_token = github_token
        self.runner_temp = runner_temp
        self.flow_lang = flow_lang

        # Obtém llm_token via LLMTokenProvider e configura openai.api_key
        provider = LLMTokenProvider()
        llm_token = provider.get_token()
        openai.api_key = llm_token

    def run(self):
        # 1) Carrega pr_<n>.pkl
        pr_info = self._load_pr_info()
        current_title = pr_info["pr_title"]
        diff_excerpt = pr_info["diff_text"]

        print(f"[update_pr_title] Título atual: {current_title}")

        # 2) Gera novo título via LLM
        new_title = self._generate_standard_title(diff_excerpt, current_title)
        print(f"[update_pr_title] Novo título sugerido: {new_title}")

        # 3) Se o LLM sugerir exatamente o mesmo título, nada a fazer
        if new_title.lower() == current_title.strip().lower():
            print("[update_pr_title] O título já está padronizado. Nada a fazer.")
        else:
            # 4) Atualiza no GitHub
            self._update_github_pr_title(
                repo_full_name=pr_info["repo_full_name"],
                pr_number=pr_info["pr_number"],
                new_title=new_title
            )

    def _load_pr_info(self) -> dict:
        """
        Carrega o único arquivo pr_<n>.pkl dentro de runner_temp.
        Retorna o dicionário com as informações da PR.
        """
        files = [f for f in os.listdir(self.runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("Nenhum arquivo pr_*.pkl encontrado em RUNNER_TEMP.")
        pkl_path = os.path.join(self.runner_temp, files[0])
        with open(pkl_path, "rb") as f:
            pr_info = pickle.load(f)
        return pr_info

    def _generate_standard_title(self, diff: str, current_title: str) -> str:
        """
        Chama o LLM (via OpenAI) para sugerir um título padronizado
        baseado no diff e no título atual. Retorna a string do novo título.
        """
        prompt = f"""
You are a Pull Request title normalizer. Given the current PR title and a short diff excerpt,
propose a new, concise, well-formatted title following Conventional Commits style.

Current title: "{current_title}"
Diff excerpt (truncated):
```
{diff[:2000]}
```

Return ONLY the single new title, without any extra explanation.
Respond in {self.flow_lang}.
"""
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Assistant that suggests standardized PR titles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        new_title = response.choices[0].message.content.strip().splitlines()[0]
        return new_title

    def _update_github_pr_title(self, repo_full_name: str, pr_number: int, new_title: str):
        """
        Atualiza o título da PR no GitHub usando PyGithub.
        """
        gh = Github(self.github_token)
        repo = gh.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        pr.edit(title=new_title)
        print(f"[update_pr_title] ✅ Título atualizado para: {new_title}")


if __name__ == "__main__":
    """
    Espera as seguintes variáveis de ambiente:
      - GITHUB_TOKEN
      - RUNNER_TEMP
      - FLOW_LANG (opcional, padrão 'en')
      # As credenciais para LLMTokenProvider via auth-engine:
      #   - AUTH_CLIENT_ID
      #   - AUTH_CLIENT_SECRET
      #   - AUTH_APP_TO_ACCESS
      #   - AUTH_ENGINE_URL
      #   - FLOW_TENANT
    """
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    runner_temp = os.getenv("RUNNER_TEMP", "/tmp")
    flow_lang = os.getenv("FLOW_LANG", "en")

    if not github_token:
        print("[update_pr_title] ❌ GITHUB_TOKEN não informado.")
        exit(1)

    try:
        updater = UpdatePRTitle(
            github_token=github_token,
            runner_temp=runner_temp,
            flow_lang=flow_lang
        )
        updater.run()
    except Exception as e:
        print(f"[update_pr_title] ❌ {e}")
        exit(1)
        