import os
import json
import pickle

import pytest
from src.collect_pr_info import main as collect_main

class DummyFile:
    def __init__(self):
        self.filename = "file1.txt"
        self.additions = 10
        self.deletions = 2
        self.patch = "--- patch"

class DummyPull:
    def __init__(self):
        self.number = 1
        self.title = "title"
        self.body = None
    def get_files(self):
        return [DummyFile()]

class DummyRepo:
    def get_pull(self, number):
        return DummyPull()

class DummyGithub:
    def __init__(self, token): pass
    def get_repo(self, name): return DummyRepo()

@pytest.fixture(autouse=True)
def env_setup(monkeypatch, tmp_path, tmp_path_factory):
    # Create dummy event.json
    event = {"repository": {"full_name": "repo/name"},
             "pull_request": {"number": 1, "title": "title", "body": "body"}}
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    # Patch Github class
    import src.collect_pr_info as mod
    monkeypatch.setattr(mod, "Github", DummyGithub)
    return tmp_path

def test_collect_pr_info_creates_pkl(env_setup):
    temp = env_setup
    # Run
    collect_main()
    # Assert file exists
    pkl = temp / "pr_1.pkl"
    assert pkl.exists(), "pr_1.pkl should be created"
    data = pickle.loads(pkl.read_bytes())
    assert data["repo_full_name"] == "repo/name"
    assert data["pr_number"] == 1
    assert isinstance(data["file_list"], list)