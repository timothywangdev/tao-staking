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

# Set up logger for this module
logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Utility function to run an async coroutine in a synchronous context.
    Handles both cases: if already in an event loop (e.g., in Jupyter or Celery),
    or if not (e.g., standard script execution).
    """
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
    Perform sentiment-based staking on the Tao network.

    Steps:
    1. Persist a 'pending' result in MongoDB for tracking.
    2. Fetch recent tweets related to the given netuid using DesearchClient.
    3. Analyze the sentiment of those tweets using ChutesClient.
    4. Decide how much TAO to stake or unstake based on the sentiment score.
    5. Execute the stake/unstake operation using BitTensorClient and WalletClient.
    6. Update the MongoDB record with the result (success/failure, error info, etc).

    Args:
        netuid (int): The network UID to analyze and stake for.
        hotkey (str): The hotkey (wallet address) to use for staking.
        task_id (str): Unique identifier for this task (used for DB tracking).
        mongo_client, bittensor_client, wallet_client, desearch_client, chutes_client: Optional dependency-injected clients for testability.
        stake_amount_fn (Callable): Optional function to determine stake amount from sentiment score.

    Returns:
        dict: Result document with status, error info, and other metadata.
    """
    stake_amount = None
    result = None
    # Use provided clients or default to real implementations
    mongo_client = mongo_client or MongoDBClient()
    bittensor_client = bittensor_client or BitTensorClient()
    wallet_client = wallet_client or WalletClient()
    desearch_client = desearch_client or DesearchClient()
    chutes_client = chutes_client or ChutesClient()
    stake_amount_fn = stake_amount_fn or (lambda sentiment_score: 1)  # Default: always stake 1 TAO

    # Step 1: Insert a pending result for this task in MongoDB
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
        # Step 2: Fetch tweets related to the netuid
        tweets = desearch_client.search_tweets(f"Bittensor netuid {netuid}", count=10)
        logger.debug(f"Tweets: {tweets}")

        # Step 3: Analyze sentiment of the tweets
        sentiment_score = chutes_client.get_sentiment_score(tweets)
        chutes_client.close()
        logger.debug(f"Sentiment score: {sentiment_score}")

        # Step 4: Decide how much to stake or unstake based on sentiment
        stake_amount = stake_amount_fn(sentiment_score)
        logger.debug(f"Stake amount: {stake_amount}")
        stake_unstake_success = False
        # Step 5: Stake or unstake TAO using BitTensorClient
        if stake_amount > 0:
            # Positive sentiment: stake TAO
            stake_unstake_success = await bittensor_client.stake(
                wallet_client.get_wallet(), netuid, hotkey, stake_amount
            )
            logger.debug(f"Stake success: {stake_unstake_success}")
        else:
            # Negative sentiment: unstake TAO
            stake_unstake_success = await bittensor_client.unstake(
                wallet_client.get_wallet(), netuid, hotkey, abs(stake_amount)
            )
            logger.debug(f"Unstake success: {stake_unstake_success}")

        # Prepare result document
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
        # Catch and log any errors during the process
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
    # Step 6: Update the MongoDB record with the final result
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
    """
    Celery task entry point for running sentiment-based staking asynchronously.
    Passes the Celery task id as the unique task_id for tracking in the DB.
    """
    logger.info(f"sentiment_staking_task called with netuid={netuid}, hotkey={hotkey}")
    return run_async(sentiment_staking(netuid, hotkey, task_id=self.request.id))
