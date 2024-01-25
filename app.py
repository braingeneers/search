import os
from PIL import Image
import apsw
import streamlit as st

st.set_page_config(page_title="Braingeneers Search", page_icon="🧠", layout="wide")

conn = apsw.Connection("data/braingeneers.db")


def handle_click(rowid):
    row = conn.execute(
        f"SELECT uuid, path, last_modified, metadata FROM experiments WHERE rowid = {rowid}"
    ).fetchone()
    st.title(row[0])
    st.text(row[1])
    st.text(f"Last modified: {row[2]}")
    st.json(row[3], expanded=True)


with st.sidebar:
    left, right = st.columns([10, 30])
    with left:
        image = Image.open("logo.png")
        st.image(image)
    with right:
        st.title("Braingeneers Search")

    oldest = conn.execute("SELECT MIN(last_modified) FROM experiments;").fetchone()[0]
    newest = conn.execute("SELECT MAX(last_modified) FROM experiments;").fetchone()[0]
    st.text(f"From {oldest} to {newest}")

    query = st.text_input("Query:", label_visibility="collapsed")

    if query:
        st.write("Experiments found:")
        for row in conn.execute(
            f"SELECT rowid, uuid, last_modified, snippet(experiments,3, ':green[', ']', '...',8) FROM experiments('{query}*');"
        ):
            st.button(
                f":blue[{row[1]}]\n\n{row[3]}",
                key=row[0],
                args=(row[0],),
                on_click=handle_click,
            )
    else:
        st.write("All experiments:")
        for row in conn.execute("select rowid, uuid from experiments"):
            st.button(
                f"{row[1]}",
                key=row[0],
                args=(row[0],),
                on_click=handle_click,
            )
