"""Crea el bucket (si no existe) y sube los Parquet limpios a S3."""
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.environ["BUCKET_NAME"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
LOCAL_DIR = Path("data/processed/orders")
PREFIX = "orders"

s3 = boto3.client("s3", region_name=REGION)


def ensure_bucket() -> None:
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET)
        else:
            s3.create_bucket(
                Bucket=BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"Bucket creado: {BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            print(f"El bucket ya existe: {BUCKET}")
        else:
            raise

def clear_prefix() -> None:
    """Borra los archivos anteriores para no mezclar cargas distintas."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=f"{PREFIX}/"):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if objs:
            s3.delete_objects(Bucket=BUCKET, Delete={"Objects": objs})
            print(f"Eliminados {len(objs)} archivos antiguos")

def upload_files() -> None:
    files = list(LOCAL_DIR.rglob("*.parquet"))
    if not files:
        raise SystemExit("No hay archivos .parquet. Ejecuta antes src/transform.py")
    for path in files:
        key = f"{PREFIX}/{path.relative_to(LOCAL_DIR).as_posix()}"
        s3.upload_file(str(path), BUCKET, key)
        print("Subido:", key)
    print(f"{len(files)} archivos subidos a s3://{BUCKET}/{PREFIX}/")


if __name__ == "__main__":
    ensure_bucket()
    clear_prefix()
    upload_files()