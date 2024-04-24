from functools import lru_cache

import flet as ft
import apsw

import boto3
import crawl

conn = apsw.Connection("data/braingeneers.db")

session = boto3.Session(profile_name="prp-braingeneers")
s3 = session.client(
    service_name="s3", endpoint_url="https://s3.braingeneers.gi.ucsc.edu"
)


@lru_cache(maxsize=32)
def list_objects(path):
    """ Returns list of all objects under the given path recursively """
    print(f"Listing {path} objects recursively")
    return [
        p.key
        for p in crawl.s3list(
            client=s3, bucket="braingeneers", path=path, recursive=True
        )
    ]


async def main(page: ft.Page):
    count = conn.execute("SELECT COUNT(*) FROM experiments;").fetchone()[0]
    oldest = conn.execute("SELECT MIN(last_modified) FROM experiments;").fetchone()[0]
    newest = conn.execute("SELECT MAX(last_modified) FROM experiments;").fetchone()[0]
    page.add(ft.Text(f"{count} experiments indexed between {oldest} to {newest}"))

    def handle_experiment_click(e):
        paths = list_objects(e.data)
        print(paths)

    def handle_search(e):
        results.controls.clear()
        for row in conn.execute(  # pylint: disable=not-an-iterable
            f"SELECT rowid, uuid, path, last_modified, snippet(experiments,3, '***', '***', '...',16) FROM experiments('{search.value}*') ORDER BY last_modified DESC;"
        ):
            results.controls.append(
                ft.Markdown(
                    f"[**{row[2]}**]({row[2]}): {row[4]}",
                    on_tap_link=handle_experiment_click,
                )
            )
        page.update()
        search.focus()

    search = ft.TextField(label="Search...", on_submit=handle_search)
    page.add(search)
    search.focus()

    results = ft.ListView()

    page.add(results)


ft.app(target=main)
