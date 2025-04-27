from bittensor import AsyncSubtensor
from bittensor.core.chain_data import decode_account_id
from ..config import settings
from typing import Optional
from bittensor import Wallet
import logging

logger = logging.getLogger(__name__)


class BitTensorClient:
    def __init__(self):
        """Initialize the BitTensor service with network configuration."""
        try:
            self.network = settings.BITTENSOR_NETWORK
            self.subtensor = AsyncSubtensor(network=self.network)
            logger.info(f"Initialized BitTensorService with network: {self.network}")
        except Exception as e:
            logger.error(f"Failed to initialize BitTensorService: {str(e)}")
            raise

    async def get_dividends_for_subnet(self, netuid: int) -> dict:
        async with self.subtensor as async_subtensor:
            result = await async_subtensor.substrate.query_map(
                module="SubtensorModule", storage_function="TaoDividendsPerSubnet", params=[netuid]
            )
            result_dict = {}
            async for k, v in result:
                decoded_key = decode_account_id(k)
                result_dict[decoded_key] = v.value
            return result_dict

    async def get_dividend(self, netuid: int, hotkey: str) -> float:
        """
        Query the Tao dividends for a given subnet and hotkey.

        Args:
            netuid: The subnet ID to query
            hotkey: The hotkey address to query

        Returns:
            float: The dividend amount

        Raises:
            Exception: If the query fails
        """
        print(f"Querying dividends for netuid={netuid}, hotkey={hotkey}")
        logger.info(f"Querying dividends for netuid={netuid}, hotkey={hotkey}")

        dividends_for_subnet = await self.get_dividends_for_subnet(netuid)
        # filter for hotkey
        hotkey_dividends = dividends_for_subnet.get(hotkey, 0.0)
        return hotkey_dividends

    async def stake(self, wallet: Wallet, netuid: int, hotkey: str, amount: float) -> bool:
        """
        Add stake for a given subnet and hotkey.
        """
        try:
            # Submit stake transaction
            stake_success = await self.subtensor.add_stake(
                netuid=netuid, hotkey_ss58=hotkey, amount=amount, wallet=wallet
            )
            return stake_success
        except Exception as e:
            raise Exception(f"Failed to add stake: {str(e)}")

    async def unstake(self, wallet: Wallet, netuid: int, hotkey: str, amount: float) -> bool:
        """
        Remove stake for a given subnet and hotkey.
        """
        try:
            # Submit unstake transaction
            unstake_success = await self.subtensor.unstake(
                netuid=netuid, hotkey_ss58=hotkey, amount=amount, wallet=wallet
            )
            return unstake_success
        except Exception as e:
            raise Exception(f"Failed to unstake: {str(e)}")
