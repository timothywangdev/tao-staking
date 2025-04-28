from .worker import celery_app
from app.clients.chutes import ChutesClient
from app.clients.desearch import DesearchClient
from app.clients.bittensor import BitTensorClient
from app.clients.wallet import WalletClient
import asyncio
import logging
from app.clients.mongodb import MongoDBClient
from app.models.sentiment_staking_result import SentimentStakingResult
import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # If already in an event loop, create a new task and wait for it
        import nest_asyncio

        nest_asyncio.apply()
        return asyncio.ensure_future(coro)
    else:
        return asyncio.run(coro)


async def sentiment_staking(
    netuid: int,
    hotkey: str,
    task_id: str,
    mongo_client: Optional[MongoDBClient] = None,
    bittensor_client: Optional[BitTensorClient] = None,
    wallet_client: Optional[WalletClient] = None,
    desearch_client: Optional[DesearchClient] = None,
    chutes_client: Optional[ChutesClient] = None,
    stake_amount_fn: Optional[Callable[[float], float]] = None,
):
    """
    This function performs sentiment-based staking on the Tao network.
    It analyzes the sentiment of the network and stakes or unstakes TAO accordingly.
    Persists the result in MongoDB using the required task_id.
    """
    stake_amount = None
    result = None
    mongo_client = mongo_client or MongoDBClient()
    bittensor_client = bittensor_client or BitTensorClient()
    wallet_client = wallet_client or WalletClient()
    desearch_client = desearch_client or DesearchClient()
    chutes_client = chutes_client or ChutesClient()
    stake_amount_fn = stake_amount_fn or (lambda sentiment_score: 1)  # Default logic

    pending_doc = {
        "task_id": task_id,
        "status": "pending",
        "netuid": netuid,
        "hotkey": hotkey,
        "stake_amount": None,
        "error": None,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    await mongo_client.insert_one("sentiment_staking_results", pending_doc)
    try:
        # step 1: get the tweets
        tweets = desearch_client.search_tweets(f"Bittensor netuid {netuid}", count=10)
        logger.debug(f"Tweets: {tweets}")

        # step 2: get the sentiment score
        sentiment_score = chutes_client.get_sentiment_score(tweets)
        chutes_client.close()
        logger.debug(f"Sentiment score: {sentiment_score}")

        # step 3: stake or unstake TAO
        stake_amount = stake_amount_fn(sentiment_score)
        logger.debug(f"Stake amount: {stake_amount}")
        stake_unstake_success = False
        if stake_amount > 0:
            stake_unstake_success = await bittensor_client.stake(
                wallet_client.get_wallet(), netuid, hotkey, stake_amount
            )
            logger.debug(f"Stake success: {stake_unstake_success}")
        else:
            stake_unstake_success = await bittensor_client.unstake(
                wallet_client.get_wallet(), netuid, hotkey, abs(stake_amount)
            )
            logger.debug(f"Unstake success: {stake_unstake_success}")

        result = {
            "task_id": task_id,
            "status": "success" if stake_unstake_success else "failed",
            "netuid": netuid,
            "hotkey": hotkey,
            "stake_amount": stake_amount,
            "error": None,
            "updated_at": datetime.datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"sentiment_staking_task failed with error: {e}", exc_info=True)
        result = {
            "task_id": task_id,
            "status": "failed",
            "netuid": netuid,
            "hotkey": hotkey,
            "stake_amount": stake_amount,
            "error": str(e),
            "updated_at": datetime.datetime.utcnow(),
        }
    # Update MongoDB record
    try:
        validated_doc = SentimentStakingResult(**result).model_dump()
        await mongo_client.update_one(
            "sentiment_staking_results", {"task_id": task_id}, validated_doc
        )
        logger.info(
            f"Updated sentiment staking result for task_id={task_id} with status {result['status']}"
        )
    except Exception as e:
        logger.error(f"Failed to update sentiment staking result for task_id={task_id}: {e}")
    return result


@celery_app.task(bind=True)
def sentiment_staking_task(self, netuid: int, hotkey: str):
    logger.info(f"sentiment_staking_task called with netuid={netuid}, hotkey={hotkey}")
    return run_async(sentiment_staking(netuid, hotkey, task_id=self.request.id))
