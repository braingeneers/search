# /usr/bin/env python
"""
Index any .json files found in the latest braingeneers aws inventory file by storing them as a jsonb column in a postgres table.

Assumptions:
Bucket is write only so if the key exists in postrgres then it does not need to be updated.
"""
import os
import io
import argparse

import pandas as pd

import boto3

import psycopg2
from urllib.parse import urlparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Index json files from the latest aws inventory file")
    parser.add_argument("--bucket", default="braingeneers",
                        help="S3 bucket")
    parser.add_argument("--profile", default="prp-braingeneers",
                        help="S3 credentials profile name")
    parser.add_argument("--prefix", default="services/data-lifecycle/aws-inventory/",
                        help="S3 inventory path prefix")
    args = parser.parse_args()

    session = boto3.Session()
    s3 = session.client(
        service_name="s3",
        endpoint_url="https://s3-west.nrp-nautilus.io",
    )

    # Download the latest S3 inventory file
    response = s3.list_objects_v2(Bucket=args.bucket, Prefix=args.prefix)

    # Exclude the parent directory file '/' which is zero bytes
    files = [f for f in response["Contents"] if f["Size"] > 0]

    # Sort by date and load the latest into a dataframe
    latest = sorted(files, key=lambda obj: obj["LastModified"])[-1]["Key"]

    obj = s3.get_object(Bucket=args.bucket, Key=latest)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()), compression="gzip",
                     names=["bucket", "key", "version", "latest", "?",
                            "size", "created", "etag", "class", "??", "???", "encryption"],
                     parse_dates=["created"])
    print(f"Found {df.shape[0]:,} files in the inventory")

    # Find all json files
    df = df.loc[df["key"].str.endswith(".json")]
    print(
        f"Unique json file names: {set([key.split('/')[-1] for key in df.key])}")

    p = urlparse(os.environ.get("DATABASE_URL"))
    with psycopg2.connect(
            host=p.scheme,
            port=p.port,
            database=p.hostname,
            user=p.username,
            password=p.password) as con:

        with con.cursor() as cur:
            cur.execute("""
                DELETE FROM experiments;
            """)

        for i, row in df.iterrows():
            path = "/".join(row.key.strip("/").split("/")[1:])
            print(f"Indexing {path}")

            res = s3.get_object(Bucket=args.bucket, Key=path)
            content = res.get("Body").read()

            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO experiments (key, metadata) VALUES (%s, %s);
                """, (path, content.decode("utf-8")))

            con.commit()

    print("Done.")
