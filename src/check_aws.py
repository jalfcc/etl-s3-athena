"""Comprueba que las credenciales de AWS funcionan."""
import boto3
from dotenv import load_dotenv

load_dotenv()

identity = boto3.client("sts").get_caller_identity()
print("Conectado como:", identity["Arn"])

buckets = boto3.client("s3").list_buckets()["Buckets"]
print("Buckets en la cuenta:", [b["Name"] for b in buckets])