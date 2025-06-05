"""
Tests for DexScreener API client.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from dexscreener_mcp.client import DexScreenerClient, DexScreenerAPIError
from dexscreener_mcp.types import TokenResponse, PairResponse


class TestDexScreenerClient:
    """Test cases for DexScreener API client."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        client = DexScreenerClient(rate_limit=60, cache_ttl=10)
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.rate_limit == 60
        assert client.cache_ttl == 10
        assert client.BASE_URL == "https://api.dexscreener.com/latest/dex"
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, client):
        """Test cache key generation."""
        key1 = client._get_cache_key("/tokens/0x123")
        key2 = client._get_cache_key("/search", {"q": "usdc", "limit": "10"})
        
        assert key1 == "/tokens/0x123"
        assert key2 == "/search?limit=10&q=usdc"
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, client):
        """Test caching functionality."""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Test cache miss
        assert client._get_cached_data(cache_key) is None
        
        # Test cache storage
        client._cache_data(cache_key, test_data)
        assert client._get_cached_data(cache_key) == test_data
        
        # Test cache validation
        assert client._is_cache_valid(cache_key) is True
    
    @pytest.mark.asyncio
    async def test_get_token_info_success(self, client):
        """Test successful token info retrieval."""
        mock_response = {
            "pairs": [
                {
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "url": "https://dexscreener.com/ethereum/0x123",
                    "pairAddress": "0x123",
                    "baseToken": {
                        "address": "0xabc",
                        "name": "Test Token",
                        "symbol": "TEST",
                        "decimals": 18
                    },
                    "quoteToken": {
                        "address": "0xdef",
                        "name": "USD Coin",
                        "symbol": "USDC",
                        "decimals": 6
                    },
                    "priceUsd": "1.50"
                }
            ]
        }
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.get_token_info("0xabc")
            
            assert isinstance(result, TokenResponse)
            assert len(result.pairs) == 1
            assert result.pairs[0].base_token.symbol == "TEST"
            mock_request.assert_called_once_with("tokens/0xabc")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test API error handling."""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = DexScreenerAPIError("API Error", 404)
            
            with pytest.raises(DexScreenerAPIError) as exc_info:
                await client.get_token_info("0xinvalid")
            
            assert exc_info.value.status_code == 404
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_with_limit(self, client):
        """Test search functionality with limit."""
        mock_response = {"pairs": []}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            await client.search("USDC", limit=10)
            
            mock_request.assert_called_once_with("search", {"q": "USDC", "limit": "10"})
    
    @pytest.mark.asyncio
    async def test_rate_limit_info(self, client):
        """Test rate limit info retrieval."""
        rate_limit = client.get_rate_limit_info()
        
        assert rate_limit.limit == 60
        assert rate_limit.requests_remaining == 60
        assert isinstance(rate_limit.reset_time, datetime)