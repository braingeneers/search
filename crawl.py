# /usr/bin/env python
"""
Crawl the braingeneers prp top level experiment types (ephys, imaging etc...) and update the metadata index in sqlite. 
"""
import os
import random
import argparse
import datetime
from collections import namedtuple
from operator import attrgetter
import tqdm

import apsw

import boto3

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
        description="Crawl the braingneers prp top level experiment types"
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("S3_ENDPOINT", "https://s3.braingeneers.gi.ucsc.edu"),
        help="S3 endpoint",
    )
    parser.add_argument(
        "--profile",
        default=os.getenv("S3_PROFILE", "prp-braingeneers"),
        help="S3 credentials profile name",
    )
    parser.add_argument(
        "--bucket", default=os.getenv("S3_BUCKET", "braingeneers"), help="S3 bucket"
    )
    parser.add_argument("-c", "--count", type=int, default=None, help="Count to index")
    parser.add_argument(
        "-d", "--delete", action="store_true", help="Delete all existing entries"
    )
    args = parser.parse_args()

    print(f"Starting crawl at {datetime.datetime.now()}")

    conn = apsw.Connection("data/braingeneers.db")

    if args.delete:
        print("Deleting all existing entries and vacuuming database")
        conn.execute("DELETE FROM experiments;")
        conn.execute("VACUUM;")

    # Get all paths that are already indexed in the database
    existing_paths = conn.execute("SELECT path FROM experiments;").fetchall()
    if existing_paths:
        existing_paths = set(list(zip(*existing_paths))[0])
    else:
        existing_paths = set()
    print(f"Found {len(existing_paths)} existing paths in the database")

    # Crawl a list of all paths for each of the modalities
    session = boto3.Session(profile_name=args.profile)
    s3 = session.client(
        service_name="s3",
        endpoint_url=args.endpoint,
    )

    modalities = ["archive", "ephys", "fluidics", "imaging", "integrated"]

    print(f"Listing all paths under {modalities}")
    all_paths = set(
        [
            p[0].rstrip("/")
            for t in tqdm.tqdm(modalities)
            for p in s3list(client=s3, bucket=args.bucket, path=t, recursive=False)
        ]
    )
    new_paths = all_paths - existing_paths
    print(f"Found {len(all_paths)} paths of which {len(new_paths)} are new")

    # If count specified, sample from the new paths
    if args.count:
        print(f"Sampling {args.count} paths from {len(new_paths)} new paths")
        new_paths = random.sample(list(new_paths), args.count)

    print("Search new paths for metadata.json")
    file_log = tqdm.tqdm(total=0, position=1, bar_format="{desc}")
    for path in (progress := tqdm.tqdm(new_paths, desc="Keys", position=0)):
        key = f"{path}/metadata.json"

        # NOTE: A few experiments have manifest.json instead of metadata.json, ignoring
        if not key_exists(s3, args.bucket, key):
            continue

        file_log.set_description_str(f"Current path: {path}")

        res = s3.get_object(Bucket=args.bucket, Key=key)
        content = res.get("Body").read()
        last_modified = res.get("LastModified")

        conn.execute(
            """
                INSERT INTO experiments (uuid, path, last_modified, metadata) VALUES (?, ?, ?, ?);
                """,
            (
                path.split("/")[1],
                path,
                last_modified.strftime("%Y-%m-%d"),
                content.decode("utf-8"),
            ),
        )

    file_log.clear()

    oldest = conn.execute("SELECT MIN(last_modified) FROM experiments;").fetchone()[0]
    newest = conn.execute("SELECT MAX(last_modified) FROM experiments;").fetchone()[0]
    print(f"Oldest: {oldest}")
    print(f"Newest: {newest}")

    print(f"Finished crawl at {datetime.datetime.now()}")
