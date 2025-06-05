"""
DexScreener API client with rate limiting, caching, and error handling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from urllib.parse import quote

import httpx
import structlog
from asyncio_throttle import Throttler
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .types import (
    APIError,
    ChainId,
    PairInfo,
    PairResponse,
    RateLimitInfo,
    SearchResult,
    TokenResponse,
    TrendingResponse,
)

# Check if we're in MCP mode to avoid stdout pollution
import sys
try:
    _is_mcp_mode = not sys.stdin.isatty()
except (OSError, ValueError):
    _is_mcp_mode = True

# Disable logging in MCP mode to prevent stdout pollution
if _is_mcp_mode:
    import logging
    logging.disable(logging.CRITICAL)

logger = structlog.get_logger(__name__)


class DexScreenerAPIError(Exception):
    """Custom exception for DexScreener API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DexScreenerClient:
    """
    Async client for DexScreener API with comprehensive error handling,
    rate limiting, caching, and retry logic.
    """
    
    BASE_URL = "https://api.dexscreener.com/latest/dex"
    
    def __init__(
        self,
        rate_limit: int = 300,  # requests per minute
        cache_ttl: int = 60,    # cache TTL in seconds
        timeout: int = 30,      # request timeout in seconds
        max_retries: int = 3,   # max retry attempts
    ):
        self.rate_limit = rate_limit
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=rate_limit, period=60)
        
        # Simple in-memory cache
        self._cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "DexScreener-MCP-Server/1.0.0",
                "Accept": "application/json",
            },
        )
        
        logger.info(
            "DexScreener client initialized",
            rate_limit=rate_limit,
            cache_ttl=cache_ttl,
            timeout=timeout,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("DexScreener client closed")
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for endpoint and parameters."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{endpoint}?{param_str}"
        return endpoint
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        return datetime.now() - cache_time < timedelta(seconds=self.cache_ttl)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid."""
        if self._is_cache_valid(cache_key):
            logger.debug("Cache hit", cache_key=cache_key)
            return self._cache[cache_key]
        
        # Remove expired cache entries
        if cache_key in self._cache:
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            logger.debug("Cache expired", cache_key=cache_key)
        
        return None
    
    def _cache_data(self, cache_key: str, data: Dict) -> None:
        """Store data in cache."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
        logger.debug("Data cached", cache_key=cache_key)
    
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request with retry logic and rate limiting."""
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Apply rate limiting
        async with self.throttler:
            url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
            
            logger.debug("Making API request", url=url, params=params)
            
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Cache successful response
                self._cache_data(cache_key, data)
                
                logger.info(
                    "API request successful",
                    url=url,
                    status_code=response.status_code,
                    response_size=len(str(data)),
                )
                
                return data
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                logger.error(
                    "API request failed",
                    url=url,
                    status_code=e.response.status_code,
                    error=error_msg,
                )
                raise DexScreenerAPIError(error_msg, e.response.status_code)
                
            except httpx.RequestError as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error("Network error", url=url, error=error_msg)
                raise DexScreenerAPIError(error_msg)
    
    async def get_token_info(self, token_address: str) -> TokenResponse:
        """
        Get token information and trading pairs.
        
        Args:
            token_address: Token contract address
            
        Returns:
            TokenResponse with pairs data
            
        Raises:
            DexScreenerAPIError: If API request fails
            ValidationError: If response validation fails
        """
        try:
            data = await self._make_request(f"tokens/{token_address}")
            return TokenResponse(**data)
        except ValidationError as e:
            logger.error("Token response validation failed", error=str(e))
            raise DexScreenerAPIError(f"Invalid response format: {str(e)}")
    
    async def get_pair_info(self, chain_id: str, pair_address: str) -> PairResponse:
        """
        Get trading pair information.
        
        Args:
            chain_id: Blockchain identifier
            pair_address: Pair contract address
            
        Returns:
            PairResponse with pair data
            
        Raises:
            DexScreenerAPIError: If API request fails
            ValidationError: If response validation fails
        """
        try:
            data = await self._make_request(f"pairs/{chain_id}/{pair_address}")
            return PairResponse(**data)
        except ValidationError as e:
            logger.error("Pair response validation failed", error=str(e))
            raise DexScreenerAPIError(f"Invalid response format: {str(e)}")
    
    async def search(
        self, 
        query: str, 
        limit: Optional[int] = None
    ) -> SearchResult:
        """
        Search for tokens and pairs.
        
        Args:
            query: Search query (token name, symbol, or address)
            limit: Maximum number of results to return
            
        Returns:
            SearchResult with found pairs
            
        Raises:
            DexScreenerAPIError: If API request fails
            ValidationError: If response validation fails
        """
        params = {"q": query}
        if limit is not None:
            params["limit"] = str(limit)
        
        try:
            data = await self._make_request("search", params)
            return SearchResult(**data)
        except ValidationError as e:
            logger.error("Search response validation failed", error=str(e))
            raise DexScreenerAPIError(f"Invalid response format: {str(e)}")
    
    async def get_trending_pairs(self, chain_id: Optional[str] = None) -> TrendingResponse:
        """
        Get trending pairs, optionally filtered by chain.
        
        Args:
            chain_id: Optional blockchain identifier to filter by
            
        Returns:
            TrendingResponse with trending pairs
            
        Raises:
            DexScreenerAPIError: If API request fails
            ValidationError: If response validation fails
        """
        endpoint = chain_id if chain_id else "tokens"
        
        try:
            data = await self._make_request(endpoint)
            return TrendingResponse(**data)
        except ValidationError as e:
            logger.error("Trending response validation failed", error=str(e))
            raise DexScreenerAPIError(f"Invalid response format: {str(e)}")
    
    async def get_multiple_pairs(
        self, 
        pair_addresses: List[str]
    ) -> List[PairInfo]:
        """
        Get information for multiple pairs in a single request.
        
        Args:
            pair_addresses: List of pair addresses in format "chain:address"
            
        Returns:
            List of PairInfo objects
            
        Raises:
            DexScreenerAPIError: If API request fails
            ValidationError: If response validation fails
        """
        if not pair_addresses:
            return []
        
        # DexScreener accepts comma-separated pair addresses
        addresses_param = ",".join(pair_addresses)
        
        try:
            data = await self._make_request(f"pairs/{addresses_param}")
            pairs_data = data.get("pairs", [])
            return [PairInfo(**pair) for pair in pairs_data]
        except ValidationError as e:
            logger.error("Multiple pairs response validation failed", error=str(e))
            raise DexScreenerAPIError(f"Invalid response format: {str(e)}")
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit information."""
        # This is a simplified implementation
        # In a real scenario, you'd track actual API response headers
        return RateLimitInfo(
            requests_remaining=self.rate_limit,
            reset_time=datetime.now() + timedelta(minutes=1),
            limit=self.rate_limit,
        )