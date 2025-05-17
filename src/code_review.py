# src/code_review.py
import os
import pickle
import requests
import json
from github import Github
import re
from datetime import datetime

def main():
    # Obter variáveis de ambiente
    github_token = os.environ.get("GITHUB_TOKEN")
    access_token = os.environ.get("TOKEN_LLM_API")
    api_url = os.environ.get("AI_API_URL", "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions")
    ai_model = os.environ.get("AI_MODEL", "gpt-4o-mini")
    environment = os.environ.get("ENVIRONMENT", "dev")  # dev por padrão
    
    # Log do ambiente atual
    print(f"Utilizando configurações do ambiente: {environment}")
    print(f"Environment GitHub: ai-pr-review-{environment}")
    print(f"API URL: {api_url}")
    print(f"Modelo AI: {ai_model}")
    
    if not access_token:
        print(f"Erro: TOKEN_LLM_API não está definido! Configure este secret no ambiente 'ai-pr-review-{environment}'.")
        return
    
    try:
        # Carregar informações da PR
        temp_dir = os.environ.get('RUNNER_TEMP', '/tmp')
        pr_info_path = os.path.join(temp_dir, 'pr_info.pkl')
        
        with open(pr_info_path, 'rb') as f:
            pr_info = pickle.load(f)
        
        repo_full_name = pr_info["repo_full_name"]
        pr_number = pr_info["pr_number"]
        pr_title = pr_info["pr_title"]
        pr_body = pr_info["pr_body"]
        file_list = pr_info["file_list"]
        diff_text = pr_info["diff_text"]
        pr_base_ref = pr_info.get("pr_base_ref", "unknown")  # Branch de destino
        saved_environment = pr_info.get("environment", environment)  # Usar environment salvo ou o atual
        
        print("\n" + "="*80)
        print(f"➡️ INICIANDO ETAPA: Análise de Código")
        print("="*80 + "\n")
        
        print(f"Realizando revisão de código para PR #{pr_number} em {repo_full_name}")
        print(f"PR direcionada para branch: {pr_base_ref}")
        
        # Inicializar cliente GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Verifica se já existe um comentário de análise de código
        existing_comment_id = None
        for comment in pr.get_issue_comments():
            if "## Análise de Código por IA" in comment.body:
                existing_comment_id = comment.id
                print(f"Encontrado comentário existente de análise de código (ID: {existing_comment_id})")
                break
                
        # Formatar lista de arquivos para o prompt
        file_list_text = "\n".join([f"- {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in file_list[:20]])
        
        # Criar prompt específico para code review
        prompt = """
        Por favor, analise esta solicitação de Pull Request e realize uma revisão de código detalhada:
        
        Título: {}
        Branch de destino: {}
        Descrição: {}
        
        Arquivos alterados:
        {}
        
        Alterações:
        {}
        
        Forneça uma análise detalhada do código focando em:
        1. Potenciais bugs ou problemas
        2. Qualidade do código e boas práticas
        3. Preocupações de segurança
        4. Considerações de desempenho
        5. Sugestões de melhoria específicas
        
        Estruture sua análise em seções claras e seja objetivo, fornecendo exemplos específicos
        quando possível e sugestões concretas para melhorias.
        """.format(
            pr_title,
            pr_base_ref,
            pr_body[:500] if pr_body else "",
            file_list_text,
            diff_text[:4000]  # Versão completa para análise
        )
        
        print("Chamando API de IA para análise de código...")
        
        # Chamar a API para análise
        code_review = call_ai_service(api_url, access_token, prompt, ai_model, saved_environment)
        
        # Preparar o comentário de revisão
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        review_comment = f"## Análise de Código por IA\n\n"
        
        if existing_comment_id:
            # Se já existe um comentário, adicionar a nova análise mantendo o histórico
            comment = repo.get_issue_comment(existing_comment_id)
            original_content = comment.body
            
            # Adicionar uma linha divisória e a nova análise
            review_comment = (
                original_content + 
                f"\n\n---\n\n### Atualização ({current_date})\n\n" + 
                code_review
            )
            
            # Atualizar o comentário existente
            comment.edit(review_comment)
            print(f"Comentário de revisão existente atualizado (ID: {existing_comment_id}).")
        else:
            # Se não existe, criar um novo comentário
            review_comment += f"### Análise inicial ({current_date})\n\n" + code_review + f"\n\n<sub>Gerado com configurações do ambiente: {saved_environment}</sub>"
            pr.create_issue_comment(review_comment)
            print("Novo comentário de revisão de código postado com sucesso!")
        
        print("\n" + "="*80)
        print("✅ ETAPA CONCLUÍDA: Análise de Código")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Erro ao realizar revisão de código: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

def call_ai_service(api_url, access_token, prompt, model_name, environment):
    """Chamar a API de IA com o prompt fornecido"""
    
    payload = json.dumps({
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 3000,
        "model": model_name
    })
    
    headers = {
        'FlowTenant': 'flowteam',
        'Content-Type': 'application/json',
        'FlowAgent': f'code-reviewer-{environment}',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        print("Enviando requisição para a API...")
        print(f"Usando FlowAgent: code-reviewer-{environment}")
        response = requests.request("POST", api_url, headers=headers, data=payload)
        print(f"Status da resposta: {response.status_code}")
        
        response.raise_for_status()
        
        # Processar a resposta
        result = response.json()
        
        # Extrair a resposta do modelo
        if "choices" in result and len(result["choices"]) > 0:
            if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                return result["choices"][0]["message"]["content"].strip()
        
        # Fallback
        return f"Análise de código não pôde ser formatada corretamente."
            
    except Exception as e:
        print(f"Erro ao chamar serviço de IA: {str(e)}")
        return f"⚠️ Erro ao obter análise de código: {str(e)}"

if __name__ == "__main__":
    main()