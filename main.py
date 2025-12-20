from datetime import datetime
from pathlib import Path
from uuid import UUID

import asyncpg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from api.users import router as users_router
from common.dependencies import Connection, User
from crud.loved_ones import create_loved_one, delete_loved_one, get_loved_ones, mark_loved_one_called
from db.database import lifespan

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(users_router)


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
def delete_loved_one_legacy(request: Request, name: str) -> HTMLResponse:
    index = load_index()
    index.loved_ones = [f for f in index.loved_ones if f.name != name]

    save_index(index)
    return templates.TemplateResponse(
        request=request,
        name="loved_ones_list.html",
        context={"loved_ones": index.loved_ones},
    )


# API endpoints for authenticated users


@app.get("/api/loved_ones")
async def get_loved_ones_api(user: User, conn: asyncpg.Connection = Connection):
    loved_ones = await get_loved_ones(conn, user.id)
    return loved_ones


@app.post("/api/loved_ones")
async def create_loved_one_api(name: str, user: User, conn: asyncpg.Connection = Connection):
    loved_one = await create_loved_one(conn, user.id, name)
    return loved_one


@app.post("/api/loved_ones/{loved_one_id}/called")
async def mark_called_api(loved_one_id: UUID, user: User, conn: asyncpg.Connection = Connection):
    loved_one = await mark_loved_one_called(conn, user.id, loved_one_id)
    if not loved_one:
        raise HTTPException(status_code=404, detail="Loved one not found")
    return loved_one


@app.delete("/api/loved_ones/{loved_one_id}")
async def delete_loved_one_api(loved_one_id: UUID, user: User, conn: asyncpg.Connection = Connection):
    success = await delete_loved_one(conn, user.id, loved_one_id)
    if not success:
        raise HTTPException(status_code=404, detail="Loved one not found")
    return {"success": True}


class MigrationRequest(BaseModel):
    loved_ones: list[dict]


@app.post("/api/migrate")
async def migrate_local_storage(
    request: MigrationRequest, user: User, conn: asyncpg.Connection = Connection
):
    """
    Migrate loved ones from local storage to the server.
    Expects a list of loved ones with name, last_called, and created_at fields.
    """
    for lo_data in request.loved_ones:
        # Create the loved one in the Connection
        loved_one = await create_loved_one(conn, user.id, lo_data["name"])

        # Update last_called if it exists
        if lo_data.get("last_called"):
            await mark_loved_one_called(conn, user.id, loved_one.id)

    # Return all loved ones for the user
    loved_ones = await get_loved_ones(conn, user.id)
    return loved_ones
