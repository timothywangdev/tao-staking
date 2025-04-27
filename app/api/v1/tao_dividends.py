"""
Tao dividends API endpoints.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from ...models.dividend import DividendResponse, ErrorResponse
from ...middleware.auth import get_api_key
from ...config import settings
from ...clients.bittensor import BitTensorClient
from ...clients.cache import CacheClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tao_dividends"])
bittensor_client = BitTensorClient()
cache_client = CacheClient()


@router.get(
    "/tao_dividends",
    response_model=DividendResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    description="Get Tao dividends for a given subnet and hotkey.",
)
async def get_tao_dividends(
    request: Request,  # Required by slowapi
    netuid: Annotated[int | None, None] = None,
    hotkey: Annotated[str | None, None] = None,
    trade: Annotated[bool | None, None] = False,
    api_key: str = Depends(get_api_key),
) -> DividendResponse:
    """
    Get Tao dividends for a given subnet and hotkey.

    Args:
        request: FastAPI request object (required by slowapi)
        netuid: Optional subnet ID, defaults to settings.DEFAULT_NETUID
        hotkey: Optional hotkey, defaults to settings.DEFAULT_HOTKEY
        trade: Optional boolean, defaults to False
        api_key: API key for authentication

    Returns:
        DividendResponse: Dividend information including amount and cache status

    Raises:
        HTTPException: If there's an error querying the blockchain or cache
    """
    try:
        # Use defaults if not provided
        netuid = netuid if netuid is not None else settings.DEFAULT_NETUID
        hotkey = hotkey if hotkey else settings.DEFAULT_HOTKEY

        logger.info(f"Processing dividend request for netuid={netuid}, hotkey={hotkey}")

        # Try to get from cache first
        try:
            cached_data = await cache_client.get_cached_dividend(netuid, hotkey)
            if cached_data:
                logger.debug(f"Cache hit for netuid={netuid}, hotkey={hotkey}")
                return DividendResponse(**cached_data, cached=True)
        except Exception as cache_error:
            logger.warning(f"Cache error: {str(cache_error)}")
            # Continue with blockchain query if cache fails

        # Query blockchain
        try:
            dividend = await bittensor_client.get_dividend(netuid, hotkey)
        except Exception as blockchain_error:
            logger.error(f"Blockchain query error: {str(blockchain_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to query blockchain: {str(blockchain_error)}",
            )

        # Prepare response
        response = DividendResponse(
            netuid=netuid,
            hotkey=hotkey,
            dividend=dividend,
            cached=False,
            stake_tx_triggered=trade,
        )

        # Cache the result
        try:
            await cache_client.set_cached_dividend(netuid, hotkey, response.dict())
        except Exception as cache_error:
            logger.warning(f"Failed to cache result: {str(cache_error)}")
            # Continue since we have the data even if caching failed

        logger.info(f"Successfully processed dividend request for netuid={netuid}, hotkey={hotkey}")
        return response

    except HTTPException:
        raise  # Re-raise HTTP exceptions as is
    except Exception as e:
        logger.error(f"Unexpected error in get_tao_dividends: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
