import json
from functools import lru_cache
import boto3
import crawl
import apsw
from fastapi import FastAPI
from nicegui import app, ui

session = boto3.Session(profile_name="prp-braingeneers")
app.storage.s3 = session.client(
    service_name="s3", endpoint_url="https://s3.braingeneers.gi.ucsc.edu"
)

app.storage.conn = apsw.Connection("data/braingeneers.db")

fast_app = FastAPI()


@app.get("/hello")
def read_root():
    return {"Hello": "World"}


def search(e):
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
def home():
    app.storage.client["query"] = (
        ui.input(placeholder="Search...")
        .props('autofocus outlined rounded item-aligned input-class="ml-3"')
        .classes("w-96 self-center mt-24 transition-all")
        .on("keydown.enter", search)
    )

    app.storage.client["experiments"] = ui.list().props("dense separator")


@lru_cache(maxsize=32)
def list_objects(path):
    """Returns list of all objects under the given path recursively"""
    print(f"Listing {path} objects recursively")
    return [
        p.key
        for p in crawl.s3list(
            client=app.storage.s3, bucket="braingeneers", path=path, recursive=True
        )
    ]


from nwb import NWB


@ui.page("/nwb/{path:path}")
def nwb(path: str):
    print("Browsing nwb file:", path)
    with ui.card():
        nwb_widget = NWB(
            path, on_change=lambda e: ui.notify(f"The value changed to {e.args}.")
        )

    ui.button("Reset", on_click=nwb_widget.reset).props("small outline")


@ui.page("/experiment/{path:path}")
def experiment(path: str):
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


ui.run_with(fast_app, storage_secret="pick your private secret here")


if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn" command as shown in the start.sh script'
    )
