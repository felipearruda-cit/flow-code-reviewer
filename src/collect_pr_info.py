import os
import json
import pickle
from github import Github

def main():
    # Obter variáveis de ambiente
    github_token = os.environ.get("GITHUB_TOKEN")
    github_event_path = os.environ.get("GITHUB_EVENT_PATH")
    
    if not github_event_path:
        print("Erro: GITHUB_EVENT_PATH não definido. Não é possível processar o evento.")
        return
        
    try:
        # Carregar evento
        with open(github_event_path, "r") as f:
            event = json.load(f)
        
        # Extrair detalhes da PR
        repo_full_name = event["repository"]["full_name"]
        pr_number = event["pull_request"]["number"]
        pr_title = event["pull_request"]["title"]
        pr_body = event["pull_request"]["body"] or ""
        
        print(f"Coletando informações da PR #{pr_number} em {repo_full_name}: {pr_title}")
        
        # Inicializar cliente GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Obter diferenças da PR
        file_list = []
        diff_text = ""
        
        print("Obtendo arquivos modificados...")
        for file in pr.get_files():
            file_list.append({
                "filename": file.filename,
                "additions": file.additions,
                "deletions": file.deletions,
                "patch": file.patch
            })
            if file.patch:
                diff_text += f"\n--- {file.filename}\n{file.patch}\n"
        
        print(f"Arquivos processados: {len(file_list)}")
        
        # Salvar informações da PR em arquivo para compartilhar entre os scripts
        pr_info = {
            "repo_full_name": repo_full_name,
            "pr_number": pr_number,
            "pr_title": pr_title,
            "pr_body": pr_body,
            "file_list": file_list,
            "diff_text": diff_text
        }
        
        # Nome do arquivo baseado no número da PR
        pr_filename = f"pr_{pr_number}.pkl"
        temp_dir = os.environ.get('RUNNER_TEMP', '/tmp')
        pr_info_path = os.path.join(temp_dir, pr_filename)
        
        with open(pr_info_path, 'wb') as f:
            pickle.dump(pr_info, f)
        
        print(f"Informações da PR salvas em {pr_info_path}")
        
    except Exception as e:
        print(f"Erro durante a coleta de informações: {str(e)}")
        import traceback; traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
