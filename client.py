import random
import string
from datetime import datetime, timezone
from sys import stderr

import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from fake_useragent import UserAgent
from loguru import logger

logger.remove()
logger.add(
    stderr,
    format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>",
)


class Client:
    def __init__(self, private_key, proxy=None):
        self.ua = UserAgent()
        self.session = self.create_session(proxy)
        self.private_key = private_key
        self.address = Account.from_key(private_key).address

    def create_session(self, proxy):
        session = requests.Session()

        if proxy:
            session.proxies.update({"http": proxy, "https": proxy})

        session.headers.update(
            {
                "Accept": "*/*",
                "Content-Type": "application/json",
                "Origin": "https://claim.ether.fi",
                "Referer": "https://claim.ether.fi/season-3",
                "User-Agent": self.ua.random,
            }
        )
        return session

    def get_random_nonce(self, length=17):
        characters = string.ascii_letters + string.digits
        nonce = "".join(random.choice(characters) for _ in range(length))
        return nonce

    def get_timestamp(self):
        # Get the current UTC time with timezone-aware datetime object
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return timestamp

    def create_message(self, nonce, timestamp):
        message = {
            "domain": "claim.ether.fi",
            "address": self.address,
            "statement": (
                "I have read, understood, and agreed to the Airdrop Terms and Conditions "
                "and to the Third Party Token Distribution Terms.\n\n  Airdrop Terms and Conditions:\n"
                "  https://www.ether.fi/documents/etherfi_airdrop-terms.pdf\n\n  Third Party Token "
                "Distribution Terms:\n  https://www.ether.fi/documents/etherfi_third-party-token-distribution-terms.pdf\n\n"
                f"  Wallet address:\n  {self.address}"
            ),
            "uri": "https://claim.ether.fi",
            "version": "1",
            "chainId": 1,
            "nonce": nonce,
            "issuedAt": timestamp,
        }

        return message

    def sign_message(self, nonce, timestamp):
        message = (
            "claim.ether.fi wants you to sign in with your Ethereum account:\n"
            f"{self.address}\n\n"
            "I have read, understood, and agreed to the Airdrop Terms and Conditions and to the Third Party Token Distribution Terms.\n\n"
            "  Airdrop Terms and Conditions:\n"
            "  https://www.ether.fi/documents/etherfi_airdrop-terms.pdf\n\n"
            "  Third Party Token Distribution Terms:\n"
            "  https://www.ether.fi/documents/etherfi_third-party-token-distribution-terms.pdf\n\n"
            "  Wallet address:\n"
            f"  {self.address}\n\n"
            "URI: https://claim.ether.fi\n"
            "Version: 1\n"
            "Chain ID: 1\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {timestamp}"
        )

        message_encoded = encode_defunct(text=message)
        signed_message = Account.sign_message(
            message_encoded, private_key=self.private_key
        )
        return "0x" + signed_message.signature.hex()

    def get_allocation(self, message, signature):
        url = f"https://claim.ether.fi/api/s3-allocations/{self.address}"

        payload = {"address": self.address, "signature": signature, "message": message}

        resp = self.session.post(url, json=payload)
        data = resp.json()

        if data:
            return data
        else:
            raise Exception(f"Failed to fetch allocation: {data}")
