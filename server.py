import argparse

from flask import Flask, make_response, redirect
import boto3

app = Flask(__name__)

session = boto3.Session(profile_name="prp-braingeneers")
s3_client = session.client(
    service_name="s3",
    endpoint_url="https://s3-west.nrp-nautilus.io",
)


@app.route("/s3/<path:path>", methods=["HEAD"])
def s3_head(path):
    app.logger.info("HEAD %s", path)
    res = s3_client.head_object(Bucket="braingeneers", Key=path)
    response = make_response()
    response.headers.add("Accept-Ranges", "bytes")
    response.headers.add("Cache-Control", "max-age=3600")
    response.headers.add("Connection", "keep-alive")
    response.headers.add("Content-Length", res["ContentLength"])
    response.headers.add("Content-Type", res["ContentType"])
    response.headers.add("Keep-Alive", "timeout=5")
    return response


@app.route("/s3/<path:path>", methods=["GET"])
def s3_get(path):
    app.logger.info("GET %s", path)
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": "braingeneers", "Key": path},
            ExpiresIn=3600,
        )
    except ClientError as e:
        app.logging.error(e)
        return None

    response = make_response(redirect(presigned_url, code=301))
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Proxy S3 requests through a Flask server via signed URLs"
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("S3_ENDPOINT", "https://s3-west.nrp-nautilus.io"),
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

    # g.args = parser.parse_args()

    # session = boto3.Session(profile_name=g.args.profile)
    # s3 = session.client(
    #     service_name="s3",
    #     endpoint_url=g.args.endpoint,
    # )
