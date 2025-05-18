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
        # Carregar informações da PR
        temp_dir = os.environ.get('RUNNER_TEMP', '/tmp')
        # Determina o nome do arquivo com base no número da PR
        # (este número virá de collect_pr_info.py)
        # Abriremos o PKL mesmo sem saber o número de antemão
        pkl_files = [f for f in os.listdir(temp_dir) if f.startswith("pr_") and f.endswith(".pkl")]
        if not pkl_files:
            print("Erro: Nenhum arquivo pr_*.pkl encontrado em RUNNER_TEMP.")
            return
        pr_info_path = os.path.join(temp_dir, pkl_files[0])
        
        with open(pr_info_path, 'rb') as f:
            pr_info = pickle.load(f)
        
        repo_full_name = pr_info["repo_full_name"]
        pr_number = pr_info["pr_number"]
        pr_title = pr_info["pr_title"]
        pr_body = pr_info["pr_body"] or ""
        file_list = pr_info["file_list"]
        diff_text = pr_info["diff_text"]
        
        print(f"Gerando descrição para PR #{pr_number} em {repo_full_name}")
        
        # Formatar lista de arquivos
        file_list_text = "\n".join([f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
                                     for f in file_list[:20]])
        
        prompt = f"""
Por favor, analise esta solicitação de Pull Request e crie uma descrição concisa e informativa:

Título: {pr_title}

Arquivos alterados:
{file_list_text}

Alterações principais:
{diff_text[:2000]}

Forneça uma descrição clara e concisa desta PR em 3-5 parágrafos, incluindo:
1. O propósito principal desta alteração
2. Quais arquivos/componentes principais são afetados
3. Quaisquer considerações importantes ou dependências

Mantenha um tom profissional e foque nos aspectos técnicos mais relevantes.
"""
        
        description = call_cit_ai_service(access_token, prompt)
        
        # Inicializar cliente GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Regex para substituir toda a seção existente de descrição gerada por IA
        pattern = r"(## Descrição Gerada por IA[\s\S]*?)(?=\n##|$)"
        
        if re.search(pattern, pr_body):
            new_body = re.sub(pattern, f"## Descrição Gerada por IA\n\n{description}\n\n", pr_body)
            print("Descrição gerada por IA atualizada (substituída).")
        else:
            if pr_body.strip() and pr_body not in ["No description provided.", ""]:
                # Há descrição manual: adiciona abaixo dela
                new_body = pr_body + f"\n\n## Descrição Gerada por IA\n\n{description}\n\n"
                print("Descrição gerada por IA adicionada ao final da descrição manual.")
            else:
                # Sem descrição manual relevante
                new_body = f"## Descrição Gerada por IA\n\n{description}\n\n"
                print("Nova descrição de PR gerada por IA.")
        
        pr.edit(body=new_body)
        print("Descrição da PR atualizada com sucesso!")
        
    except Exception as e:
        print(f"Erro ao adicionar descrição: {str(e)}")
        import traceback; traceback.print_exc()
        exit(1)

def call_cit_ai_service(access_token, prompt):
    url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
    payload = json.dumps({
        "stream": False,
        "messages": [{"role": "user","content": prompt}],
        "max_tokens": 1000,
        "model": "gpt-4o-mini"
    })
    headers = {
        'FlowTenant': 'flowteam',
        'Content-Type': 'application/json',
        'FlowAgent': 'pr-description-generator',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro ao chamar serviço de IA: {e}")
        return f"⚠️ Não foi possível gerar descrição: {e}"

if __name__ == "__main__":
    main()
