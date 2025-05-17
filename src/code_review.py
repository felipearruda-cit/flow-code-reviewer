import os
import sys
import glob
import pickle
import requests
import pprint
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
    
    # Lista de possíveis localizações para procurar o arquivo
    possible_locations = [
        "/home/runner/work/_temp/pr_info.pkl",  # Localização no GitHub Actions
        os.path.join(os.getcwd(), "pr_info.pkl"),  # Diretório atual
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pr_info.pkl")  # Raiz do projeto
    ]
    
    # Buscar o arquivo em todas as localizações possíveis
    pr_info_file = None
    for location in possible_locations:
        if os.path.exists(location):
            pr_info_file = location
            print(f"Arquivo PR info encontrado em: {location}")
            break
    
    if not pr_info_file:
        print("❌ Arquivo de informações do PR não encontrado em nenhum local esperado!")
        
        # Como último recurso, tentar buscar qualquer arquivo pr_info.pkl no sistema
        temp_dir = "/home/runner/work/_temp"
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "pr_info.pkl":
                        pr_info_file = os.path.join(root, file)
                        print(f"Encontrado arquivo PR info em: {pr_info_file}")
                        break
                if pr_info_file:
                    break
        
        if not pr_info_file:
            sys.exit(1)
    
    try:
        with open(pr_info_file, 'rb') as f:
            pr_data = pickle.load(f)
            
        # Debug - imprimir estrutura do arquivo para entender as chaves disponíveis
        print("Estrutura do arquivo pr_info.pkl:")
        pprint.pprint(pr_data)
        
        # Usar o formato correto que vimos nos logs:
        # - 'pr_number' em vez de 'number'
        # - 'repo_full_name' está correto
        
        # Extração dos dados com verificações de segurança
        pr_number = pr_data.get('pr_number')
        repo_full_name = pr_data.get('repo_full_name')
        
        # Verificar se conseguimos obter as informações básicas
        if pr_number is None or repo_full_name is None:
            print("❌ Campos necessários não encontrados no arquivo:")
            print(f"  - pr_number: {pr_number}")
            print(f"  - repo_full_name: {repo_full_name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo de informações do PR: {e}")
        sys.exit(1)
    
    print(f"Realizando revisão de código para PR #{pr_number} em {repo_full_name}")
    
    repo = g.get_repo(repo_full_name)
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