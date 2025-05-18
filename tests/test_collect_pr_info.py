import os
import json
import pickle
import pytest
from src.collect_pr_info import PRInfoCollector

# Fixtures para simular o evento e o GitHub
class DummyFile:
    filename = "foo.py"
    additions = 5
    deletions = 1
    patch = "patch foo"

class DummyPR:
    def __init__(self, files):
        self._files = files
    def get_files(self):
        return self._files

class DummyRepo:
    def __init__(self, pr):
        self._pr = pr
    def get_pull(self, number):
        return self._pr

class DummyGithub:
    def __init__(self, token):
        pass
    def get_repo(self, full_name):
        # Simula PR com um único arquivo
        return DummyRepo(DummyPR([DummyFile()]))

@pytest.fixture(autouse=True)
def prepare_env(tmp_path, monkeypatch):
    # Cria um event.json simulado
    evt = {
        "repository": {"full_name": "user/repo"},
        "pull_request": {"number": 42, "title": "My PR", "body": "Initial body"}
    }
    evt_path = tmp_path / "event.json"
    evt_path.write_text(json.dumps(evt))

    # Ajusta variáveis de ambiente
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(evt_path))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))

    # Injeta DummyGithub em vez do real
    monkeypatch.setattr("src.collect_pr_info.Github", DummyGithub)

    return tmp_path

def test_pr_info_collector_creates_pkl(prepare_env):
    temp_dir = str(prepare_env)
    collector = PRInfoCollector(
        github_token=os.environ["GITHUB_TOKEN"],
        event_path=os.environ["GITHUB_EVENT_PATH"],
        runner_temp=temp_dir
    )
    collector.run()

    # Verifica se o arquivo foi criado
    pkl_file = prepare_env / "pr_42.pkl1"
    assert pkl_file.exists(), "O arquivo pr_42.pkl deve existir"

    # Carrega e valida conteúdo básico
    data = pickle.loads(pkl_file.read_bytes())
    assert data["repo_full_name"] == "user/repo"
    assert data["pr_number"] == 42
    assert isinstance(data["file_list"], list)
    assert data["file_list"][0]["filename"] == "foo.py"
