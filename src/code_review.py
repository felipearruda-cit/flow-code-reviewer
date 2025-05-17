import os
import sys
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
    
    # Encontrar arquivo pr_info.pkl
    pr_info_file = "/home/runner/work/_temp/pr_info.pkl"
    if not os.path.exists(pr_info_file):
        print("❌ Arquivo de informações do PR não encontrado!")
        sys.exit(1)
    
    try:
        with open(pr_info_file, 'rb') as f:
            pr_data = pickle.load(f)
        
        # Extrair dados necessários
        pr_number = pr_data.get('pr_number')
        repo_full_name = pr_data.get('repo_full_name')
        pr_title = pr_data.get('pr_title', 'No title available')
        
        if pr_number is None or repo_full_name is None:
            print("❌ Dados do PR incompletos!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo de informações do PR: {e}")
        sys.exit(1)
    
    print(f"Realizando revisão de código para PR #{pr_number} em {repo_full_name}")
    
    print(f"================================================================================")
    print(f"➡️ INICIANDO ETAPA: Análise de Código")
    print(f"================================================================================")
    
    # Obter o diff usando a API REST diretamente - contornar limitações de permissão
    diff_text = ""
    try:
        # Usar a API REST diretamente para obter o diff
        headers = {"Accept": "application/vnd.github.v3.diff", "Authorization": f"token {github_token}"}
        diff_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
        
        print(f"Obtendo diff da URL: {diff_url}")
        response = requests.get(diff_url, headers=headers)
        
        if response.status_code == 200:
            diff_text = response.text
        else:
            print(f"❌ Erro ao obter diff: {response.status_code} - {response.text}")
            
            # Tentar outro método: buscar arquivos alterados
            files_url = f"{diff_url}/files"
            print(f"Tentando obter arquivos modificados de: {files_url}")
            
            files_response = requests.get(files_url, headers={"Authorization": f"token {github_token}"})
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                diff_text = "Arquivos modificados:\n\n"
                
                for file in files_data:
                    diff_text += f"Arquivo: {file.get('filename')}\n"
                    diff_text += f"Status: {file.get('status')}\n"
                    diff_text += f"Alterações: +{file.get('additions', 0)} -{file.get('deletions', 0)}\n"
                    
                    # Obter patch se disponível
                    if 'patch' in file:
                        diff_text += f"\n{file['patch']}\n\n"
            else:
                print(f"❌ Erro ao obter arquivos modificados: {files_response.status_code} - {files_response.text}")
                diff_text = "Não foi possível obter as alterações do PR."
                
    except Exception as e:
        print(f"❌ Erro ao obter o diff do PR: {e}")
        diff_text = "Erro ao obter alterações do PR."
    
    # Verificar se conseguimos obter algum conteúdo
    if not diff_text or diff_text == "Não foi possível obter as alterações do PR." or diff_text == "Erro ao obter alterações do PR.":
        print("❌ Não foi possível obter o diff do PR. Encerrando.")
        sys.exit(1)
    
    # Resumir o diff para análise
    diff_summary = summarize_diff(diff_text)
    
    # Preparar os detalhes do PR (simplificados, sem usar a API PyGithub diretamente)
    pr_details = {
        'title': pr_title,
        'description': "No description available"
    }
    
    # Tentar obter mais detalhes do PR via API REST
    try:
        pr_details_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
        pr_response = requests.get(pr_details_url, headers={"Authorization": f"token {github_token}"})
        
        if pr_response.status_code == 200:
            pr_info = pr_response.json()
            pr_details['description'] = pr_info.get('body') or "No description available"
    except Exception as e:
        print(f"Aviso: Não foi possível obter descrição detalhada do PR: {e}")
    
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
            
            # Publicar comentário usando a API REST diretamente
            try:
                comment_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
                comment_headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
                comment_data = {"body": review_comment}
                
                comment_response = requests.post(comment_url, headers=comment_headers, json=comment_data)
                
                if comment_response.status_code in [201, 200]:
                    print("✅ Comentário de revisão de código publicado com sucesso!")
                else:
                    print(f"❌ Erro ao publicar comentário: {comment_response.status_code} - {comment_response.text}")
            except Exception as e:
                print(f"❌ Erro ao publicar comentário: {e}")
        else:
            print(f"❌ Erro na chamada da API: {response.status_code} - {response.text}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Erro ao realizar revisão de código: {e}")
        sys.exit(1)
    
    print("✅ Processo de revisão de código concluído!")

if __name__ == "__main__":
    main()