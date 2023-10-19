import os
import streamlit as st

# Initialize connection.
conn = st.experimental_connection(
    name="foo", type="sql", url=os.environ["DATABASE_URL"]
)

st.title("Braingeneers Search")

# Show all uuids
# df = conn.query("select metadata->'uuid' as uuid from experiments;", ttl="0")
# Print results.
# for row in df.itertuples():
#     st.write(f"{row.uuid}")

query = st.text_input("")

if query:
    df = conn.query(
        f"select metadata->'uuid' as uuid from experiments where to_tsvector('english', metadata) @@ to_tsquery('{query}:*')",
        ttl="0",
    )

    for row in df.itertuples():
        st.write(f"{row.uuid}")
