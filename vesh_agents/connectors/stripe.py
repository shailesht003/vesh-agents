"""Stripe API connector — production-grade with retry, backoff, and rate-limit handling."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from vesh_agents.connectors.base import (
    BaseConnector,
    ChangeType,
    ColumnSchema,
    ConnectorCapabilities,
    DiscoveredSchema,
    NormalizedRecord,
    TableSchema,
)

logger = logging.getLogger(__name__)

STRIPE_OBJECT_TYPES = ["customer", "subscription", "invoice", "charge", "product", "price"]
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 30.0
RATE_LIMIT_PAUSE_SECONDS = 2.0


def _retry_with_backoff(fn, *args, **kwargs):
    """Execute a Stripe API call with exponential backoff on transient errors."""
    try:
        import stripe as stripe_sdk
    except ImportError:
        raise ImportError("Stripe connector requires 'stripe' package. Install with: pip install vesh-agents[stripe]")

    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except stripe_sdk.RateLimitError as exc:
            if attempt == MAX_RETRIES:
                raise
            retry_after = getattr(exc, "headers", {}).get("Retry-After")
            wait = float(retry_after) if retry_after else RATE_LIMIT_PAUSE_SECONDS * (2**attempt)
            wait = min(wait, MAX_BACKOFF_SECONDS)
            logger.warning("Stripe rate limited (attempt %d), waiting %.1fs", attempt + 1, wait)
            time.sleep(wait)
        except stripe_sdk.APIConnectionError:
            if attempt == MAX_RETRIES:
                raise
            wait = INITIAL_BACKOFF_SECONDS * (2**attempt)
            logger.warning("Stripe connection error (attempt %d), waiting %.1fs", attempt + 1, wait)
            time.sleep(wait)
        except stripe_sdk.APIError as exc:
            status = getattr(exc, "http_status", None)
            if status and status >= 500 and attempt < MAX_RETRIES:
                wait = INITIAL_BACKOFF_SECONDS * (2**attempt)
                logger.warning("Stripe server error %d (attempt %d), waiting %.1fs", status, attempt + 1, wait)
                time.sleep(wait)
            else:
                raise


class StripeConnector(BaseConnector):
    """Connector for Stripe API — extracts customers, subscriptions, invoices, etc."""

    def __init__(self, connection_id: str, config: dict, credentials: dict):
        super().__init__(connection_id, config, credentials)
        try:
            import stripe as stripe_sdk

            self._client = stripe_sdk.StripeClient(api_key=credentials.get("api_key", ""))
        except ImportError:
            raise ImportError("Stripe connector requires 'stripe' package. Install with: pip install vesh-agents[stripe]")

    def get_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_cdc=False, supports_incremental=True, supports_schema_introspection=True, read_only=True
        )

    async def test_connection(self) -> bool:
        try:
            _retry_with_backoff(self._client.customers.list, limit=1)
            return True
        except Exception:
            return False

    async def discover(self) -> DiscoveredSchema:
        tables = [
            TableSchema(
                table_name="customer",
                columns=[
                    ColumnSchema("id", "string", is_primary_key=True, semantic_type="external_id"),
                    ColumnSchema("email", "string", semantic_type="email_address"),
                    ColumnSchema("name", "string", semantic_type="person_name"),
                    ColumnSchema("created", "timestamp", semantic_type="created_timestamp"),
                    ColumnSchema("currency", "string", semantic_type="currency_code"),
                ],
            ),
            TableSchema(
                table_name="subscription",
                columns=[
                    ColumnSchema("id", "string", is_primary_key=True, semantic_type="external_id"),
                    ColumnSchema("customer", "string", semantic_type="external_id"),
                    ColumnSchema("status", "string", semantic_type="status_flag"),
                    ColumnSchema("current_period_start", "timestamp"),
                    ColumnSchema("current_period_end", "timestamp"),
                    ColumnSchema("created", "timestamp", semantic_type="created_timestamp"),
                    ColumnSchema("plan_amount", "integer", semantic_type="revenue_amount"),
                ],
            ),
            TableSchema(
                table_name="invoice",
                columns=[
                    ColumnSchema("id", "string", is_primary_key=True, semantic_type="external_id"),
                    ColumnSchema("customer", "string", semantic_type="external_id"),
                    ColumnSchema("amount_paid", "integer", semantic_type="revenue_amount"),
                    ColumnSchema("status", "string", semantic_type="status_flag"),
                    ColumnSchema("created", "timestamp", semantic_type="created_timestamp"),
                ],
            ),
        ]
        return DiscoveredSchema(source_type="stripe", tables=tables)

    async def extract_full(
        self, object_types: list[str] | None = None, progress_callback: Callable[[int, int | None], None] | None = None
    ) -> list[NormalizedRecord]:
        targets = object_types or STRIPE_OBJECT_TYPES
        records: list[NormalizedRecord] = []
        now = datetime.now(UTC)

        for obj_type in targets:
            logger.info("Extracting Stripe %s (full)", obj_type)
            items = self._list_objects(obj_type)
            for item in items:
                item_dict = self._stripe_obj_to_dict(item)
                records.append(
                    NormalizedRecord(
                        source_type="stripe",
                        source_id=self.connection_id,
                        object_type=obj_type,
                        record_id=item_dict.get("id", ""),
                        data=item_dict,
                        extracted_at=now,
                        change_type=ChangeType.CREATE,
                        record_hash=self._compute_record_hash(item_dict),
                    )
                )
                if progress_callback and len(records) % 100 == 0:
                    progress_callback(len(records), None)
            logger.info("Extracted %d %s records from Stripe", len(records), obj_type)
        if progress_callback:
            progress_callback(len(records), len(records))
        return records

    async def extract_incremental(
        self,
        since: datetime,
        object_types: list[str] | None = None,
        progress_callback: Callable[[int, int | None], None] | None = None,
    ) -> list[NormalizedRecord]:
        records: list[NormalizedRecord] = []
        now = datetime.now(UTC)
        since_ts = int(since.timestamp())

        events = _retry_with_backoff(self._client.events.list, created={"gte": since_ts}, limit=100)
        for event in events.auto_paging_iter():
            event_dict = self._stripe_obj_to_dict(event)
            obj_data = event_dict.get("data", {}).get("object", {})
            obj_type = obj_data.get("object", "unknown")
            change_type = ChangeType.UPDATE
            event_type = event_dict.get("type", "")
            if "created" in event_type:
                change_type = ChangeType.CREATE
            elif "deleted" in event_type:
                change_type = ChangeType.DELETE
            records.append(
                NormalizedRecord(
                    source_type="stripe",
                    source_id=self.connection_id,
                    object_type=obj_type,
                    record_id=obj_data.get("id", ""),
                    data=obj_data,
                    extracted_at=now,
                    change_type=change_type,
                    record_hash=self._compute_record_hash(obj_data),
                )
            )
            if progress_callback and len(records) % 100 == 0:
                progress_callback(len(records), None)
        if progress_callback:
            progress_callback(len(records), len(records))
        return records

    def _list_objects(self, obj_type: str) -> list[Any]:
        list_fn_map = {
            "customer": self._client.customers.list,
            "subscription": self._client.subscriptions.list,
            "invoice": self._client.invoices.list,
            "charge": self._client.charges.list,
            "product": self._client.products.list,
            "price": self._client.prices.list,
        }
        list_fn = list_fn_map.get(obj_type)
        if not list_fn:
            return []
        result = _retry_with_backoff(list_fn, limit=100)
        return list(result.auto_paging_iter())

    @staticmethod
    def _stripe_obj_to_dict(obj: Any) -> dict:
        if hasattr(obj, "to_dict_recursive"):
            return obj.to_dict_recursive()
        if hasattr(obj, "__dict__"):
            return dict(obj)
        return {}
