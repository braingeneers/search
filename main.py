"""
UI for Braingeneers Experiments Respository

Notes:
@ui.page define routes driving the nicegui ui
@app.get/head define REST api endpoints via nicegui's underlying fastapi
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize global s3 connection
session = boto3.Session(profile_name=os.getenv("S3_PROFILE", "prp-braingeneers"))
app.storage.s3 = session.client(
    service_name="s3",
    endpoint_url=os.getenv("S3_ENDPOINT", "https://s3.braingeneers.gi.ucsc.edu"),
)

# Initialize global crawled sqlite database connection
app.storage.conn = apsw.Connection(
    "data/braingeneers.db", flags=apsw.SQLITE_OPEN_READONLY
)


"""
Access to NRP S3 objects to support viewing datafiles (i.e. nwb files)

There are two approaches supported here:

s3/: Proxy access to files in S3 with cacheing. This ends up doubling the bandwidth
as the file needs to come from S3 and then to the browser. 

presigned/: Proxy to signed URLs from NRP S3 to object store access for large files
so that the browser can pull directly form S3 avoiding the double bandwidth.
Signed URLs are limited to a single HTTP request method i.e. GET, or HEAD,
but not both. In the browser FS.createLazyFile calls HEAD to get the size
of the file and then GET, but we can only have a single URL so we handle
the HEAD here directly via boto3 and then do a redirect to the signed
URL for subsequent GET requests.
"""


@app.head("/s3/{path:path}", status_code=status.HTTP_204_NO_CONTENT)
@app.head("/presigned/{path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def s3_head(path, response: Response):
    """Handle HEAD request with ContentLength via boto3"""
    logger.info("HEAD: %s", path)
    res = app.storage.s3.head_object(Bucket="braingeneers", Key=path)
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Cache-Control"] = "max-age=3600"
    response.headers["Connection"] = "keep-alive"
    response.headers["Content-Length"] = str(res["ContentLength"])
    response.headers["Content-Type"] = res["ContentType"]
    response.headers["Keep-Alive"] = "timeout=5"


@lru_cache(maxsize=64)
async def get_object_stream(path: str, range: str):
    """Cache chunks on the assumption users will scan back and forth in time"""
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


"""
Search UI
"""


def search(e):
    """Full text sqlite search with snippet highlighting"""
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

    # stack-label 'should' hide the label if None, but doesn't work...
    app.storage.client["query"] = (
        ui.input(label=None, placeholder="Search...")
        .props(
            'stack-label dense autofocus outlined rounded item-aligned input-class="ml-3"'
        )
        .classes("w-96 self-center mt-24 transition-all")
        .on("keydown.enter", search)
    )

    # Count and display count and dates of experiments indexed
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


"""
Experiment UI
"""


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
    ui.markdown(f"# {path.replace('_', '\\_')}")
    ui.markdown("## objects:")
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
    ui.markdown("## metadata.json:")
    key = f"{path}/metadata.json"
    res = app.storage.s3.get_object(Bucket="braingeneers", Key=key)
    metadata = json.loads(res.get("Body").read().decode("utf-8"))
    editor = ui.json_editor({"content": {"json": metadata}})
    editor.run_editor_method("updateProps", {"readOnly": True})


"""
NWB File UI

Note: Experimental and not fully working
"""


@app.get("/static/{path:path}")
def static(path: str):
    """Serve static files with js mimetime corrected for module loading."""
    logger.info("Serving static file: %s", path)
    if path.endswith(".js"):
        return FileResponse(f"static/{path}", media_type="application/javascript")
    else:
        return FileResponse(f"static/{path}")


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
ui.run(show=False)
