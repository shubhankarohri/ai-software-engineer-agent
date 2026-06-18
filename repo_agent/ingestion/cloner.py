
import os
import shutil
import re
import git
from pathlib import Path


class RepoCloner:
    GITHUB_URL_PATTERN = re.compile(
        r"^https://github\.com/[\w\-\.]+/[\w\-\.]+(\.git)?$"
    )

    def __init__(self, base_dir: str = "data/repos"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.repo = None
        self.repo_path = None

    def _validate_url(self, url: str) -> None:
        if not self.GITHUB_URL_PATTERN.match(url):
            raise ValueError(
                f"Invalid GitHub URL: '{url}'\n"
                f"Expected format: https://github.com/owner/repo"
            )

    def _extract_repo_name(self, url: str) -> str:
        name = url.rstrip("/").split("/")[-1]
        return name.removesuffix(".git")

    def clone(self, url: str, force_reclone: bool = False) -> Path:
        self._validate_url(url)
        repo_name = self._extract_repo_name(url)
        target_path = self.base_dir / repo_name

        if target_path.exists():
            if force_reclone:
                print(f"  Removing existing clone at {target_path} ...")
                shutil.rmtree(target_path)
            else:
                print(f"  ✓ Repo already cloned at: {target_path}")
                self.repo_path = target_path
                self.repo = git.Repo(target_path)
                return target_path

        print(f"  Cloning '{repo_name}' from GitHub...")
        try:
            self.repo = git.Repo.clone_from(
                url=url,
                to_path=str(target_path),
                depth=1,
            )
            self.repo_path = target_path
            print(f"  ✓ Cloned to: {target_path}")
            return target_path

        except git.exc.GitCommandError as e:
            if target_path.exists():
                shutil.rmtree(target_path)
            raise RuntimeError(f"Clone failed: {e}") from e

    def get_repo_metadata(self) -> dict:
        if not self.repo:
            raise RuntimeError("No repo cloned yet. Call .clone() first.")

        head = self.repo.head.commit
        return {
            "name": self.repo_path.name,
            "local_path": str(self.repo_path),
            "head_commit_sha": head.hexsha[:7],
            "head_commit_message": head.message.strip(),
            "head_commit_author": str(head.author),
        }
