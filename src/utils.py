import re
import datetime

def summarize_diff(diff_text):
    """
    Resumir o texto de diferença para análise, limitando o tamanho do texto.
    
    Args:
        diff_text (str): O texto de diferença completo do PR
    
    Returns:
        str: Um resumo ou versão truncada do diff para análise
    """
    # Limite máximo de caracteres para o diff
    MAX_DIFF_SIZE = 10000
    
    if len(diff_text) > MAX_DIFF_SIZE:
        # Truncar o diff para o tamanho máximo permitido
        truncated_diff = diff_text[:MAX_DIFF_SIZE]
        truncated_diff += f"\n\n... [Diff truncado. Tamanho total: {len(diff_text)} caracteres] ..."
        return truncated_diff
    
    return diff_text

def format_review_comment(content, title):
    """
    Formatar o conteúdo da revisão em um comentário para o GitHub.
    
    Args:
        content (str): O conteúdo da análise gerado pela IA
        title (str): O título da seção de análise
    
    Returns:
        str: O comentário formatado para o GitHub
    """
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    comment = f"## 🤖 {title}\n\n"
    comment += f"### Análise realizada em: {now}\n\n"
    comment += content
    comment += "\n\n---\n"
    comment += "_Análise gerada automaticamente por IA. Esta análise pode conter falhas e deve ser revisada por humanos._"
    
    return comment

def get_pr_details(pull_request):
    """
    Obter detalhes relevantes de um Pull Request.
    
    Args:
        pull_request: Objeto de Pull Request do PyGithub
    
    Returns:
        dict: Um dicionário com os detalhes do PR
    """
    details = {
        'title': pull_request.title,
        'description': pull_request.body or "Sem descrição",
        'author': pull_request.user.login,
        'created_at': pull_request.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        'updated_at': pull_request.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        'base_branch': pull_request.base.ref,
        'head_branch': pull_request.head.ref,
        'state': pull_request.state,
        'commits': pull_request.commits,
        'changed_files': pull_request.changed_files,
        'additions': pull_request.additions,
        'deletions': pull_request.deletions,
    }
    
    return details

def find_existing_comment(pull_request, header_text):
    """
    Encontrar um comentário existente no PR com base no cabeçalho.
    
    Args:
        pull_request: Objeto de Pull Request do PyGithub
        header_text (str): Texto do cabeçalho a ser procurado
    
    Returns:
        int or None: ID do comentário encontrado ou None
    """
    for comment in pull_request.get_issue_comments():
        if header_text in comment.body:
            return comment.id
    
    return None

def parse_issue_url(url):
    """
    Extrair número do PR/Issue de uma URL do GitHub.
    
    Args:
        url (str): URL da issue ou PR
    
    Returns:
        int or None: Número da issue/PR ou None se não encontrado
    """
    match = re.search(r'/issues/(\d+)|/pull/(\d+)', url)
    if match:
        return int(match.group(1) or match.group(2))
    return None