from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.MINIO_PUBLIC_BUCKET
    endpoint_url = settings.MINIO_ENDPOINT
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    region_name = "us-east-1"
    file_overwrite = False