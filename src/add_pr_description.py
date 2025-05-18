import os
import pickle
import requests
import json
import re
from github import Github

def main():
    # --- Tokens e idioma ---
    github_token = os.environ.get("GITHUB_TOKEN")
    access_token = os.environ.get("TOKEN_LLM_API")
    lang = os.environ.get("FLOW_LANG", "en")
    if not access_token:
        print("❌ Erro: TOKEN_LLM_API não definido.")
        return

    # --- Carrega arquivo pr_<n>.pkl ---
    temp = os.environ.get("RUNNER_TEMP", "/tmp")
    pkls = [f for f in os.listdir(temp) if f.startswith("pr_") and f.endswith(".pkl")]
    if not pkls:
        print("❌ Erro: nenhum pr_*.pkl encontrado.")
        return
    with open(os.path.join(temp, pkls[0]), "rb") as f:
        pr = pickle.load(f)

    # --- Prepara lista de arquivos e diff ---
    files_txt = "\n".join(
        f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in pr["file_list"][:20]
    )
    diff_txt = pr["diff_text"][:2000]

    # --- Monta prompt genérico com instrução de idioma ---
    prompt = f"""
Generate a *Flow Code Summary* for this Pull Request.
Please reply in **{lang}** and follow this format:

1) 3–5 bullet points with the main highlights;
2) A **Changes** section as a markdown table (file | short description).

Data:
- Title: {pr['pr_title']}
- Files:
{files_txt}

- Diff snippet:
{diff_txt}
"""
    summary = call_ia(access_token, prompt)

    # --- Limpa seções antigas de summary no corpo da PR ---
    body = pr["pr_body"] or ""
    body = re.sub(r"(?ms)^##\s*Flow Code Summary.*?(?=^##\s|\Z)", "", body).strip()

    # --- Remove eventuais cabeçalhos duplicados vindos da IA ---
    summary = re.sub(r'(?m)^#+\s*Flow Code Summary.*\n', '', summary).strip()

    # --- Monta novo corpo e aplica ---
    new_body = f"{body}\n\n## Flow Code Summary\n\n{summary}\n"
    gh   = Github(github_token)
    pull = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
    pull.edit(body=new_body)
    print("✅ Flow Code Summary atualizado.")

def call_ia(token, prompt):
    url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
    payload = json.dumps({
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "model": "gpt-4o-mini"
    })
    headers = {
        'FlowTenant':'flowteam',
        'FlowAgent':'pr-summary-generator',
        'Content-Type':'application/json',
        'Accept':'application/json',
        'Authorization':f'Bearer {token}'
    }
    resp = requests.post(url, headers=headers, data=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    main()
