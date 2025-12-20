from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.users import router as users_router
from common.dependencies import Connection, UserDependency
from crud.loved_ones import create_loved_one, delete_loved_one, get_loved_ones, mark_loved_one_called
from db.database import lifespan

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


app.include_router(users_router)


@app.get("/api/loved_ones")
async def get_loved_ones_api(username: UserDependency, conn: Connection):
    return await get_loved_ones(conn, username)


@app.post("/api/loved_ones")
async def create_loved_one_api(name: str, username: UserDependency, conn: Connection):
    return await create_loved_one(conn, username, name)


@app.post("/api/loved_ones/{loved_one_id}/called")
async def mark_called_api(loved_one_name: str, username: UserDependency, conn: Connection):
    loved_one = await mark_loved_one_called(conn, username, loved_one_name)

    if not loved_one:
        raise HTTPException(status_code=404, detail="Loved one not found")

    return loved_one


@app.delete("/api/loved_ones/{loved_one_id}")
async def delete_loved_one_api(loved_one_name: str, username: UserDependency, conn: Connection):
    success = await delete_loved_one(conn, username, loved_one_name)

    if not success:
        raise HTTPException(status_code=404, detail="Loved one not found")

    return {"success": True}
