import asyncio
import httpx
import os
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Literal

Severity = Literal["red", "yellow", "green"]
Criteria = tuple[str, Severity]
env = Environment(loader=FileSystemLoader("web"))
template = env.get_template("page.jinja2")

@dataclass
class Repo:
    license: str | None
    url: str
    name: str
    topics: list[str] | None
    is_fork: bool
    description: str | None
    is_private: bool
    visibility: str
    created: datetime
    updated: datetime

    @property
    def license_check(self) -> Criteria:
        if self.license:
            return self.license, "green"
        else:
            return "No license", "red"
    
    @property
    def topics_check(self) -> Criteria:
        if self.topics:
            return ", ".join(self.topics), "green"
        else:
            return "No topics", "red"
        
    @property
    def visibility_check(self) -> Criteria:
        if self.visibility == "public":
            return "Public", "green"
        elif self.visibility == "internal":
            return "Internal", "yellow"
        else:
            return "Private", "red"
    
    @property
    def description_check(self) -> Criteria:
        if self.description:
            return "Description Available", "green"
        else:
            return "No description", "red"
    
    @property
    def fork_check(self) -> Criteria:
        if self.is_fork:
            return "Fork", "yellow"
        else:
            return "Not a fork", "green"
        
    @property
    def last_update_check(self) -> Criteria:
        days = (datetime.now() - self.updated).days
        if days < 365:
            return f"{days}  day(s) ago", "green"
        else:
            return f"{days}  day(s) ago", "yellow"

async def repo_from_resp(response) -> Repo:
    created = datetime.fromisoformat(response["created_at"].replace("Z", ""))
    updated = datetime.fromisoformat(response["updated_at"].replace("Z", ""))
    return Repo(
        license=response["license"]["name"] if response["license"] else None,
        url=response["html_url"],
        name=response["name"],
        topics=response["topics"] if "topics" in response else None,
        is_fork=response["fork"],
        description=response["description"],
        is_private=response["private"],
        visibility=response["visibility"],
        created=created,
        updated=updated,
    )

async def get_all_repos(org: str, token: str) -> list[Repo]:
    headers = {"Authorization": f"Bearer {token}"}
    repos = []
    async with httpx.AsyncClient() as client:
        page = 1
        while True:
            response = await client.get(
                f"https://api.github.com/orgs/{org}/repos?page={page}&per_page=100",
                headers=headers,
            )
            if response.status_code == 200:
                page_repos = response.json()
                if not page_repos:
                    break
                repos += [await repo_from_resp(repo) for repo in page_repos]
                page += 1
            else:
                response.raise_for_status()
    return repos

if __name__ == "__main__":
    token = os.environ["PAT"]
    org = os.environ["ORG"]
    repos = asyncio.run(get_all_repos(org, token))
    out = template.render({"repos": repos})
    with open("public/index.html", "w") as f:
        f.write(out)


