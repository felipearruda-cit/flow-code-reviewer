# .github/workflows/scripts/code_review.py
import os
import pickle
import requests
import json
from github import Github
from datetime import datetime

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    access_token = os.environ.get("TOKEN_LLM_API")
    lang = os.environ.get("FLOW_LANG", "en")
    if not access_token:
        print("Erro: TOKEN_LLM_API não definido."); return

    # carrega pr_<n>.pkl
    temp = os.environ.get("RUNNER_TEMP", "/tmp")
    pkls = [f for f in os.listdir(temp) if f.startswith("pr_") and f.endswith(".pkl")]
    if not pkls:
        print("Erro: pr_*.pkl não encontrado."); return
    with open(os.path.join(temp, pkls[0]), "rb") as f:
        pr = pickle.load(f)

    # prepara lista de arquivos e diff
    files_txt = "\n".join(
        f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in pr["file_list"][:20]
    )
    diff_txt = pr["diff_text"][:4000]

    # prompt genérico, sem pedir título da PR
    prompt = f"""
Generate a *Flow Code Reviewer* report for this Pull Request.
Please reply in **{lang}** and include exactly these sections:

## Resumo das Alterações
- 3–5 bullet points com os principais highlights

## Changes
- uma tabela markdown com (file | short description)

## Suggestions
- bullet points com potenciais bugs, code style, segurança e performance

Data:
- Files:
{files_txt}

- Diff snippet:
{diff_txt}
"""
    review = call_ia(access_token, prompt)

    # monta somente o comentário da revisão
    comment_body = review.strip()

    # publica/substitui no GitHub
    gh   = Github(github_token)
    pull = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])

    existing = next((c for c in pull.get_issue_comments()
                     if c.body.startswith("## Resumo das Alterações")), None)
    if existing:
        existing.edit(comment_body)
        print("✅ Flow Code Reviewer atualizado.")
    else:
        pull.create_issue_comment(comment_body)
        print("✅ Flow Code Reviewer criado.")

def call_ia(token, prompt):
    url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
    payload = json.dumps({
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "model": "gpt-4o-mini"
    })
    headers = {
        'FlowTenant':'flowteam','FlowAgent':'code-reviewer',
        'Content-Type':'application/json','Accept':'application/json',
        'Authorization':f'Bearer {token}'
    }
    resp = requests.post(url, headers=headers, data=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    main()

