from bittensor import Wallet
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class WalletClient:
    def __init__(self):
        self.wallet = Wallet(name=settings.BITTENSOR_WALLET_NAME)

        if not self.wallet.coldkey_file.exists_on_device():
            self.wallet.regenerate_coldkey(
                mnemonic=settings.BITTENSOR_WALLET_MNEMONIC, use_password=False, overwrite=True
            )

    async def get_balance(self):
        return await self.wallet.get_balance()

    def get_wallet(self):
        return self.wallet
