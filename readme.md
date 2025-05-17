# AI Pull Request Assistant

Um sistema automatizado de análise e revisão de Pull Requests que utiliza IA para gerar descrições de PR e realizar análises de código, facilitando o processo de revisão.

## 📋 Funcionalidades

- **Geração automática de descrições**: Cria automaticamente uma descrição detalhada e concisa para PRs, baseada nas alterações realizadas
- **Análise de código**: Realiza revisão de código, identificando possíveis problemas e sugerindo melhorias
- **Atualizações incrementais**: Atualiza descrições e análises existentes sem criar duplicatas
- **Histórico de revisões**: Mantém o histórico de análises anteriores para acompanhamento da evolução da PR

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- GitHub Actions
- PyGithub (API do GitHub)
- Modelos de IA da OpenAI (via API CI&T)

## 🚀 Instalação

### Pré-requisitos

- Repositório GitHub
- Permissões para configurar GitHub Actions
- Token de acesso à API de IA

### Configuração

1. **Copie os arquivos do workflow para o seu repositório**:
2. **Configure os secrets necessários no seu repositório**:

Acesse: `Repositório > Settings > Secrets and variables > Actions` e adicione:

- `TOKEN_LLM_API`: Token de acesso à API CI&T de IA

3. **Verifique as permissões**: Certifique-se de que o GITHUB_TOKEN tem permissões para `contents: read` e `pull-requests: write`

## 📝 Uso

O workflow é executado automaticamente quando:

- Um Pull Request é aberto
- Um Pull Request recebe novas alterações (sincronização)

Não é necessária nenhuma ação manual para iniciar o processo.

### Exemplos

Após a execução, você verá:

1. **Descrição da PR atualizada**: