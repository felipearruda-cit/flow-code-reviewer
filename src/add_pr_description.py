# src/add_pr_description.py
import os
import pickle
import requests
import json
from github import Github
import re

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
        pr_body = pr_info["pr_body"] or ""
        file_list = pr_info["file_list"]
        diff_text = pr_info["diff_text"]
        pr_base_ref = pr_info.get("pr_base_ref", "unknown")  # Branch de destino
        saved_environment = pr_info.get("environment", environment)  # Usar environment salvo ou o atual
        
        print("\n" + "="*80)
        print(f"➡️ INICIANDO ETAPA: Geração da Descrição da PR")
        print("="*80 + "\n")
        
        print(f"Gerando descrição para PR #{pr_number} em {repo_full_name}")
        print(f"PR direcionada para branch: {pr_base_ref}")
        
        # Verificar se já existe uma descrição gerada por IA
        has_ai_description = "## Descrição Gerada por IA" in pr_body
        
        # Formatar lista de arquivos para o prompt
        file_list_text = "\n".join([f"- {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in file_list[:20]])
        
        # Criar prompt específico para descrição
        prompt = """
        Por favor, analise esta solicitação de Pull Request e crie uma descrição concisa e informativa:
        
        Título: {}
        Branch de destino: {}
        
        Arquivos alterados:
        {}
        
        Alterações principais:
        {}
        
        Forneça uma descrição clara e concisa desta PR em 3-5 parágrafos, incluindo:
        1. O propósito principal desta alteração
        2. Quais arquivos/componentes principais são afetados
        3. Quaisquer considerações importantes ou dependências
        
        Mantenha um tom profissional e foque nos aspectos técnicos mais relevantes.
        """.format(
            pr_title,
            pr_base_ref,
            file_list_text,
            diff_text[:2000]  # Versão mais reduzida para descrição
        )
        
        print("Chamando API de IA para gerar descrição...")
        
        # Chamar a API para análise
        description = call_ai_service(api_url, access_token, prompt, ai_model, saved_environment)
        
        # Inicializar cliente GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Atualizar descrição da PR
        if has_ai_description:
            print("Uma descrição gerada por IA já existe. Atualizando...")
            # Substituir a parte da descrição gerada por IA existente
            pattern = r"(## Descrição Gerada por IA\n\n)(.+?)(\n\n|\Z)"
            new_body = re.sub(pattern, f"## Descrição Gerada por IA\n\n{description}\n\n", pr_body, flags=re.DOTALL)
            if new_body == pr_body:
                # Se o padrão não foi encontrado, simplesmente adicione no final
                new_body = pr_body + f"\n\n## Descrição Gerada por IA\n\n{description}"
        elif not pr_body or pr_body.strip() == "" or pr_body == "No description provided.":
            # Se não houver descrição, use apenas a gerada
            print("Nenhuma descrição existente. Criando uma nova...")
            new_body = f"## Descrição Gerada por IA\n\n{description}"
        else:
            # Se houver uma descrição manual, adicione a gerada por IA no final
            print("Adicionando descrição gerada por IA à descrição existente...")
            new_body = pr_body + f"\n\n## Descrição Gerada por IA\n\n{description}"
        
        # Adicionar nota sobre o ambiente usado
        new_body += f"\n\n<sub>Gerado com configurações do ambiente: {saved_environment}</sub>"
        
        # Atualizar a PR
        pr.edit(body=new_body)
        print("Descrição da PR atualizada com sucesso!")
        
        print("\n" + "="*80)
        print("✅ ETAPA CONCLUÍDA: Geração da Descrição da PR")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Erro ao adicionar descrição: {str(e)}")
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
        "max_tokens": 1000,  # Menor para descrições
        "model": model_name
    })
    
    headers = {
        'FlowTenant': 'flowteam',
        'Content-Type': 'application/json',
        'FlowAgent': f'pr-description-generator-{environment}',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        print("Enviando requisição para a API...")
        print(f"Usando FlowAgent: pr-description-generator-{environment}")
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
        return f"Descrição gerada automaticamente para PR"
            
    except Exception as e:
        print(f"Erro ao chamar serviço de IA: {str(e)}")
        return f"⚠️ Não foi possível gerar descrição: {str(e)}"

if __name__ == "__main__":
    main()