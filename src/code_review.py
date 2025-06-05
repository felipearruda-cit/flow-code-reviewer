# src/code_review.py

import os
import pickle
from github import Github
from llm_client import LLMClient


class CodeReviewer:
    def __init__(self,
                 github_token: str,
                 runner_temp:  str,
                 flow_lang:    str = "en"):
        self.github_token = github_token
        self.runner_temp  = runner_temp
        self.flow_lang    = flow_lang

        # LLMClient instanciado com agent "code-reviewer"
        self.llm_client = LLMClient(flow_agent="code-reviewer")

    def run(self):
        # 1) Carrega o arquivo pr_<n>.pkl
        files = [f for f in os.listdir(self.runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("NO pr_*.pkl found in RUNNER_TEMP.")
        with open(os.path.join(self.runner_temp, files[0]), "rb") as f:
            pr = pickle.load(f)

        # 2) Prepara lista de arquivos e diff
        files_txt = "\n".join(
            f"- {finfo['filename']} (+{finfo['additions']}/-{finfo['deletions']})"
            for finfo in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:4000]

        # 3) Prompt com nova seção de Security & Best Practices
        prompt = f"""
Generate a *Flow Code Reviewer* report for this Pull Request.

Please reply **entirely** in **{self.flow_lang}**, and include exactly these sections:

Your report must contain exactly these five sections (translated into the target language) and use markdown for sections:

0. Header - use the title *Flow Code Reviewer*
1. Changes  — a markdown table (File | Description)
2. Suggestions — bullet points with brief code examples
3. Security — identify potential security risks
4. Best Practices — actionable best-practice recommendations and code examples with the changes

Data:
- Files:
{files_txt}

- Diff snippet:
{diff_txt}
"""

        review = self.llm_client.chat(prompt, flow_lang=self.flow_lang, max_tokens=3000)

        # 4) Publica ou atualiza o comentário
        gh    = Github(self.github_token)
        pull  = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
        comment_body = review.strip()

        # Procura comentário existente que comece com o header (ex: "## Flow Code Reviewer")
        existing = None
        for c in pull.get_issue_comments():
            if c.body.lstrip().startswith("## Flow Code Reviewer"):
                existing = c
                break

        if existing:
            existing.edit(comment_body)
            print("[code_review] ✅ Flow Code Reviewer updated.")
        else:
            pull.create_issue_comment(comment_body)
            print("[code_review] ✅ Flow Code Reviewer created.")


if __name__ == "__main__":
    rev = CodeReviewer(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
        flow_lang=os.environ.get("FLOW_LANG", "en")
    )
    try:
        rev.run()
    except Exception as e:
        print(f"[code_review] ❌ {e}")
        exit(1)