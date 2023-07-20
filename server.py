import os
from urllib.parse import urlparse

from flask import Flask, jsonify
from flask_cors import CORS

import psycopg2

app = Flask(__name__)

# CORS implemented so that we don't get errors when trying to access the server from a different server location
CORS(app)

try:
    p = urlparse(os.environ.get("DATABASE_URL"))
    con = psycopg2.connect(
        host=p.scheme,
        port=p.port,
        database=p.hostname,
        user=p.username,
        password=p.password,
    )

    cur = con.cursor()

    # GET: Fetch all uuid's from the database
    @app.route("/")
    def fetch_all_uuids():
        cur.execute("select metadata->'uuid' from experiments limit 5;")
        rows = cur.fetchall()
        print(rows)
        return jsonify(rows)

except:
    print("Error")
