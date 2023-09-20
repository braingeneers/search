import os
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template
from flask_cors import CORS

import psycopg2

app = Flask(__name__)

# CORS implemented so that we don't get errors when trying to access the server from a different server location
CORS(app)

try:
    p = urlparse(os.environ.get("DATABASE_URL"))
    print(p)
    con = psycopg2.connect(
        host=p.hostname,
        port=p.port,
        database=p.path.split("/")[-1],
        user=p.username,
        password=p.password,
    )

    cur = con.cursor()

    # GET: Fetch all uuid's from the database
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/ping")
    def ping():
        return "pong"

    @app.route("/version")
    def version():
        return "0.0.5"

    @app.route("/uuids")
    def fetch_all_uuids():
        cur.execute("select metadata->'uuid' from experiments;")
        rows = cur.fetchall()
        print(rows)
        return jsonify(rows)

except:
    print("Error starting search application")
