import os
import sys
import pickle
import requests
from github import Github
from utils import summarize_diff, format_review_comment, get_pr_details

def main():
    # Configuração
    github_token = os.environ.get("GITHUB_TOKEN")
    api_token = os.environ.get("TOKEN_LLM_API")
    ai_api_url = os.environ.get("AI_API_URL", "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions")
    ai_model = os.environ.get("AI_MODEL", "gpt-4o-mini")
    environment = os.environ.get("ENVIRONMENT", "dev")
    
    if not github_token or not api_token:
        print("❌ Tokens de autenticação não configurados!")
        sys.exit(1)

    # Inicializar cliente GitHub
    g = Github(github_token)
    
    # Obter detalhes do PR (mudança para arquivo pkl)
    pr_info_file = "pr_info.pkl"  # Alterado para .pkl
    try:
        with open(pr_info_file, 'rb') as f:  # 'rb' para modo binário
            pr_data = pickle.load(f)  # Usar pickle.load em vez de json.load
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo de informações do PR: {e}")
        sys.exit(1)
    
    print(f"Realizando revisão de código para PR #{pr_data['number']} em {pr_data['repo_full_name']}")
    
    repo = g.get_repo(pr_data['repo_full_name'])
    pr_number = pr_data['number']
    pull_request = repo.get_pull(pr_number)
    
    # Verificar se já existe um comentário de revisão anterior
    existing_comment_id = None
    review_comment_header = "## 🤖 Análise de Código"
    
    for comment in pull_request.get_issue_comments():
        if review_comment_header in comment.body:
            existing_comment_id = comment.id
            break
    
    print(f"================================================================================")
    print(f"➡️ INICIANDO ETAPA: Análise de Código")
    print(f"================================================================================")
    
    # Obter o diff do PR
    diff_text = pull_request.get_diff()
    
    # Resumir o diff para análise (limitar tamanho)
    diff_summary = summarize_diff(diff_text)
    
    # Preparar o prompt para a API da CI&T
    pr_details = get_pr_details(pull_request)
    
    print("Chamando API da CI&T para análise de código...")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        
        payload = {
            "model": ai_model,
            "messages": [
                {"role": "system", "content": f"Você é um especialista em revisão de código. Você deve analisar o diff a seguir e fornecer feedback útil sobre possíveis problemas, melhorias, bugs potenciais e sugestões de refatoração. Seja construtivo e específico. Considere aspectos como desempenho, segurança, manutenibilidade e legibilidade."},
                {"role": "user", "content": f"Por favor, analise este diff de código de um pull request:\n\nTítulo do PR: {pr_details['title']}\nDescrição: {pr_details['description']}\n\nAlterações:\n{diff_summary}"}
            ]
        }
        
        print("Enviando requisição para a API...")
        response = requests.post(ai_api_url, headers=headers, json=payload)
        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            review_content = response_data['choices'][0]['message']['content']
            
            # Formatar o comentário de revisão
            review_comment = format_review_comment(review_content, "Análise de Código")
            
            # Encontrar e atualizar comentário existente se houver
            if existing_comment_id:
                print(f"Encontrado comentário existente de análise de código (ID: {existing_comment_id})")
                
                # Correção aqui
                issue = repo.get_issue(pr_number)
                comment = issue.get_comment(existing_comment_id)
                
                try:
                    comment.edit(body=review_comment)
                    print("Comentário de revisão de código atualizado com sucesso!")
                except Exception as e:
                    print(f"Erro ao atualizar comentário: {e}")
            else:
                # Criar um novo comentário no PR
                try:
                    pull_request.create_issue_comment(review_comment)
                    print("Comentário de revisão de código criado com sucesso!")
                except Exception as e:
                    print(f"Erro ao criar comentário: {e}")
        else:
            print(f"❌ Erro na chamada da API: {response.text}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Erro ao realizar revisão de código: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()