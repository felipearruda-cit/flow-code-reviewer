import os
import pickle
import requests
import json
from github import Github
from datetime import datetime

class CodeReviewer:
    def __init__(self,
                 github_token: str,
                 llm_token:    str,
                 runner_temp:  str,
                 flow_lang:    str = "en"):
        self.github_token = github_token
        self.llm_token    = llm_token
        self.runner_temp  = runner_temp
        self.flow_lang    = flow_lang

    def run(self):
        # 1) Carrega o arquivo pr_<n>.pkl
        files = [f for f in os.listdir(self.runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("Nenhum pr_*.pkl encontrado em RUNNER_TEMP.")
        with open(os.path.join(self.runner_temp, files[0]), "rb") as f:
            pr = pickle.load(f)

        # 2) Prepara lista de arquivos e diff
        file_list_txt = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:4000]

        # 3) Prompt solicitando sugestões com exemplos de código
        prompt = f"""
Generate a *Flow Code Reviewer* report for this Pull Request.
Please reply in **{self.flow_lang}** and include exactly these sections:

## Resumo das Alterações
- 3–5 bullet points with the main highlights

## Changes
| File | Description |
|------|-------------|
…(your table here)…

## Suggestions
- For each suggestion (bugs, code style, security, performance),
  provide a brief code snippet or example illustrating the improvement.

Data:
- Files:
{file_list_txt}

- Diff snippet:
{diff_txt}
"""

        review = self._call_llm(prompt)

        # 4) Publica ou atualiza o comentário
        gh   = Github(self.github_token)
        pull = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
        comment_body = review.strip()

        existing = next((c for c in pull.get_issue_comments()
                         if c.body.lstrip().startswith("## Resumo das Alterações")), None)
        if existing:
            existing.edit(comment_body)
            print("[code_review] ✅ Flow Code Reviewer atualizado.")
        else:
            pull.create_issue_comment(comment_body)
            print("[code_review] ✅ Flow Code Reviewer criado.")

    def _call_llm(self, prompt: str) -> str:
        url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        payload = json.dumps({
            "stream": False,
            "messages": [{"role":"user","content":prompt}],
            "max_tokens": 3000,
            "model": "gpt-4o-mini"
        })
        headers = {
            "FlowTenant":"flowteam",
            "FlowAgent":"code-reviewer",
            "Content-Type":"application/json",
            "Accept":"application/json",
            "Authorization":f"Bearer {self.llm_token}"
        }
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    rev = CodeReviewer(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        llm_token=   os.environ.get("TOKEN_LLM_API", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
        flow_lang=   os.environ.get("FLOW_LANG", "en")
    )
    try:
        rev.run()
    except Exception as e:
        print(f"[code_review] ❌ {e}")
        exit(1)
