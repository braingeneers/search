import os
from PIL import Image
import apsw
import streamlit as st

st.set_page_config(page_title="Braingeneers Search", page_icon="🧠", layout="wide")

conn = apsw.Connection("data/braingeneers.db")


def handle_click(rowid):
    for row in conn.execute(f"SELECT metadata FROM experiments WHERE rowid = {rowid}"):
        st.json(row[0], expanded=True)


with st.sidebar:
    left, right = st.columns([10, 30])
    with left:
        image = Image.open("logo.png")
        st.image(image)
    with right:
        st.title("Braingeneers Search")

    query = st.text_input("Query:", label_visibility="collapsed")

    if query:
        st.write("Experiments found:")
        for row in conn.execute(
            f"SELECT rowid, snippet(experiments,2, ':blue[', ']', '...',8) FROM experiments('{query}*');"
        ):
            st.button(
                f"{row[1]}",
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
