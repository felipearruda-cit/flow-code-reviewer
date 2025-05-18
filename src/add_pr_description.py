# .github/workflows/scripts/add_pr_description.py
import os
import pickle
import requests
import json
import re
from github import Github

def main():
    # 1) pega tokens
    github_token = os.environ.get("GITHUB_TOKEN")
    access_token = os.environ.get("TOKEN_LLM_API")
    if not access_token:
        print("Erro: TOKEN_LLM_API não está definido!"); return

    # 2) carrega o pr_<n>.pkl gerado pelo collect_pr_info.py
    temp_dir = os.environ.get("RUNNER_TEMP", "/tmp")
    pkl_files = [f for f in os.listdir(temp_dir) if f.startswith("pr_") and f.endswith(".pkl")]
    if not pkl_files:
        print("Erro: não encontrei nenhum pr_*.pkl em RUNNER_TEMP."); return
    pr_info_path = os.path.join(temp_dir, pkl_files[0])
    with open(pr_info_path, "rb") as f:
        pr_info = pickle.load(f)

    repo_full_name = pr_info["repo_full_name"]
    pr_number      = pr_info["pr_number"]
    pr_body        = pr_info["pr_body"] or ""
    pr_title       = pr_info["pr_title"]
    file_list      = pr_info["file_list"]
    diff_text      = pr_info["diff_text"]

    # 3) gera o prompt para a IA
    file_list_text = "\n".join(
        f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in file_list[:20]
    )
    prompt = f"""
Gere um *Flow Code Summary* para esta PR, no formato:

1) 3–5 bullets com os pontos principais;
2) Uma seção **Changes** em tabela (arquivo | descrição curta);

Dados:
- Título: {pr_title}
- Arquivos:
{file_list_text}

- Diff (trecho):
{diff_text[:2000]}
"""

    summary = call_cit_ai_service(access_token, prompt)

    # 4) limpa QUALQUER seção antiga de summary do corpo da PR
    #    - remove blocos começando em "## Flow Code Summary" até o próximo "##"
    #    - também remove se por acaso ficou "## Summary by ..."
    pr_body = re.sub(r"(?ms)^##\s*Flow Code Summary.*?(?=^##\s|\Z)", "", pr_body)
    pr_body = re.sub(r"(?ms)^##\s*Summary by.*?(?=^##\s|\Z)",        "", pr_body)
    pr_body = pr_body.strip()

    # 5) monta o novo corpo apenas com a seção Flow Code Summary
    new_body = f"{pr_body}\n\n## Flow Code Summary\n\n{summary}\n"

    # 6) aplica no GitHub
    gh   = Github(github_token)
    repo = gh.get_repo(repo_full_name)
    pr   = repo.get_pull(pr_number)
    pr.edit(body=new_body)
    print("✅ Corpo da PR atualizado com novo Flow Code Summary (sem duplicações).")

def call_cit_ai_service(access_token, prompt):
    url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
    payload = json.dumps({
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "model": "gpt-4o-mini"
    })
    headers = {
        'FlowTenant':    'flowteam',
        'FlowAgent':     'pr-summary-generator',
        'Content-Type':  'application/json',
        'Accept':        'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    try:
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro na chamada de IA: {e}")
        return f"⚠️ Não foi possível gerar Flow Code Summary: {e}"

if __name__ == "__main__":
    main()
