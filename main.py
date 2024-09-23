import random
import time

from client import Client, logger

USE_PROXY = False  # proxy format: LOGIN:PASS@IP:PORT
SLEEP_BETWEEN_WALLETS = [5, 15]


if __name__ == "__main__":
    try:
        with open("keys.txt") as file:
            keys = [row.strip() for row in file]

        with open("proxies.txt") as file:
            proxies = [f"http://{row.strip()}" for row in file]

        chain_id_lookup = {8453: "Base", 42161: "Arbitrum", 1: "Ethereum"}

        if USE_PROXY == False:
            logger.warning("Not using proxy \n")

        for index, private_key in enumerate(keys, start=1):
            client = Client(private_key, random.choice(proxies) if USE_PROXY else None)
            wallet_label = f"[{index}/{len(keys)}] {client.address} |"

            try:
                nonce = client.get_random_nonce()
                timestamp = client.get_timestamp()

                message = client.create_message(nonce, timestamp)
                signature = client.sign_message(nonce, timestamp)

                allocation = client.get_allocation(message, signature)

                if allocation["hasAllocation"]:
                    total_allocation = int(allocation["totalAllocation"]) / 10**18
                    chain = f'{chain_id_lookup[allocation["chain"]]}'
                    sybil = allocation["sybil"]

                    allocation_details = f"{wallet_label} {total_allocation:.2f} ETHFI | Claimable on: {chain} | Sybil: {sybil}"

                    if not sybil:
                        logger.success(allocation_details)
                    else:
                        logger.warning(allocation_details)

                    if index < len(keys):
                        time.sleep(random.randint(*SLEEP_BETWEEN_WALLETS))
                else:
                    logger.error(f"{wallet_label} Non-Eligible")

            except Exception as error:
                print(f"An error occurred for {client.address}: {error}")

    except KeyboardInterrupt:
        print("Script interrupted by user")
