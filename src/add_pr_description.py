import os
import pickle
import requests
import json
import re
from github import Github

class PRDescriptionGenerator:
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
        # find the pkl
        files = [f for f in os.listdir(self.runner_temp) if f.startswith("pr_") and f.endswith(".pkl")]
        if not files:
            raise RuntimeError("Nenhum pr_*.pkl encontrado.")
        pkl_path = os.path.join(self.runner_temp, files[0])

        with open(pkl_path, "rb") as f:
            pr = pickle.load(f)

        # prepare prompt
        file_list_txt = "\n".join(
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr["file_list"][:20]
        )
        diff_txt = pr["diff_text"][:2000]

        prompt = f"""
Generate a *Flow Code Summary* for this Pull Request.
Please reply in **{self.flow_lang}**, using:

1) 3–5 bullet points with the main highlights;
2) A **Changes** markdown table (file | short description).

Data:
- Title: {pr['pr_title']}
- Files:
{file_list_txt}

- Diff snippet:
{diff_txt}
"""
        summary = self._call_llm(prompt)

        # strip any old block
        body = pr["pr_body"] or ""
        body = re.sub(r"(?ms)^##\s*Flow Code Summary.*?(?=^##\s|\Z)", "", body).strip()

        # strip duplicate headings from the LLM
        summary = re.sub(r'(?m)^#+\s*Flow Code Summary.*\n', '', summary).strip()

        new_body = f"{body}\n\n## Flow Code Summary\n\n{summary}\n"

        gh   = Github(self.github_token)
        pull= gh.get_repo(pr["repo_full_name"]).get_pull(pr["pr_number"])
        pull.edit(body=new_body)

        print("[add_pr_description] ✅ Flow Code Summary updated")

    def _call_llm(self, prompt: str) -> str:
        url = "https://flow.ciandt.com/ai-orchestration-api/v1/openai/chat/completions"
        payload = json.dumps({
            "stream": False,
            "messages":[{"role":"user","content":prompt}],
            "max_tokens":1000,
            "model":"gpt-4o-mini"
        })
        headers = {
            "FlowTenant":   "flowteam",
            "FlowAgent":    "pr-summary-generator",
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "Authorization":f"Bearer {self.llm_token}"
        }
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

if __name__ == "__main__":
    gen = PRDescriptionGenerator(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        llm_token=   os.environ.get("TOKEN_LLM_API", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
        flow_lang=  os.environ.get("FLOW_LANG", "en")
    )
    try:
        gen.run()
    except Exception as e:
        print(f"[add_pr_description] ❌ {e}")
        exit(1)
