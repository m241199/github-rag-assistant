from pydantic import BaseModel


class RepoCreate(BaseModel):
    github_url: str


class RepoResponse(BaseModel):
    id: str
    github_url: str
    name: str
    branch: str

    class Config:
        orm_mode = True
        from_attributes = True
