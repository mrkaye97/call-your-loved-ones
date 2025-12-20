from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator, Field

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def format_date(value: datetime | None) -> str:
    if value is None:
        return "never"

    return value.strftime("%-m/%-d/%Y")


templates.env.filters["format_date"] = format_date

index_file = Path("db/index.json")


class LovedOne(BaseModel):
    name: str
    last_called: datetime | None
    created_at: datetime = Field(default_factory=datetime.now)


class Index(BaseModel):
    version: int
    loved_ones: list[LovedOne]

    @field_validator("loved_ones", mode="after")
    def sort_loved_ones(cls, v: list[LovedOne]) -> list[LovedOne]:
        def sort_key(loved_one: LovedOne) -> tuple[bool, datetime]:
            if loved_one.last_called is None:
                return (False, -loved_one.created_at.timestamp())

            return (True, loved_one.last_called.timestamp())

        return sorted(v, key=sort_key)


def load_index() -> Index:
    if not index_file.exists():
        index_file.parent.mkdir(parents=True, exist_ok=True)
        empty_index = Index(version=1, loved_ones=[])
        save_index(empty_index)
        return empty_index

    return Index.model_validate_json(index_file.read_text())


def save_index(index: Index) -> None:
    index_file.write_text(index.model_dump_json(indent=2))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


@app.get("/")
def index(request: Request) -> HTMLResponse:
    index = load_index()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"loved_ones": index.loved_ones}
    )


@app.post("/loved_ones")
def add_loved_one(request: Request, name: str = Form(...)) -> HTMLResponse:
    index = load_index()
    index.loved_ones.insert(0, LovedOne(name=name, last_called=None))

    save_index(index)

    return templates.TemplateResponse(
        request=request,
        name="loved_ones_list.html",
        context={"loved_ones": index.loved_ones},
    )


@app.post("/loved_ones/{name}/called")
def mark_called(request: Request, name: str) -> HTMLResponse:
    index = load_index()
    for loved_one in index.loved_ones:
        if loved_one.name == name:
            loved_one.last_called = datetime.now()
            break

    save_index(index)

    return templates.TemplateResponse(
        request=request,
        name="loved_ones_list.html",
        context={"loved_ones": index.loved_ones},
    )


@app.delete("/loved_ones/{name}")
def delete_loved_one(request: Request, name: str) -> HTMLResponse:
    index = load_index()
    index.loved_ones = [f for f in index.loved_ones if f.name != name]

    save_index(index)
    return templates.TemplateResponse(
        request=request,
        name="loved_ones_list.html",
        context={"loved_ones": index.loved_ones},
    )
