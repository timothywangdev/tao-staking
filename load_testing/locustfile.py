import random
from typing import Any

from locust import HttpUser, task, between


# hotkeys fetched from subnet 18
hotkeys = {
    "5DsfDHkSdtZtqxNh7i1BzT2YoZwNyvzhuhCyGS3v6gMvUnjf": 0,
    "5HHF7Z2M2xzwNSskMWB3Gzdhe1ZxcNr2nKw6dcZovWCGmjF1": 0,
    "5EHVCZsbbkZftF5k4TfRiw6npbSpNEHX7sv1DucksoRnaxNo": 0,
    "5HgidDt59C2NvB2BqDC96gy1nAsj2xkX9kfdwVMgpdn2M6hF": 0,
    "5HidY9Danh9NhNPHL2pfrf97Zboew3v7yz4abuibZszcKEMv": 0,
    "5D4zCdvevMXCSt3bg9W2W2R9DmPTyi2tGdpbZAdJtyLDCktN": 0,
    "5FPFGr9xWdyFfHgDbBRQEWtqLCed8j6oR3b7Mz6UcU6WWqmc": 0,
    "5HBw3DVifESqMKaTZwaxPSMNAh8bvHt4Hn11EVbys2MRFJCY": 1,
    "5FkKpt26tZVWtTGnLqvh1ts1yhZmHC2yitzVi2y2CFKWU5Km": 0,
    "5DJCkMuBznnP9hfPCtAzzKhtSUYHLgUL2LMhUjRc9EY6SKeZ": 0,
    "5CcE7Ma5rux2ePKoKCCpjZmgjpEsYSiAiU6Fq9jwiGRqA69e": 256,
    "5GLWYfcBfUB4fGxMXTD5e1qQDGiGRiwgSq6YEVLwoq2vqbmW": 0,
    "5FnF48p3kVtwixXoDvxfvZYmijchFRvk3VaDqBsYAyaEpX8r": 0,
    "5FHL4VqWWya79EqrArujR5TmZABvnan2Vw6Fj3LebZn66R3j": 0,
    "5Dk2y7wgtnrkN5C7BQYTmrTNoU3vhko5d2wtc8w6bVsmoAtF": 12777,
    "5GjhNW3vVqdJD9VSGj5eiaAi4QhuBhkW1CWMUSoHT9iBJZUv": 0,
    "5G9yUy94GvaWHUWXd3QgGt7rS8rPz3cZrFNGD8ntPGERJeif": 0,
    "5D863DMf2nSTQH35xehzjCdax6B8AyyuyzxeLKqSK5h9yLQv": 0,
    "5GERb2LsXpohgU4G9E8AFBr74cTh6B1EbwThkJNmd3tQo2pA": 2,
    "5EeV112mg3L4zcyiP3vwGQBanoshMP7r4UnosTC3QVyTyezC": 0,
    "5CDGKAZH3TVHjidBL2ALKaDwKEoEzRMLPHzuq2yKTXT78bRr": 0,
    "5EX7aVJMUHJpTPN3E2CQVittUYc69vhFJkQsV6rF92pLcbfU": 0,
    "5CPJnbQXXWZyU5BKBwrRviq5sNktHYn32rGaPNWyCTqYVowh": 0,
    "5HYpBFLMJ18o6WkRHzBC1aj4y4XShgpf5KRRdJqNs2Fb1cWJ": 2115,
    "5FJ6pag4nBDNSQRWT5MkndaTMYirc1mXBZhFzdDhkyHUk34w": 0,
    "5CvssGcZAxsWngeZXNa7ijFnQ9gf6ywhcyMgspq84txvj89T": 0,
    "5CWy7oWjVGSw36YwsZNc657q4bwbeYEhigr3vQ8PyrTQpofc": 0,
    "5G48DozsZjAqxCyvQnKDu5ikJEMD4WTKkHZyqYUnxYGbZDjS": 0,
    "5CAWM4QF4VwKLyumSXAurtYGq6PmPSPzPZKJXKC4AZZEmC7Z": 0,
    "5EUztr4SzVPzrq28kpSHNwg3uQc55KdwFbZaYLATuhy2G2HJ": 0,
    "5CfLMqa9AagPnV7UA96EgMD2GVUjmkSp2P2qjRPTtD48XQri": 0,
    "5G6PjaYxpsaDfHvwY1rkSnEW53qkasXTCHCaX8Dujc13pRCo": 2213,
    "5EvexZ1sWVAEp5ZNNsQV6Jtq4gW5JtWviLPskmWcy5MEEBot": 0,
    "5HbYrqfwji9Qk7Qz3zXwaMzwJ8D6pPTCJ9CBgq4WVJ3QEhDk": 0,
    "5F7Jrp5Riag5NFAuYTPSqKFiqfxuc8jR3iFZkmFLSkPfnfyL": 32,
    "5GKE2ccF5A63SkyFQ7r3CD41jqpKGeE1ArPdVzNFAARyAe6q": 279,
    "5EhjUbhpAbhaB8oLrx6sRhdFGY45ZiqUri834iRBoH14t4g9": 0,
    "5H4AXVnMDrUoHUzUFcruGtkhJ1ChLvhYcM3JhjucY29KfECY": 37859,
    "5C5cEC7dUkgSY1GUbD8diBWLP2gyNBMjc9zG1LvMeEp2owuD": 0,
    "5ENnZ2x7zXmRQiyub6xUjeTynw4htes9UC36SWhqaYKLPiYB": 0,
    "5Dfaz75bsjFue9VN2FAj2vksrc8YccDQ863EnXR2ks2288mf": 0,
    "5Dy9b5BB7K8mzpPkX2bFAirJtL2b48DjFeVA2ke1RGJ7JZkT": 6839,
    "5Ge2grkA9Qb8cPwcSQtgsGn2rKJ8LXbPTz8JTHR4Wy97NCB1": 105188,
    "5HBWiTAJf4evBcPQsyJQKvyNSCGRaYxEGqHE4TD1HYZq156u": 0,
    "5FRKU6ir5xjhdgLackUyQthcHV3Pr9UtMzEVRWjVbRNymAXa": 111,
    "5H3dSo1UKQjU3jRP6Rq8hcC7iJ7YnuDxZHx7EVXuRRYsUYAa": 0,
    "5CLZNaeXHMuLVURTkFWFG4pfnc65sE3QVZdWLgYvnWQs11Et": 0,
    "5EhpvFoR6TSKHaMfqY9TCqbNYQbesKCYMWh3VvmyUqKvM1nj": 0,
    "5Gbmbi1K9FpGJxMu4VCKrzfNTUTKwojtFA4iXQ16roHw3KKb": 27,
    "5HNR6ifJh7b5GvCnWAcMSLoQh4G43shBnKKns5p4DEKfuPLq": 0,
    "5CYB3HYYXov9PEQrtj8PjaY3ovSajqzt4ck3SnbQ4Q1SrW27": 0,
    "5HC5euUxTxAReGHw8hn5L7niT1QVeTsPZXK3UQjVCCkqUGFV": 0,
    "5Gj6xhf8s6t5geVaEu8nNsnif4t7D2f4xMpRMCUKrrH4bA5T": 0,
    "5D7CeVRYKi6ANm5zKHGViZJrgXfnt4GeWXNWDESDaiC8WtAz": 32,
    "5FCPTnjevGqAuTttetBy4a24Ej3pH9fiQ8fmvP1ZkrVsLUoT": 1980891,
    "5GjPaNSawsrtwnuH72DgZB1ndriAdPMNKqikFapK9ZndXquU": 0,
    "5Cr4JKJFyCMgeQScSu14SVoKAMLaabEt6Bvc6fxL8eok2nsa": 0,
    "5DcQrTd45LGT88WR3tBRqgyDxFJ73SQ2ULfUqNcrMNez2Vtx": 34,
    "5FKw5N9pYdiquNjMPfxWR962VJpUktKpYufGvBGwAT4suWxE": 2185,
    "5GU2Bp7EQNqtmpRGt2j7rTLL41uZUWAeBnwbJoNFEqobrb2z": 81,
    "5CiFXoH4BRtkMEmnqzCbUSWMKkoTuiuapj5GdoKLYxjhZYyS": 0,
    "5EWWLFJrZKmuCkyDfRDjn7bt6EpEyKvJcUPVm2k9eNtZR3H8": 0,
    "5Dqmg3axeE2ewsiCBrcbMda6r6mMVot4FXgqxTH9mxaKFYJZ": 0,
    "5DhDjEsGR6iqwFsKqS1Fx7KQAGWCnKemqGfSMB5UpFsoytAJ": 0,
}


class TaoDividendsUser(HttpUser):
    """Load test user class for the tao_dividends API endpoint."""

    wait_time = between(1, 2)  # Wait between 1 and 2 seconds between tasks
    api_key: str = "secret_key"  # Replace with your actual API key

    # Default test values from the example
    default_netuid: str = "18"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the user with proper headers."""
        super().__init__(*args, **kwargs)
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

    def get_random_hotkey(self) -> str:
        """Get a random hotkey from the available hotkeys.

        Returns:
            str: A randomly selected hotkey
        """
        return random.choice(list(hotkeys.keys()))

    def make_request(
        self,
        netuid: str | None = None,
        hotkey: str | None = None,
        trade: bool = False,
    ) -> None:
        """Make a request to the tao_dividends endpoint with the given parameters.

        Args:
            netuid: Optional subnet ID
            hotkey: Optional account hotkey
            trade: Whether to trigger trade analysis
        """
        # If no hotkey provided, get a random one
        if hotkey is None:
            hotkey = self.get_random_hotkey()

        params = {}
        if netuid is not None:
            params["netuid"] = netuid
        if hotkey is not None:
            params["hotkey"] = hotkey
        if trade:
            params["trade"] = "true"

        with self.client.get(
            "/api/v1/tao_dividends",
            params=params,
            headers=self.headers,
            name="/api/v1/tao_dividends",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Request failed with status code: {response.status_code}")

    @task(3)
    def test_with_both_params(self) -> None:
        """Most common case - test with both netuid and hotkey."""
        self.make_request(netuid=self.default_netuid, hotkey=self.get_random_hotkey())

    @task(2)
    def test_with_netuid_only(self) -> None:
        """Test with only netuid parameter."""
        self.make_request(netuid=self.default_netuid)

    @task(2)
    def test_with_hotkey_only(self) -> None:
        """Test with only hotkey parameter."""
        self.make_request(hotkey=self.get_random_hotkey())

    @task(1)
    def test_with_no_params(self) -> None:
        """Test without any parameters."""
        self.make_request()

    # @task(1)
    # def test_with_trade_true(self) -> None:
    #     """Test with trade=true to trigger sentiment analysis."""
    #     self.make_request(
    #         netuid=self.default_netuid,
    #         hotkey=self.get_random_hotkey(),
    #         trade=True,
    #     )
