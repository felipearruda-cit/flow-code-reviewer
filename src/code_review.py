# src/code_review.py
import os
import pickle
import requests
import json
import re
from github import Github

class CodeReviewer:
    MARKER = "<!-- flow-code-reviewer -->"

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
        # 1) Carrega o pr_<n>.pkl
        temp = self.runner_temp
        pkls = [f for f in os.listdir(temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not pkls:
            raise RuntimeError("Nenhum pr_*.pkl encontrado em RUNNER_TEMP.")
        with open(os.path.join(temp, pkls[0]), "rb") as f:
            pr = pickle.load(f)

        # 2) Prepara arquivos e diff snippet
        files_txt = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:4000]

        # 3) Prompt pedindo 4 sessões, cabeçalhos traduzidos e conteúdo no idioma escolhido
        prompt = f"""
You are an AI assistant. Generate a *Flow Code Reviewer* report for this Pull Request,
responding **entirely** in **{self.flow_lang}**.  

**Your report must have exactly these four sections**, in this order:
1. Changes
2. Suggestions
3. Security
4. Best Practices

**Translate each of these section headers** into the target language **{self.flow_lang}**, and under each header
provide the content in that language. Do not output any other headings or titles.

Data:
- Files:
{files_txt}

- Diff snippet:
{diff_txt}
"""
        review = self._call_llm(prompt).strip()

        # 4) Limpa títulos que a IA possa ter gerado por engano
        review = re.sub(r'(?m)^(#+\s*.+\n)+', '', review).strip()

        # 5) Monta o comentário com cabeçalho fixo + marker
        comment_body = f"{self.MARKER}\n\n## Flow Code Reviewer\n\n{review}"

        # 6) Publica ou atualiza no GitHub
        gh       = Github(self.github_token)
        pull     = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
        existing = next((
            c for c in pull.get_issue_comments()
            if c.body.startswith(self.MARKER)
        ), None)

        if existing:
            existing.edit(comment_body)
            print("[code_review] ✅ comentário atualizado.")
        else:
            pull.create_issue_comment(comment_body)
            print("[code_review] ✅ comentário criado.")

    def _call_llm(self, prompt: str) -> str:
        url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        payload = json.dumps({
            "stream": False,
            "messages": [{"role":"user","content":prompt}],
            "max_tokens": 3000,
            "model": "gpt-4o-mini"
        })
        headers = {
            "FlowTenant":   "flowteam",
            "FlowAgent":    "code-reviewer",
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "Authorization":f"Bearer {self.llm_token}"
        }
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    reviewer = CodeReviewer(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        llm_token=   os.environ.get("TOKEN_LLM_API", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
        flow_lang=   os.environ.get("FLOW_LANG", "en")
    )
    try:
        reviewer.run()
    except Exception as e:
        print(f"[code_review] ❌ {e}")
        exit(1)
