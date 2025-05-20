# src/code_review.py
import os
import pickle
import requests
import json
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
        files = [f for f in os.listdir(temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("Nenhum pr_*.pkl encontrado em RUNNER_TEMP.")
        with open(os.path.join(temp, files[0]), "rb") as f:
            pr = pickle.load(f)

        # 2) Prepara arquivos e diff snippet
        files_txt = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:4000]

        # 3) Prompt pede à AI que gere cabeçalhos no idioma escolhido
        prompt = f"""
Generate a *Flow Code Reviewer* report for this Pull Request.
Please reply in **{self.flow_lang}**.  
Include whatever headings and structure you like (Summary, Changes, Suggestions, Security & Best Practices, etc.) — 
no need for any English / Portuguese fallbacks; just use the chosen language.

Data:
- Files:
{files_txt}

- Diff snippet:
{diff_txt}
"""
        review = self._call_llm(prompt).strip()

        # 4) Prepara o corpo do comentário, sempre prefixando com o marker
        comment_body = f"{self.MARKER}\n\n{review}"

        # 5) Publica ou atualiza no GitHub
        gh   = Github(self.github_token)
        pull = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])

        existing = next((
            c for c in pull.get_issue_comments()
            if c.body.startswith(self.MARKER)
        ), None)

        if existing:
            existing.edit(comment_body)
            print("[code_review] ✅ comentário atualizado")
        else:
            pull.create_issue_comment(comment_body)
            print("[code_review] ✅ comentário criado")

    def _call_llm(self, prompt: str) -> str:
        url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        payload = json.dumps({
            "stream": False,
            "messages":[{"role":"user","content":prompt}],
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
        return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    import sys
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
        sys.exit(1)
