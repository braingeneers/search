import os
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Braingeneers Search", page_icon="🧠", layout="wide")

conn = st.connection(name="search", type="sql", url=os.environ["DATABASE_URL"])


def handle_click(uuid):
    df = conn.query(
        f"select metadata->'uuid' as uuid, metadata as metadata from experiments where metadata->>'uuid' = '{uuid}'",
        ttl="0",
    )
    for row in df.itertuples():
        st.json(row.metadata, expanded=True)


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
        df = conn.query(
            f"select metadata->'uuid' as uuid from experiments where to_tsvector('english', metadata) @@ to_tsquery('{query}:*')",
            ttl="0",
        )
    else:
        st.write("All experiments:")
        df = conn.query(
            "select metadata->'uuid' as uuid from experiments",
            ttl="0",
        )

    for row in df.itertuples():
        st.button(
            f"{row.uuid}",
            key=row.Index,
            args=(f"{row.uuid}",),
            on_click=handle_click,
        )
