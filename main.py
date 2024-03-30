from contextlib import asynccontextmanager

import apsw

import flet as ft
import flet.fastapi as flet_fastapi

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    await flet_fastapi.app_manager.start()
    yield
    await flet_fastapi.app_manager.shutdown()


app = FastAPI(lifespan=lifespan)

conn = apsw.Connection("data/braingeneers.db")


async def main(page: ft.Page):
    count = conn.execute("SELECT COUNT(*) FROM experiments;").fetchone()[0]
    oldest = conn.execute("SELECT MIN(last_modified) FROM experiments;").fetchone()[0]
    newest = conn.execute("SELECT MAX(last_modified) FROM experiments;").fetchone()[0]
    stats = ft.Text(f"{count} experiments indexed between {oldest} to {newest}")

    def btn_click(e):
        page.add(ft.Text(f"Hello, {txt_name.value}!"))

    txt_name = ft.TextField(label="Query")

    page.add(stats, txt_name, ft.ElevatedButton("Search", on_click=btn_click))


app.mount("/flet-app", flet_fastapi.app(main))

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/s3/{path:path}")
async def s3_head(path):
    return path


ft.app(target=main)
