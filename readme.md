# 🇺🇸 Flow Code Reviewer

[![PR Tests](https://github.com/felipearruda-cit/flow-code-reviewer/actions/workflows/pr-tests.yml/badge.svg)](https://github.com/felipearruda-cit/flow-code-reviewer/actions/workflows/pr-tests.yml)

This repository implements automation for **Pull Request description** generation and **code review**, using Flow via GitHub Actions.

## Environment Variables / Secrets

| Name            | Description                                                          | Default |
| --------------- | -------------------------------------------------------------------- | ------- |
| `GITHUB_TOKEN`  | Default GitHub Actions token for authenticating to the GitHub API.   | —       |
| `TOKEN_LLM_API` | Access token for CI\&T's AI service.                                 | —       |
| `FLOW_LANG`     | Language (ISO code or name) for the reports, e.g., `en`, `pt`, `zh`. | `en`    |

> **Important:** Each run automatically clears old sections (`Flow Code Summary` and `Flow Code Reviewer Report`) before adding new content.

## GitHub Actions Workflow

The file `.github/workflows/ai-pr-review.yml` triggers on `pull_request: [opened, synchronize]`. The **Flow Code Reviewer** job runs on every commit:

## Customization

* Adjust `max_tokens`, `model`, and prompts in the scripts to control size and format.
* The `FLOW_LANG` secret accepts any language code or name; the AI will respond in the specified language.

## Contributing

1. Fork this repository
2. Create a branch: `git checkout -b feature/new-feature`
3. Commit: `git commit -m "Your change description"`
4. Push: `git push origin feature/new-feature`
5. Open a Pull Request

---

# 🇧🇷 Flow Code Reviewer

Este repositório implementa automação para geração de **descrição** e **revisão de código** de Pull Requests, usando Flow via GitHub Actions.

## Variáveis de Ambiente / Secrets

| Nome            | Descrição                                                             | Default |
| --------------- | --------------------------------------------------------------------- | ------- |
| `GITHUB_TOKEN`  | Token padrão do GitHub Actions para autenticação na API do GitHub.    | —       |
| `TOKEN_LLM_API` | Token de acesso ao serviço de IA da CI\&T.                            | —       |
| `FLOW_LANG`     | Idioma (código ISO ou nome) para os relatórios, ex: `en`, `pt`, `zh`. | `en`    |

> **Importante:** Cada execução limpa automaticamente as seções antigas (`Flow Code Summary` e `Flow Code Reviewer Report`) antes de adicionar o novo conteúdo.

## Workflow no GitHub Actions

O arquivo `.github/workflows/ai-pr-review.yml` dispara nos eventos `pull_request: [opened, synchronize]`. O job **Flow Code Reviewer** executa em cada commit:

## Personalização

* Ajuste `max_tokens`, `model` e prompts nos scripts para controlar tamanho e formato.
* O secret `FLOW_LANG` aceita qualquer código ou nome de idioma; a IA responderá no idioma especificado.

## Contribuição

1. Faça um fork deste repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m "Descrição da sua mudança"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---