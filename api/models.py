from pydantic import BaseModel


class PaperOut(BaseModel):
    id:          str
    title:       str
    abstract:    str
    authors:     list[str]
    published:   str
    categories:  list[str]
    summary:     str | None
    tldr:        str | None
    task:        str | None
    difficulty:  str | None
    methods:     list[str]
    velocity:    float | None
    inserted_at: str | None

    class Config:
        from_attributes = True


class TaskCount(BaseModel):
    task: str | None
    n:    int


class DateCount(BaseModel):
    published: str
    n:         int


class StatsOut(BaseModel):
    total:    int
    by_task:  list[TaskCount]
    by_date:  list[DateCount]
    trending: list[PaperOut]