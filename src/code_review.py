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
        # Carregar informações da PR
        temp_dir = os.environ.get('RUNNER_TEMP', '/tmp')
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
        pr_body = pr_info["pr_body"]
        file_list = pr_info["file_list"]
        diff_text = pr_info["diff_text"]
        
        print(f"Realizando revisão de código para PR #{pr_number} em {repo_full_name}")
        
        # Inicializar cliente GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Procurar comentário existente
        existing_comment = None
        for comment in pr.get_issue_comments():
            if comment.body.startswith("## Análise de Código por IA"):
                existing_comment = comment
                break
                
        # Formatar prompt
        file_list_text = "\n".join([f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
                                     for f in file_list[:20]])
        prompt = f"""
Por favor, analise esta solicitação de Pull Request e realize uma revisão de código detalhada:

Título: {pr_title}
Descrição: {pr_body[:500]}

Arquivos alterados:
{file_list_text}

Alterações:
{diff_text[:4000]}

Forneça uma análise detalhada do código focando em:
1. Potenciais bugs ou problemas
2. Qualidade do código e boas práticas
3. Preocupações de segurança
4. Considerações de desempenho
5. Sugestões de melhoria específicas

Estruture sua análise em seções claras e seja objetivo, fornecendo exemplos específicos quando possível e sugestões concretas para melhorias.
"""
        code_review = call_cit_ai_service(access_token, prompt)
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        review_comment = (
            "## Análise de Código por IA\n\n"
            f"### Análise ({current_date})\n\n"
            f"{code_review}"
        )
        
        if existing_comment:
            existing_comment.edit(review_comment)
            print(f"Comentário de revisão existente (ID {existing_comment.id}) atualizado.")
        else:
            pr.create_issue_comment(review_comment)
            print("Novo comentário de revisão de código postado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao realizar revisão de código: {e}")
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
        'FlowTenant': 'flowteam',
        'Content-Type': 'application/json',
        'FlowAgent': 'code-reviewer',
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
        return f"⚠️ Erro ao obter análise de código: {e}"

if __name__ == "__main__":
    main()
