import time
import random
import datetime

import requests
from web3 import Web3, HTTPProvider

from consts import DECIMALS, SECONDS_IN_DAY, REBASE_DELAY, AVERAGE_BLOCK_TIME, BLOCKS_DELAY
from contracts_abi import REBASE_ABI, UNISWAP_ABI, ORACLES_ABI
from settings_local import (NODE_HTTP_ENDPOINT, ORCHESTRATOR_ADDRESS, SENDER_ADDRESS, SENDER_PRIV_KEY, UNISWAP_ADDRESS,
                            MARKET_ORACLE_ADDRESS, CPI_ORACLE_ADDRESS)


class Contract:
    def __init__(self, contract_address, contract_abi):
        self.w3 = Web3(HTTPProvider(NODE_HTTP_ENDPOINT))
        self.contract = self.w3.eth.contract(contract_address, abi=contract_abi)

    def _get_default_tx_params(self):
        tx_params = {
            'gas': 500000,
            'gasPrice': self.w3.eth.gasPrice,
            'nonce': self.w3.eth.getTransactionCount(SENDER_ADDRESS, 'pending'),
            'chainId': self.w3.eth.chainId,
        }

        return tx_params

    def _sign_and_send(self, tx_data):
        signed = self.w3.eth.account.signTransaction(tx_data, SENDER_PRIV_KEY)
        print(signed, flush=True)
        tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)
        print(tx_hash.hex(), flush=True)


class RebaseContract(Contract):
    def __init__(self, contract_address, contract_abi):
        super().__init__(contract_address, contract_abi)

    def execute_rebase(self):
        tx_params = self._get_default_tx_params()

        tx_data = self.contract.functions.rebase().buildTransaction(tx_params)
        print(tx_data, flush=True)

        self._sign_and_send(tx_data)
        print('rebase transaction sent', flush=True)

    def get_last_rebase(self):
        try:
            with open('last_rebase_time.txt', 'r') as file:
                last_rebase_time = int(file.read())
        except FileNotFoundError:
            print('last rebase file not found', flush=True)
            return 0
        return last_rebase_time

    def save_last_rebase(self, last_rebase_time):
        with open('last_rebase_time.txt', 'w') as file:
            file.write(str(last_rebase_time))
        print('last rebase time saved', flush=True)

    def generate_rebase_time(self):
        last_rebase_time = rebase_contract.get_last_rebase()
        print('last rebase time', last_rebase_time, flush=True)
        seconds_to_rebase = random.randint(max(last_rebase_time - REBASE_DELAY, 0), SECONDS_IN_DAY)

        return seconds_to_rebase


class MarketOracleContract(Contract):
    def __init__(self, contract_address, contract_abi):
        super().__init__(contract_address, contract_abi)

    def get_pion_usd_rate(self):
        uniswap_contract = self.w3.eth.contract(UNISWAP_ADDRESS, abi=UNISWAP_ABI)

        reserves = uniswap_contract.functions.getReserves().call()
        pion_eth_rate = reserves[1] * DECIMALS['PION'] / (reserves[0] * DECIMALS['ETH'])

        eth_rate_request = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd')
        eth_usd_rate = eth_rate_request.json()['ethereum']['usd']

        pion_usd_rate = int(pion_eth_rate * eth_usd_rate * DECIMALS['USD'])
        print('PION USD RATE', pion_usd_rate, flush=True)
        return pion_usd_rate

    def set_market_oracle(self):
        tx_params = self._get_default_tx_params()
        pion_usd_rate = self.get_pion_usd_rate()

        tx_data = self.contract.functions.pushReport(pion_usd_rate).buildTransaction(
            tx_params)
        print(tx_data, flush=True)

        self._sign_and_send(tx_data)


class CPIContractOracle(Contract):
    def __init__(self, contract_address, contract_abi):
        super().__init__(contract_address, contract_abi)

    def get_cpi_value(self):
        return int(259.681 * DECIMALS['USD'])

    def set_cpi_oracle(self):
        cpi_value = self.get_cpi_value()

        tx_params = self._get_default_tx_params()

        tx_data = self.contract.functions.pushReport(cpi_value).buildTransaction(tx_params)
        print(tx_data, flush=True)

        self._sign_and_send(tx_data)


if __name__ == '__main__':
    rebase_contract = RebaseContract(ORCHESTRATOR_ADDRESS, REBASE_ABI)
    market_oracle_contract = MarketOracleContract(MARKET_ORACLE_ADDRESS, ORACLES_ABI)
    cpi_oracle_contract = CPIContractOracle(CPI_ORACLE_ADDRESS, ORACLES_ABI)

    seconds_to_rebase = rebase_contract.generate_rebase_time()
    execution_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_to_rebase)
    print(f'generated time = {seconds_to_rebase} \nrebase should start at {execution_time.replace(microsecond=0)} UTC',
          flush=True)
    time.sleep(seconds_to_rebase)

    market_oracle_contract.set_market_oracle()
    cpi_oracle_contract.set_cpi_oracle()
    print(f'oracles data set, wait {AVERAGE_BLOCK_TIME * BLOCKS_DELAY} seconds', flush=True)
    time.sleep(AVERAGE_BLOCK_TIME * BLOCKS_DELAY)

    rebase_contract.execute_rebase()
    rebase_contract.save_last_rebase(seconds_to_rebase)
