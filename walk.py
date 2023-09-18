# /usr/bin/env python
"""
Walk the braingeneers prp top level experiment types (ephys, imaging etc...)
"""
import os
import random
import argparse
from collections import namedtuple
from operator import attrgetter

from tqdm import tqdm

import psycopg2
from urllib.parse import urlparse

import boto3
import pandas as pd

S3Obj = namedtuple("S3Obj", ["key", "mtime", "size", "ETag"])


def s3list(
    client,
    bucket,
    path,
    start=None,
    end=None,
    recursive=True,
    list_dirs=True,
    list_objs=True,
    limit=None,
):
    """
    https://stackoverflow.com/questions/35803027/retrieving-subfolders-names-in-s3-bucket-from-boto3

    Iterator that lists a bucket's objects under path, (optionally) starting with
    start and ending before end.

    If recursive is False, then list only the "depth=0" items (dirs and objects).

    If recursive is True, then list recursively all objects (no dirs).

    Args:
        client:
            boto3 client
        bucket:
            name of a bucket
        path:
            a directory in the bucket.
        start:
            optional: start key, inclusive (may be a relative path under path, or
            absolute in the bucket)
        end:
            optional: stop key, exclusive (may be a relative path under path, or
            absolute in the bucket)
        recursive:
            optional, default True. If True, lists only objects. If False, lists
            only depth 0 "directories" and objects.
        list_dirs:
            optional, default True. Has no effect in recursive listing. On
            non-recursive listing, if False, then directories are omitted.
        list_objs:
            optional, default True. If False, then directories are omitted.
        limit:
            optional. If specified, then lists at most this many items.

    Returns:
        an iterator of S3Obj.

    Examples:

        # iterate through all S3 objects under some dir
        >>> for p in s3list(client, bucket, 'some/dir'):
        ...     print(p)

        # iterate through up to 20 S3 objects under some dir, starting with foo_0010
        >>> for p in s3list(client, bucket, 'some/dir', limit=20, start='foo_0010'):
        ...     print(p)

        # non-recursive listing under some dir:
        >>> for p in s3list(client, bucket, 'some/dir', recursive=False):
        ...     print(p)

        # non-recursive listing under some dir, listing only dirs:
        >>> for p in s3list(client, bucket, 'some/dir', recursive=False, list_objs=False):
        ...     print(p)"""
    kwargs = dict()
    if start is not None:
        if not start.startswith(path):
            start = os.path.join(path, start)
        # note: need to use a string just smaller than start, because
        # the list_object API specifies that start is excluded (the first
        # result is *after* start).
        kwargs.update(Marker=__prev_str(start))
    if end is not None:
        if not end.startswith(path):
            end = os.path.join(path, end)
    if not recursive:
        kwargs.update(Delimiter="/")
        if not path.endswith("/"):
            path += "/"
    kwargs.update(Prefix=path)
    if limit is not None:
        kwargs.update(PaginationConfig={"MaxItems": limit})

    paginator = client.get_paginator("list_objects")
    for resp in paginator.paginate(Bucket=bucket, **kwargs):
        q = []
        if "CommonPrefixes" in resp and list_dirs:
            q = [S3Obj(f["Prefix"], None, None, None) for f in resp["CommonPrefixes"]]
        if "Contents" in resp and list_objs:
            q += [
                S3Obj(f["Key"], f["LastModified"], f["Size"], f["ETag"])
                for f in resp["Contents"]
            ]
        # note: even with sorted lists, it is faster to sort(a+b)
        # than heapq.merge(a, b) at least up to 10K elements in each list
        q = sorted(q, key=attrgetter("key"))
        if limit is not None:
            q = q[:limit]
            limit -= len(q)
        for p in q:
            if end is not None and p.key >= end:
                return
            yield p


def __prev_str(s):
    if len(s) == 0:
        return s
    s, c = s[:-1], ord(s[-1])
    if c > 0:
        s += chr(c - 1)
    s += "".join(["\u7FFF" for _ in range(10)])
    return s


def key_exists(client, bucket, key):
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=key)
        for obj in response["Contents"]:
            if key == obj["Key"]:
                return True
        return False
    except KeyError:
        return False
    except Exception as e:
        # Handle or log other exceptions such as bucket doesn't exist
        return e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Walk the braingneers prp top level experiment types"
    )
    parser.add_argument("--bucket", default="braingeneers", help="S3 bucket")
    parser.add_argument(
        "--profile", default="prp-braingeneers", help="S3 credentials profile name"
    )
    parser.add_argument("-c", "--count", type=int, default=None, help="Count to index")
    args = parser.parse_args()

    session = boto3.Session(profile_name="prp-braingeneers")
    s3 = session.client(
        service_name="s3",
        endpoint_url="https://s3-west.nrp-nautilus.io",
    )

    modalities = ["archive", "ephys", "fluidics", "imaging", "integrated"]

    print(f"Collecting uuids in {modalities}")
    uuids = [
        (t, p[0].split("/")[1])
        for t in tqdm(modalities)
        for p in s3list(client=s3, bucket=args.bucket, path=t, recursive=False)
    ]
    print(f"Found {len(uuids)} uuids")

    if args.count:
        print(f"Sampling {args.count} uuids from {len(uuids)}")
        uuids = random.sample(uuids, args.count)

    print("Reading metadata:")

    # NOTE: A few experiments have manifest.json instead of metadata.json, ignoring
    info = [
        (
            *u,
            key_exists(s3, args.bucket, f"{u[0]}/{u[1]}/metadata.json"),
            # key_exists(s3, args.bucket, f"{u[0]}/{u[1]}/manifest.json"),
        )
        for u in tqdm(uuids)
    ]

    df = pd.DataFrame(info, columns=["type", "uuid", "metadata"])
    df = df[df.metadata == True]
    print(f"Of these found metadata.json for {df.shape[0]}")
    print(
        f"Duplicate uuids: {df[df.duplicated(subset='uuid', keep=False)].uuid.values}"
    )

    print("Indexing metadata.json into the database...")
    p = urlparse(os.environ.get("DATABASE_URL"))
    with psycopg2.connect(
        host=p.scheme,
        port=p.port,
        database=p.hostname,
        user=p.username,
        password=p.password,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                """
                DELETE FROM experiments;
                """
            )

        for i, row in df.iterrows():
            path = f"{row.type}/{row.uuid}/metadata.json"
            print(f"Indexing {path}")

            res = s3.get_object(Bucket=args.bucket, Key=path)
            content = res.get("Body").read()

            with con.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO experiments (key, metadata) VALUES (%s, %s);
                    """,
                    (path, content.decode("utf-8")),
                )

            con.commit()

        print("Done.")
