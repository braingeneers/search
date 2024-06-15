"""
UI for Braingeneers Experiment Repository
"""

import os
import json
import logging
from functools import lru_cache

import apsw
import boto3

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse, StreamingResponse, FileResponse
from nicegui import app, ui

import crawl
from nwb import NWB


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Initialize global s3 connection
session = boto3.Session(profile_name=os.getenv("S3_PROFILE", "prp-braingeneers"))
app.storage.s3 = session.client(
    service_name="s3",
    endpoint_url=os.getenv("S3_ENDPOINT", "https://s3.braingeneers.gi.ucsc.edu"),
)

# Initialize global crawled database connection
app.storage.conn = apsw.Connection("data/braingeneers.db")


@app.get("/static/{path:path}")
def static(path: str):
    """Serve static files with js mimetime corrected for module loading."""
    if path.endswith(".js"):
        return FileResponse(f"static/{path}", media_type="application/javascript")
    else:
        return FileResponse(f"static/{path}")


#
# Proxy to URLs from NRP S3 to object store access for large files
#
@app.head("/s3/{path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def s3_head(path, response: Response):
    """Handle HEAD request directly returning ContentLength"""
    logger.info("HEAD: %s", path)
    res = app.storage.s3.head_object(Bucket="braingeneers", Key=path)
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Cache-Control"] = "max-age=3600"
    response.headers["Connection"] = "keep-alive"
    response.headers["Content-Length"] = str(res["ContentLength"])
    response.headers["Content-Type"] = res["ContentType"]
    response.headers["Keep-Alive"] = "timeout=5"


@lru_cache(maxsize=32)
async def get_object_stream(path: str, range: str):
    return app.storage.s3.get_object(Bucket="braingeneers", Key=path, Range=range)[
        "Body"
    ].iter_chunks()


@app.get("/s3/{path:path}")
async def s3_get(path: str, request: Request) -> StreamingResponse:
    """Proxy a GET with ranges to S3."""
    logger.info("GET: %s", path)
    range = request.headers.get("Range", "").strip()
    logger.info("Range: %s", range)
    # return StreamingResponse(get_object_stream(path, range))
    return StreamingResponse(
        app.storage.s3.get_object(Bucket="braingeneers", Key=path, Range=range)[
            "Body"
        ].iter_chunks()
    )


#
# Proxy to presigned URLs from NRP S3 to facilitate direct client/browser
# to object store access for large files
#
@app.head("/presigned/{path:path}", status_code=status.HTTP_204_NO_CONTENT)
def s3_presigned_head(path, response: Response):
    """Handle HEAD request directly returning ContentLength"""
    logger.info("HEAD: %s", path)
    res = app.storage.s3.head_object(Bucket="braingeneers", Key=path)
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Cache-Control"] = "max-age=3600"
    response.headers["Connection"] = "keep-alive"
    response.headers["Content-Length"] = str(res["ContentLength"])
    response.headers["Content-Type"] = res["ContentType"]
    response.headers["Keep-Alive"] = "timeout=5"


@app.get("/presigned/{path:path}", response_class=RedirectResponse)
def s3_presigned_get(path: str, request: Request):
    """Handle GET by returning a redirect to a presigned URL in the NRP S3"""
    logger.info("GET: %s", path)
    try:
        presigned_url = app.storage.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "braingeneers", "Key": path},
            ExpiresIn=3600,
        )
        logger.info("Signed URL: %s", presigned_url)
        return RedirectResponse(
            url=presigned_url, status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    except ClientError as e:
        logger.error(e)
        return None


#
# Search UI
#
def search(e):
    """Full text sqlite search with snippets."""
    app.storage.client["query"].classes("mt-2", remove="mt-24")
    app.storage.client["experiments"].clear()
    with app.storage.client["experiments"]:
        for row in app.storage.conn.execute(  # pylint: disable=not-an-iterable
            f"""SELECT rowid, uuid, path, last_modified, snippet(experiments,3, '<span style="color:blue">', '</span>', '...',10) FROM experiments('{e.sender.value}*') ORDER BY last_modified DESC;"""
        ):
            with ui.item(
                row[1],
                on_click=lambda path=row[2]: ui.navigate.to(f"experiment/{path}"),
            ):
                with ui.item_section():
                    ui.html(row[4])


@ui.page("/")
async def home():
    """Search home page"""
    await ui.context.client.connected()

    ui.image("logo.png").style(
        "display: block; margin-left: auto; margin-right: auto; height: 59px; width: 47px"
    )

    app.storage.client["query"] = (
        ui.input(placeholder="Search...")
        .props('autofocus outlined rounded item-aligned input-class="ml-3"')
        .classes("w-96 self-center mt-24 transition-all")
        .on("keydown.enter", search)
    )

    # Count number and dates of experiments indexed
    count = app.storage.conn.execute("SELECT COUNT(*) FROM experiments;").fetchone()[0]
    oldest = app.storage.conn.execute(
        "SELECT MIN(last_modified) FROM experiments;"
    ).fetchone()[0]
    newest = app.storage.conn.execute(
        "SELECT MAX(last_modified) FROM experiments;"
    ).fetchone()[0]
    ui.label(f"{count} indexed experiments\nfrom {oldest} to {newest}").classes(
        "self-center"
    )

    app.storage.client["experiments"] = ui.list().props("dense separator")


#
# Experiment UI
#
@lru_cache(maxsize=32)
def list_objects(path):
    """Returns list of all objects under the given path recursively"""
    logger.info(f"Listing {path} objects recursively")
    return [
        p.key
        for p in crawl.s3list(
            client=app.storage.s3, bucket="braingeneers", path=path, recursive=True
        )
    ]


@ui.page("/experiment/{path:path}")
def experiment(path: str):
    """Single experiment UI with metadata.json and all files listed."""
    ui.markdown(f"## **Path**: {path}")
    paths = list_objects(path)
    with ui.list().props("dense separator"):
        for p in paths:
            if p.endswith(".nwb"):
                ui.item(
                    p,
                    on_click=lambda path=p: ui.navigate.to(f"/nwb/{path}"),
                )
            else:
                ui.item(p)
    key = f"{path}/metadata.json"
    res = app.storage.s3.get_object(Bucket="braingeneers", Key=key)
    metadata = json.loads(res.get("Body").read().decode("utf-8"))
    editor = ui.json_editor({"content": {"json": metadata}})
    editor.run_editor_method("updateProps", {"readOnly": True})


#
# NWB File UI
#
@ui.page("/nwb/{path:path}")
def nwb(path: str):
    """Browse contents of NWB file using h5wasm to read directly."""
    logger.info("Browsing nwb file: %s", path)
    with ui.card():
        nwb_widget = NWB(f"/s3/{path}", "/acquisition/ElectricalSeries/data")
    ui.button("Display", on_click=lambda: nwb_widget.display([0, 10], 0, 5)).props(
        "small outline"
    )


# Initialize and start application
ui.run()
