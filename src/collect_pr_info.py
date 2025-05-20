import os
import json
import pickle
from github import Github

class PRInfoCollector:
    def __init__(self, github_token: str, event_path: str, runner_temp: str):
        self.github_token = github_token
        self.event_path   = event_path
        self.runner_temp  = runner_temp

    def run(self):
        if not self.event_path:
            raise RuntimeError("GITHUB_EVENT_PATH não definido.")
        with open(self.event_path, "r") as f:
            event = json.load(f)

        repo_full_name = event["repository"]["full_name"]
        pr_number      = event["pull_request"]["number"]
        pr_title       = event["pull_request"]["title"]
        pr_body        = event["pull_request"]["body"] or ""

        gh   = Github(self.github_token)
        repo = gh.get_repo(repo_full_name)
        pr   = repo.get_pull(pr_number)

        files = []
        diff_text = ""
        for file in pr.get_files():
            files.append({
                "filename":  file.filename,
                "additions": file.additions,
                "deletions": file.deletions,
                "patch":     file.patch
            })
            if file.patch:
                diff_text += f"\n--- {file.filename}\n{file.patch}\n"

        # === imprime somente a lista de arquivos que serão analisados ===
        print("\n[collect_pr_info] 🗂️  Files to be analyzed:")
        for f in files:
            print(f"  • {f['filename']}")
        print()

        pr_info = {
            "repo_full_name": repo_full_name,
            "pr_number":      pr_number,
            "pr_title":       pr_title,
            "pr_body":        pr_body,
            "file_list":      files,
            "diff_text":      diff_text
        }

        os.makedirs(self.runner_temp, exist_ok=True)
        out_path = os.path.join(self.runner_temp, f"pr_{pr_number}.pkl")
        with open(out_path, "wb") as f:
            pickle.dump(pr_info, f)

        print(f"[collect_pr_info] ✅ saved PR info to {out_path}")

if __name__ == "__main__":
    collector = PRInfoCollector(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        event_path=os.environ.get("GITHUB_EVENT_PATH", ""),
        runner_temp=os.environ.get("RUNNER_TEMP", "/tmp"),
    )
    try:
        collector.run()
    except Exception as e:
        print(f"[collect_pr_info] ❌ {e}")
        exit(1)
