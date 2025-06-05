# src/add_pr_description.py

import os
import pickle
import re
from github import Github
from llm_client import LLMClient


class PRDescriptionGenerator:
    def __init__(self,
                 github_token: str,
                 runner_temp:  str,
                 flow_lang:    str = "en"):
        self.github_token = github_token
        self.runner_temp  = runner_temp
        self.flow_lang    = flow_lang

        # LLMClient instanciado com agent "pr-summary-generator"
        self.llm_client = LLMClient(flow_agent="pr-summary-generator")

    def run(self):
        # 1) Carrega o arquivo pr_<n>.pkl
        files = [f for f in os.listdir(self.runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("No pr_*.pkl found in RUNNER_TEMP.")
        pkl_path = os.path.join(self.runner_temp, files[0])
        with open(pkl_path, "rb") as f:
            pr = pickle.load(f)

        # 2) Prepara lista de arquivos e trecho do diff
        file_list_txt = "\n".join(
            f"- {finfo['filename']} (+{finfo['additions']}/-{finfo['deletions']})"
            for finfo in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:2000]

        # 3) Prompt instruindo a IA **não** incluir nenhum cabeçalho próprio
        prompt = f"""
Generate a *Flow Code Summary* for this Pull Request.
Please reply in **{self.flow_lang}**, **without** adding any top-level heading or title
(such as "Resumo do Pull Request" or "Flow Code Summary"). We will
prepend "## Flow Code Summary" ourselves.

1) 3–5 bullet points with the main highlights;
2) A **Changes** section as a markdown table (file | short description).

Data:
- Title: {pr['pr_title']}
- Files:
{file_list_txt}

- Diff snippet:
{diff_txt}
"""

        summary = self.llm_client.chat(prompt, flow_lang=self.flow_lang, max_tokens=1000)

        # 4) Remove qualquer bloco antigo de summary no corpo da PR
        body = pr["pr_body"] or ""
        body = re.sub(r"(?ms)^##\s*Flow Code Summary.*?(?=^##\s|\Z)", "", body).strip()

        # 5) Remove eventuais headings duplicados vindos da IA
        summary = re.sub(r'(?m)^#+\s*Flow Code Summary.*\n', '', summary).strip()

        # 6) Monta o novo corpo
        new_body = f"{body}\n\n## Flow Code Summary\n\n{summary}\n"

        # 7) Edita a PR no GitHub
        gh   = Github(self.github_token)
        pull = gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
        pull.edit(body=new_body)

        print("[add_pr_description] ✅ Flow Code Summary updated.")


if __name__ == "__main__":
    gen = PRDescriptionGenerator(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
        flow_lang=os.environ.get("FLOW_LANG", "en")
    )
    try:
        gen.run()
    except Exception as e:
        print(f"[add_pr_description] ❌ {e}")
        exit(1)