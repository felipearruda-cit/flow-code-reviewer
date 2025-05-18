import os
import pickle
import requests
import json
from github import Github
from datetime import datetime

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    access_token = os.environ.get("TOKEN_LLM_API")
    
    if not access_token:
        print("Erro: TOKEN_LLM_API não está definido! Configure este secret no repositório.")
        return
    
    try:
        # --- carrega o pr_<n>.pkl ---
        temp_dir = os.environ.get('RUNNER_TEMP', '/tmp')
        pkl_files = [f for f in os.listdir(temp_dir) if f.startswith("pr_") and f.endswith(".pkl")]
        if not pkl_files:
            print("Erro: Nenhum arquivo pr_*.pkl encontrado em RUNNER_TEMP.")
            return
        pr_info_path = os.path.join(temp_dir, pkl_files[0])
        with open(pr_info_path, 'rb') as f:
            pr_info = pickle.load(f)
        
        repo_full_name = pr_info["repo_full_name"]
        pr_number      = pr_info["pr_number"]
        pr_title       = pr_info["pr_title"]
        pr_body        = pr_info["pr_body"]
        file_list      = pr_info["file_list"]
        diff_text      = pr_info["diff_text"]
        
        # --- prepara prompt pedindo formato com Changes+Sugestões ---
        file_list_text = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in file_list[:20]
        )
        prompt = f"""
Gere um relatório *Flow Code Reviewer* para esta PR, contendo:

1) Uma seção “Changes” em forma de tabela (Arquivo | Resumo da alteração);
2) Uma seção “Suggestions” com bullets sobre potenciais bugs, qualidade de código, segurança e desempenho;
3) Mantenha conciso e organizado.

Dados:
- Título: {pr_title}
- Descrição: {pr_body[:500]}
- Arquivos:  
{file_list_text}
- Trecho das alterações:  
{diff_text[:4000]}
"""
        review = call_cit_ai_service(access_token, prompt)
        
        g    = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr   = repo.get_pull(pr_number)
        
        # --- procura e substitui o comentário antigo, se existir ---
        existing = None
        for c in pr.get_issue_comments():
            if c.body.startswith("## Flow Code Reviewer"):
                existing = c
                break
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_body = (
            "## Flow Code Reviewer\n\n"
            f"*Atualizado em: {now}*\n\n"
            + review
        )
        
        if existing:
            existing.edit(comment_body)
            print(f"Comentário Flow Code Reviewer (ID {existing.id}) atualizado.")
        else:
            pr.create_issue_comment(comment_body)
            print("Novo comentário Flow Code Reviewer criado.")
    
    except Exception as e:
        print(f"Erro na revisão de código: {e}")
        import traceback; traceback.print_exc()
        exit(1)


def call_cit_ai_service(access_token, prompt):
    url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
    payload = json.dumps({
        "stream": False,
        "messages": [{"role": "user","content": prompt}],
        "max_tokens": 3000,
        "model": "gpt-4o-mini"
    })
    headers = {
        'FlowTenant':    'flowteam',
        'FlowAgent':     'code-reviewer',
        'Content-Type':  'application/json',
        'Accept':        'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    try:
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status()
        r = resp.json()
        return r["choices"][0]["message"]["content"].strip()
    except Exception as ex:
        print(f"Erro na chamada de IA: {ex}")
        return f"⚠️ Não foi possível obter Flow Code Reviewer: {ex}"

if __name__ == "__main__":
    main()
