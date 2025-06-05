# src/update_pr_title.py

import os
import pickle
from github import Github
import openai
from llm_token_provider import LLMTokenProvider

def generate_standard_title(diff: str, current_title: str, flow_lang: str) -> str:
    """
    Chama o OpenAI para sugerir um título padronizado baseado no diff e no título atual.
    Retorna somente a string com o novo título.
    """
    # Obtenha o token LLM via LLMTokenProvider
    provider = LLMTokenProvider()
    llm_token = provider.get_token()
    openai.api_key = llm_token

    prompt = f"""
You are a Pull Request title normalizer. Given the current PR title and a short diff excerpt,
propose a new, concise, well-formatted title following Conventional Commits style.

Current title: "{current_title}"
Diff excerpt (truncated):
```
{diff[:2000]}
```

Return ONLY the single new title, without any extra explanation.
Respond in {flow_lang}.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Assistant that suggests standardized PR titles."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.0,
        max_tokens=20
    )

    new_title = response.choices[0].message.content.strip().splitlines()[0]
    return new_title

def load_pr_info(runner_temp: str) -> dict:
    """
    Carrega o arquivo pr_<n>.pkl gerado por collect_pr_info.py (ou equivalente).
    Espera encontrar um único arquivo pr_N.pkl dentro de runner_temp.
    Retorna um dict com campos:
      - repo_full_name
      - pr_number
      - pr_title
      - pr_body
      - file_list
      - diff_text
    """
    files = [f for f in os.listdir(runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
    if not files:
        raise RuntimeError("Nenhum arquivo pr_*.pkl encontrado em RUNNER_TEMP.")
    path = os.path.join(runner_temp, files[0])
    with open(path, "rb") as f:
        pr = pickle.load(f)
    return pr

def update_github_pr_title(github_token: str, repo_full_name: str, pr_number: int, new_title: str):
    """
    Atualiza o título da PR no GitHub usando PyGithub.
    """
    gh = Github(github_token)
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
        # 1) Carrega as informações da PR
        pr = load_pr_info(runner_temp)
        current_title = pr["pr_title"]
        diff_excerpt = pr["diff_text"]

        print(f"[update_pr_title] Título atual: {current_title}")

        # 2) Gera novo título via LLM
        new_title = generate_standard_title(diff_excerpt, current_title, flow_lang)
        print(f"[update_pr_title] Novo título sugerido: {new_title}")

        # 3) Se o LLM sugerir exatamente o mesmo título, nada a fazer
        if new_title.lower() == current_title.strip().lower():
            print("[update_pr_title] O título já está padronizado. Nada a fazer.")
        else:
            # 4) Atualiza no GitHub
            update_github_pr_title(
                github_token=github_token,
                repo_full_name=pr["repo_full_name"],
                pr_number=pr["pr_number"],
                new_title=new_title
            )

    except Exception as e:
        print(f"[update_pr_title] ❌ {e}")
        exit(1)