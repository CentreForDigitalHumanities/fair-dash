import asyncio
import httpx
import os
import toml
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Literal

Severity = Literal["red", "yellow", "green"]
Criteria = tuple[str, Severity]
env = Environment(loader=FileSystemLoader("web"))
template = env.get_template("page.jinja2")

@dataclass
class OrganizationConfig:
    name: str
    token_ref: str

@dataclass
class Config:
    organizations: list[OrganizationConfig]

@dataclass
class Repo:
    license: str | None
    url: str
    name: str
    topics: list[str] | None
    is_fork: bool
    description: str | None
    is_private: bool
    is_archived: bool
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
    def archived_check(self) -> Criteria:
        if self.is_archived:
            return "Archived", "yellow"
        else:
            return "Not archived", "green"
        
    @property
    def last_update_check(self) -> Criteria:
        days = (datetime.now() - self.updated).days
        if days < 365:
            return f"{days}  day(s) ago", "green"
        else:
            return f"{days}  day(s) ago", "yellow"
        
@dataclass
class Stats:
    licenses_ok: int
    topics_ok: int
    visibility_ok: int
    description_ok: int
    public_ok: int

    @classmethod
    def from_repos(cls, repos: list[Repo]) -> "Stats":
        licenses_ok = sum(1 for repo in repos if repo.license_check[1] == "green")
        topics_ok = sum(1 for repo in repos if repo.topics_check[1] == "green")
        visibility_ok = sum(1 for repo in repos if repo.visibility_check[1] == "green")
        description_ok = sum(1 for repo in repos if repo.description_check[1] == "green")
        public_ok = sum(1 for repo in repos if repo.visibility == "public")
        return cls(
            licenses_ok=licenses_ok,
            topics_ok=topics_ok,
            visibility_ok=visibility_ok,
            description_ok=description_ok,
            public_ok=public_ok,
        )



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
        is_archived=response["archived"],
        created=created,
        updated=updated,
    )

async def get_org_repos(org: OrganizationConfig) -> list[Repo]:
    token = os.environ[org.token_ref]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Getting repos for {org.name}")
    repos = []
    async with httpx.AsyncClient() as client:
        page = 1
        while True:
            response = await client.get(
                f"https://api.github.com/orgs/{org.name}/repos?page={page}&per_page=100",
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
    print(f"Got {len(repos)} repos for {org.name}")
    return repos

if __name__ == "__main__":
    with open("config.toml") as f:
        data = toml.load(f)
    print("initializing config")
    config = Config(
        organizations=[
            OrganizationConfig(name=org["name"], token_ref=org["token_ref"])
            for org in data["organizations"]
        ]
    )
    repos = []
    for org in config.organizations:
        repos += asyncio.run(get_org_repos(org))
    repos = sorted(repos, key=lambda repo: repo.name)
    out = template.render({"repos": repos})
    with open("public/index.html", "w") as f:
        f.write(out)


