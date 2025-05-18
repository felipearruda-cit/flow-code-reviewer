# Flow Code Review Automation

Este repositório implementa uma automação de **geração de descrição** e **revisão de código** para Pull Requests, utilizando IA, via GitHub Actions.

## Scripts Principais

* **collect\_pr\_info.py**
  Coleta detalhes da PR (título, descrição, lista de arquivos e diff) e salva em `pr_<número_da_PR>.pkl`.

* **add\_pr\_description.py**
  Gera o **Flow Code Summary** e atualiza a descrição da PR no GitHub, removendo qualquer seção antiga antes de inserir a nova.

* **code\_review\.py**
  Gera o **Flow Code Reviewer**, publicando um comentário com três seções: `Resumo das Alterações`, `Changes` e `Suggestions`. Sobrescreve o comentário anterior, garantindo que fique atualizado por commit.

## Variáveis de Ambiente / Secrets

| Nome            | Descrição                                                          | Default |
| --------------- | ------------------------------------------------------------------ | ------- |
| `GITHUB_TOKEN`  | Token padrão do GitHub Actions para autenticação na API do GitHub. | —       |
| `TOKEN_LLM_API` | Token de acesso ao serviço de IA da CI\&T.                         | —       |
| `FLOW_LANG`     | Idioma (ISO ou nome) para os relatórios. Ex: `en`, `pt`, `zh`.     | `en`    |

> **Importante:**
> Cada execução limpa automaticamente as seções antigas (`Flow Code Summary` e `Flow Code Reviewer Report`) antes de adicionar o conteúdo gerado.

## Workflow no GitHub Actions

O arquivo `.github/workflows/ai-pr-review.yml` dispara nos eventos `pull_request: [opened, synchronize]`. O job **Flow Code Reviewer** executa em cada commit:

```yaml
name: Flow Pull Request Reviewer

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  ai-review:
    name: Flow Code Reviewer
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests PyGithub python-dotenv

      - name: 🔍 Collect PR Info
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
        run: python src/collect_pr_info.py

      - name: 📝 Add PR Description
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
          TOKEN_LLM_API:  \${{ secrets.TOKEN_LLM_API }}
          FLOW_LANG:      \${{ secrets.FLOW_LANG }}
        run: python src/add_pr_description.py

      - name: 🔍 Code Review Analysis
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
          TOKEN_LLM_API:  \${{ secrets.TOKEN_LLM_API }}
          FLOW_LANG:      \${{ secrets.FLOW_LANG }}
        run: python src/code_review.py
```

## Uso Local

1. Configure um arquivo `event.json` com payload de PR e exporte:

   ```bash
   export GITHUB_EVENT_PATH=./event.json
   export GITHUB_TOKEN=ghp_...
   export TOKEN_LLM_API=sk_...
   export FLOW_LANG=pt  # ou outro idioma
   ```
2. Execute passo a passo:

   ```bash
   python src/collect_pr_info.py
   python src/add_pr_description.py
   python src/code_review.py
   ```

## Personalização

* Ajuste `max_tokens`, `model` e prompts nos scripts para controlar tamanho e formato.
* O secret `FLOW_LANG` aceita qualquer código ou nome de idioma, e a IA responderá no idioma especificado.

## Contribuição

1. Fork deste repositório
2. Crie branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m "Descrição da sua mudança"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

> Mantido sob [MIT License](LICENSE).