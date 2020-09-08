import time
import json
import random
import datetime

from web3 import Web3, HTTPProvider

from settings_local import NODE_HTTP_ENDPOINT, ORCHESTRATOR_ADDRESS, REBASE_ABI, SENDER_ADDRESS, SENDER_PRIV_KEY


def execute_rebase():
    w3 = Web3(HTTPProvider(NODE_HTTP_ENDPOINT))
    contract = w3.eth.contract(ORCHESTRATOR_ADDRESS, abi=json.dumps(REBASE_ABI))

    tx_params = {
        'gas': 500000,
        'gasPrice': w3.eth.gasPrice,
        'nonce': w3.eth.getTransactionCount(SENDER_ADDRESS, 'pending'),
        'chainId': w3.eth.chainId,
    }

    tx_data = contract.functions.rebase().buildTransaction(tx_params)
    print(tx_data, flush=True)
    signed = w3.eth.account.signTransaction(tx_data, SENDER_PRIV_KEY)
    print(signed, flush=True)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    print(tx_hash, flush=True)


if __name__ == '__main__':
    seconds_to_rebase = random.randint(0, 60 * 60 * 24)
    execution_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_to_rebase)
    print(f'Rebase should start at {execution_time.replace(microsecond=0)} UTC', flush=True)
    time.sleep(seconds_to_rebase)
    execute_rebase()
    print('rebase transaction sent', flush=True)
