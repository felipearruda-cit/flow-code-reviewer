# 🇺🇸 Flow Code Reviewer

[![Tests](https://github.com/felipearruda-cit/flow-code-reviewer/actions/workflows/pr-tests.yml/badge.svg)](https://github.com/felipearruda-cit/flow-code-reviewer/actions/workflows/pr-tests.yml)
[![GitHub issues](https://img.shields.io/github/issues/felipearruda-cit/flow-code-reviewer?style=flat-square)](https://github.com/felipearruda-cit/flow-code-reviewer/issues)
[![GitHub forks](https://img.shields.io/github/forks/felipearruda-cit/flow-code-reviewer?style=flat-square)](https://github.com/felipearruda-cit/flow-code-reviewer/network)
[![GitHub stars](https://img.shields.io/github/stars/felipearruda-cit/flow-code-reviewer?style=flat-square)](https://github.com/felipearruda-cit/flow-code-reviewer/stargazers)


This repository implements automation for **Pull Request description** generation and **code review**, using Flow via GitHub Actions.

## Environment Variables / Secrets

| Name                  | Description                                                                                      | Default |
| --------------------- | ------------------------------------------------------------------------------------------------ | ------- |
| `GITHUB_TOKEN`        | Default GitHub Actions token for authenticating to the GitHub API.                               | —       |
| `AUTH_CLIENT_ID`      | Client ID provided by the auth-engine service to obtain a temporary LLM API token.                | —       |
| `AUTH_CLIENT_SECRET`  | Client Secret provided by the auth-engine service for authentication.                             | —       |
| `AUTH_APP_TO_ACCESS`  | Identifier of the Flow app you want to access (as registered in the auth-engine).                | —       |
| `AUTH_ENGINE_URL`     | Full URL of the auth-engine endpoint. | —       |
| `FLOW_TENANT`         | Tenant name (e.g., `flowteam`) to be sent as `FlowTenant` header when requesting the LLM token. | —       |
| `FLOW_LANG`           | Language (ISO code or name) for the reports, e.g., `en`, `pt`, `zh`.                              | `en`    |
| `TOKEN_LLM_API`       | _(Legacy)_ Direct LLM token, only if you’re bypassing the auth-engine. Otherwise not needed.     | —       |

> **Important:** Each run automatically clears old sections (`Flow Code Summary` and `Flow Code Reviewer Report`) before adding new content.

## GitHub Actions Workflow

The file `.github/workflows/flow-pr-review.yml` triggers on `pull_request: [opened, synchronize, reopened]`. The **Flow Code Reviewer** job runs on every commit:

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

| Nome                 | Descrição                                                                                                       | Padrão |
| -------------------- | --------------------------------------------------------------------------------------------------------------- | ------ |
| `GITHUB_TOKEN`       | Token padrão do GitHub Actions para autenticação na API do GitHub.                                              | —      |
| `AUTH_CLIENT_ID`     | Client ID fornecido pelo serviço de autenticação para obter um token temporário da API de LLM.                  | —      |
| `AUTH_CLIENT_SECRET` | Client Secret fornecido pelo serviço de autenticação para autenticar.                                           | —      |
| `AUTH_APP_TO_ACCESS` | Identificador do app Flow que você quer acessar (registrado no serviço de autenticação).                         | —      |
| `AUTH_ENGINE_URL`    | URL completa do endpoint de autenticação (ex.: `https://flow.ciandt.com/auth-engine-api/v1/api-key/token`).     | —      |
| `FLOW_TENANT`        | Nome do tenant (ex.: `flowteam`) a ser enviado no cabeçalho `FlowTenant` ao solicitar o token LLM.              | —      |
| `FLOW_LANG`          | Idioma (código ISO ou nome) para os relatórios, ex.: `en`, `pt`, `zh`.                                          | `en`   |
| `TOKEN_LLM_API`      | _(Legado)_ Token de LLM direto, só se você estiver omitindo a etapa de autenticação. Caso contrário, não necessário. | —      |



> **Importante:** Cada execução limpa automaticamente as seções antigas (`Flow Code Summary` e `Flow Code Reviewer Report`) antes de adicionar o novo conteúdo.

## Workflow no GitHub Actions

O arquivo `.github/workflows/flow-pr-review.yml` dispara nos eventos `pull_request: [opened, synchronize, reopened]`. O job **Flow Code Reviewer** executa em cada commit:

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