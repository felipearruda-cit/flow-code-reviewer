import os
import pickle
import requests
import json
from github import Github
import re

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
        pr_body        = pr_info["pr_body"] or ""
        pr_title       = pr_info["pr_title"]
        file_list      = pr_info["file_list"]
        diff_text      = pr_info["diff_text"]
        
        # --- formata prompt pedindo bullet‐points como no exemplo anexo ---
        file_list_text = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in file_list[:20]
        )
        prompt = f"""
Gere um *Flow Code Summary* para esta PR, no formato:

1) Uma breve lista em bullets dos 3–5 pontos principais (como no exemplo anexo “Summary by CodeRabbit”);
2) Em seguida, uma seção “Changes” com uma TABELA resumindo (arquivo e descrição curta da alteração);
3) Mantenha um tom técnico e profissional.

Dados:
- Título: {pr_title}
- Arquivos:  
{file_list_text}
- Trecho das alterações:  
{diff_text[:2000]}
"""
        
        summary = call_cit_ai_service(access_token, prompt)
        
        # --- atualiza o corpo da PR, preservando descrição manual e NÃO duplicando summary ---
        g    = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr   = repo.get_pull(pr_number)
        
        # regex que encontra a seção Flow Code Summary inteira (se existir)
        pattern = r"(## Flow Code Summary[\s\S]*?)(?=\n##|$)"
        
        if re.search(pattern, pr_body):
            new_body = re.sub(
                pattern,
                f"## Flow Code Summary\n\n{summary}\n\n",
                pr_body
            )
            print("✅ Flow Code Summary existente substituído.")
        else:
            # se houver descrição manual, deixa ela e acrescenta logo abaixo
            if pr_body.strip() and pr_body not in ("No description provided.", ""):
                new_body = pr_body + f"\n\n## Flow Code Summary\n\n{summary}\n\n"
                print("✅ Flow Code Summary adicionado abaixo da descrição manual.")
            else:
                new_body = f"## Flow Code Summary\n\n{summary}\n\n"
                print("✅ Flow Code Summary criado como única descrição.")
        
        pr.edit(body=new_body)
        print("PR atualizada com Flow Code Summary.")
    
    except Exception as e:
        print(f"Erro ao adicionar summary: {e}")
        import traceback; traceback.print_exc()
        exit(1)


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
        r = resp.json()
        return r["choices"][0]["message"]["content"].strip()
    except Exception as ex:
        print(f"Erro na chamada de IA: {ex}")
        return f"⚠️ Não foi possível gerar Flow Code Summary: {ex}"

if __name__ == "__main__":
    main()
