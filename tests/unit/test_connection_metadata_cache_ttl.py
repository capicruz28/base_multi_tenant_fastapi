"""PR-F1-02 — Connection metadata cache TTL (TD-02)."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.tenant.cache import ConnectionMetadataCache, connection_cache


@pytest.mark.unit
def test_connection_metadata_cache_ttl_default_is_300():
    assert connection_cache.ttl.total_seconds() == 300


@pytest.mark.unit
def test_connection_metadata_cache_hit_before_expiry():
    cache = ConnectionMetadataCache(ttl_seconds=300)
    metadata = {"database_type": "single", "nombre_bd": "bd_test"}

    with patch("app.core.tenant.cache.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 6, 25, 12, 0, 0)
        cache.set(42, metadata)
        mock_dt.now.return_value = datetime(2026, 6, 25, 12, 4, 59)
        assert cache.get(42) == metadata


@pytest.mark.unit
def test_connection_metadata_cache_miss_after_expiry():
    cache = ConnectionMetadataCache(ttl_seconds=300)
    metadata = {"database_type": "single", "nombre_bd": "bd_test"}

    with patch("app.core.tenant.cache.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 6, 25, 12, 0, 0)
        cache.set(42, metadata)
        mock_dt.now.return_value = datetime(2026, 6, 25, 12, 5, 0)
        assert cache.get(42) is None


@pytest.mark.unit
def test_connection_metadata_cache_ttl_below_minimum_fail_fast():
    with pytest.raises(ValidationError, match="CONNECTION_METADATA_CACHE_TTL"):
        Settings(CONNECTION_METADATA_CACHE_TTL=299)


@pytest.mark.unit
def test_connection_metadata_cache_ttl_above_maximum_fail_fast():
    with pytest.raises(ValidationError, match="CONNECTION_METADATA_CACHE_TTL"):
        Settings(CONNECTION_METADATA_CACHE_TTL=901)


@pytest.mark.unit
def test_connection_metadata_cache_ttl_boundary_values_accepted():
    low = Settings(CONNECTION_METADATA_CACHE_TTL=300)
    high = Settings(CONNECTION_METADATA_CACHE_TTL=900)
    assert low.CONNECTION_METADATA_CACHE_TTL == 300
    assert high.CONNECTION_METADATA_CACHE_TTL == 900
