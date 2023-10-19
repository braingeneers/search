import os
import streamlit as st

# Initialize connection.
conn = st.experimental_connection(
    name="foo", type="sql", url=os.environ["DATABASE_URL"]
)

st.title("Braingeneers Search")

query = st.text_input("Query:", label_visibility="collapsed")

if query:
    df = conn.query(
        f"select metadata->'uuid' as uuid, metadata from experiments where to_tsvector('english', metadata) @@ to_tsquery('{query}:*')",
        ttl="0",
    )

    for row in df.itertuples():
        st.write(f"{row.uuid}")
        st.json(row.metadata, expanded=False)
