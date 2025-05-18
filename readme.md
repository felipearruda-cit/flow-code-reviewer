# Flow Code Review Automation

Este repositório contém uma solução de automação para geração de descrição de Pull Requests e revisão de código utilizando IA. O fluxo é executado via GitHub Actions e consiste em três scripts principais:

* `collect_pr_info.py`: coleta informações essenciais da PR e salva num arquivo `pr_<número>.pkl`.
* `add_pr_description.py`: gera um resumo (`Flow Code Summary`) da PR e atualiza a descrição no GitHub.
* `code_review.py`: realiza uma análise de código detalhada e publica um comentário estruturado (`Flow Code Reviewer`).

## Estrutura do Projeto

```
.github/
  workflows/
    ai-pr-review.yml        # Definição do workflow de PR
  workflows/scripts/
    collect_pr_info.py      # Coleta dados da PR
    add_pr_description.py   # Gera e insere Flow Code Summary
    code_review.py          # Gera e insere Flow Code Reviewer

README.md                  # Documentação deste repositório
```

## Requisitos

* Python 3.8+
* Biblioteca PyGithub
* requests

## Instalação

1. Clone este repositório:

   ```bash
   git clone https://github.com/seu-usuario/seu-repo.git
   cd seu-repo
   ```

2. Instale dependências num virtualenv:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\\Scripts\\activate  # Windows
   pip install --upgrade pip
   pip install PyGithub requests python-dotenv
   ```

## Variáveis de Ambiente e Secrets

Certifique-se de definir os seguintes *secrets* no GitHub:

* `GITHUB_TOKEN`: token padrão do Actions para acesso à API do GitHub.
* `TOKEN_LLM_API`: token de acesso à API de IA da CI\&T.

Você também pode usar um arquivo `.env` localmente para testes:

```
GITHUB_TOKEN=ghp_...
TOKEN_LLM_API=sk_...
```

## Uso Local

Para executar manualmente cada etapa:

```bash
# 1) Simular evento da PR no arquivo event.json (payload GitHub)
export GITHUB_EVENT_PATH=./event.json
export GITHUB_TOKEN=$GITHUB_TOKEN

# 2) Coletar info da PR\python .github/workflows/scripts/collect_pr_info.py

# 3) Gerar summary\python .github/workflows/scripts/add_pr_description.py

# 4) Gerar revisão\python .github/workflows/scripts/code_review.py
```

## GitHub Actions

O workflow definido em `.github/workflows/ai-pr-review.yml` dispara nas PRs (opened, synchronize):

1. Checkout do código
2. Setup Python
3. Instala dependências
4. Coleta informações da PR
5. Insere/atualiza `Flow Code Summary`
6. Insere/atualiza `Flow Code Reviewer`

## Customização

* Ajuste `max_tokens` e `model` nos scripts conforme necessidade.
* Personalize prompts para adequar tom e formato da IA.

## Contribuição

1. Fork do repositório
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Commit suas alterações: `git commit -m "Descrição da feature"`
4. Envie para o repositório: `git push origin feature/minha-feature`
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
