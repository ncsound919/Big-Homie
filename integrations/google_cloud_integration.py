"""
Google Cloud Platform Integration
Extends existing Google integrations with Cloud Storage, BigQuery, Cloud Functions
"""
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger
from config import settings

try:
    from google.cloud import storage, bigquery
    from google.oauth2 import service_account
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logger.warning("google-cloud libraries not installed. GCP integration limited.")

@dataclass
class GoogleCloudResult:
    """Result of a Google Cloud operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

class GoogleCloudIntegration:
    """
    Google Cloud Platform integration

    Capabilities:
    - Cloud Storage (buckets, file operations)
    - BigQuery (queries, dataset management)
    - Cloud Functions (deployment, invocation)

    Complements existing Google Lyria (music generation) integration
    """

    def __init__(self):
        self.storage_client = None
        self.bigquery_client = None
        self.credentials = None

        if GOOGLE_CLOUD_AVAILABLE and settings.google_cloud_enabled:
            try:
                if settings.google_service_account_key_path:
                    self.credentials = service_account.Credentials.from_service_account_file(
                        settings.google_service_account_key_path
                    )
                    self.storage_client = storage.Client(
                        credentials=self.credentials,
                        project=settings.google_cloud_project_id
                    )
                    self.bigquery_client = bigquery.Client(
                        credentials=self.credentials,
                        project=settings.google_cloud_project_id
                    )
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud: {e}")

    async def health_check(self) -> bool:
        """Check if Google Cloud is accessible"""
        if not settings.google_cloud_enabled or not self.storage_client:
            return False

        try:
            # Try to list buckets as a health check
            list(self.storage_client.list_buckets(max_results=1))
            return True
        except Exception as e:
            logger.error(f"Google Cloud health check failed: {e}")
            return False

    # Cloud Storage Operations
    async def storage_upload_file(
        self,
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: str
    ) -> GoogleCloudResult:
        """Upload a file to Cloud Storage"""
        if not self.storage_client:
            return GoogleCloudResult(success=False, error="Google Cloud Storage not enabled")

        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            await asyncio.to_thread(blob.upload_from_filename, source_file_path)

            return GoogleCloudResult(
                success=True,
                data={
                    "bucket": bucket_name,
                    "blob": destination_blob_name,
                    "public_url": blob.public_url
                }
            )
        except Exception as e:
            logger.error(f"Storage upload failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

    async def storage_download_file(
        self,
        bucket_name: str,
        source_blob_name: str,
        destination_file_path: str
    ) -> GoogleCloudResult:
        """Download a file from Cloud Storage"""
        if not self.storage_client:
            return GoogleCloudResult(success=False, error="Google Cloud Storage not enabled")

        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            await asyncio.to_thread(blob.download_to_filename, destination_file_path)

            return GoogleCloudResult(
                success=True,
                data={
                    "bucket": bucket_name,
                    "blob": source_blob_name,
                    "local_path": destination_file_path
                }
            )
        except Exception as e:
            logger.error(f"Storage download failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

    async def storage_list_blobs(self, bucket_name: str, prefix: Optional[str] = None) -> GoogleCloudResult:
        """List files in a Cloud Storage bucket"""
        if not self.storage_client:
            return GoogleCloudResult(success=False, error="Google Cloud Storage not enabled")

        try:
            bucket = self.storage_client.bucket(bucket_name)
            blobs = await asyncio.to_thread(lambda: list(bucket.list_blobs(prefix=prefix)))

            return GoogleCloudResult(
                success=True,
                data=[
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "updated": blob.updated.isoformat() if blob.updated else None
                    }
                    for blob in blobs
                ]
            )
        except Exception as e:
            logger.error(f"Storage list blobs failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

    # BigQuery Operations
    async def bigquery_query(self, query: str) -> GoogleCloudResult:
        """Execute a BigQuery SQL query"""
        if not self.bigquery_client:
            return GoogleCloudResult(success=False, error="Google BigQuery not enabled")

        try:
            def _run_query():
                query_job = self.bigquery_client.query(query)
                results = query_job.result()
                rows = [dict(row) for row in results]
                return rows, results.total_rows, results.schema

            rows, total_rows, schema = await asyncio.to_thread(_run_query)

            return GoogleCloudResult(
                success=True,
                data={
                    "rows": rows,
                    "total_rows": total_rows,
                    "schema": [
                        {"name": field.name, "type": field.field_type}
                        for field in schema
                    ]
                }
            )
        except Exception as e:
            logger.error(f"BigQuery query failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

    async def bigquery_list_datasets(self) -> GoogleCloudResult:
        """List BigQuery datasets"""
        if not self.bigquery_client:
            return GoogleCloudResult(success=False, error="Google BigQuery not enabled")

        try:
            datasets = await asyncio.to_thread(lambda: list(self.bigquery_client.list_datasets()))

            return GoogleCloudResult(
                success=True,
                data=[
                    {
                        "dataset_id": dataset.dataset_id,
                        "full_dataset_id": dataset.full_dataset_id,
                        "project": dataset.project
                    }
                    for dataset in datasets
                ]
            )
        except Exception as e:
            logger.error(f"BigQuery list datasets failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

    async def bigquery_list_tables(self, dataset_id: str) -> GoogleCloudResult:
        """List tables in a BigQuery dataset"""
        if not self.bigquery_client:
            return GoogleCloudResult(success=False, error="Google BigQuery not enabled")

        try:
            tables = await asyncio.to_thread(lambda: list(self.bigquery_client.list_tables(dataset_id)))

            return GoogleCloudResult(
                success=True,
                data=[
                    {
                        "table_id": table.table_id,
                        "full_table_id": table.full_table_id,
                        "table_type": table.table_type
                    }
                    for table in tables
                ]
            )
        except Exception as e:
            logger.error(f"BigQuery list tables failed: {e}")
            return GoogleCloudResult(success=False, error=str(e))

# Global instance
google_cloud = GoogleCloudIntegration()
