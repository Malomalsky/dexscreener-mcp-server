"""
Type definitions for DexScreener API responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator


class TokenInfo(BaseModel):
    """Token information model."""
    
    address: str = Field(..., description="Token contract address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    decimals: Optional[int] = Field(None, description="Token decimals")
    logo_uri: Optional[HttpUrl] = Field(None, alias="logoURI", description="Token logo URL")


class PairInfo(BaseModel):
    """Trading pair information model."""
    
    chain_id: str = Field(..., alias="chainId", description="Blockchain chain ID")
    dex_id: str = Field(..., alias="dexId", description="DEX identifier")
    url: HttpUrl = Field(..., description="DexScreener pair URL")
    pair_address: str = Field(..., alias="pairAddress", description="Pair contract address")
    
    base_token: TokenInfo = Field(..., alias="baseToken", description="Base token info")
    quote_token: TokenInfo = Field(..., alias="quoteToken", description="Quote token info")
    
    price_native: Optional[str] = Field(None, alias="priceNative", description="Price in native currency")
    price_usd: Optional[str] = Field(None, alias="priceUsd", description="Price in USD")
    
    txns: Optional[Dict[str, Dict[str, int]]] = Field(None, description="Transaction counts")
    volume: Optional[Dict[str, float]] = Field(None, description="Volume data")
    price_change: Optional[Dict[str, float]] = Field(None, alias="priceChange", description="Price changes")
    
    liquidity: Optional[Dict[str, float]] = Field(None, description="Liquidity data")
    fdv: Optional[float] = Field(None, description="Fully diluted valuation")
    market_cap: Optional[float] = Field(None, alias="marketCap", description="Market capitalization")
    
    pair_created_at: Optional[datetime] = Field(None, alias="pairCreatedAt", description="Pair creation timestamp")
    
    @validator("pair_created_at", pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v / 1000)  # Convert milliseconds to seconds
        return v


class SearchResult(BaseModel):
    """Search result model."""
    
    pairs: List[PairInfo] = Field(default_factory=list, description="Found trading pairs")


class TokenResponse(BaseModel):
    """Token API response model."""
    
    pairs: List[PairInfo] = Field(default_factory=list, description="Token trading pairs")


class PairResponse(BaseModel):
    """Single pair API response model."""
    
    pair: Optional[PairInfo] = Field(None, description="Pair information")


class TrendingResponse(BaseModel):
    """Trending pairs response model."""
    
    pairs: List[PairInfo] = Field(default_factory=list, description="Trending pairs")


ChainId = Literal[
    "ethereum", "bsc", "polygon", "avalanche", "fantom", "cronos", "arbitrum",
    "optimism", "harmony", "celo", "moonbeam", "moonriver", "fuse", "telos",
    "dogechain", "redlight", "kcc", "smartbch", "elastos", "hoo", "canto",
    "base", "linea", "mantle", "blast", "scroll", "zksync", "polygonzkevm"
]


class APIError(BaseModel):
    """API error response model."""
    
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    
    requests_remaining: int = Field(..., description="Requests remaining in current window")
    reset_time: datetime = Field(..., description="When the rate limit resets")
    limit: int = Field(..., description="Total requests allowed per window")