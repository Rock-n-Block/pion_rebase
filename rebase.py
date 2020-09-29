import time
import random
import datetime
from decimal import Decimal

import requests
from web3 import Web3, HTTPProvider

from app.models import db, RebaseHistory, LastRebase
from contracts.consts import DECIMALS, SECONDS_IN_DAY, REBASE_DELAY, AVERAGE_BLOCK_TIME, BLOCKS_DELAY
from contracts.contracts_abi import REBASE_ABI, UNISWAP_ABI, ORACLES_ABI, PION_ABI
from settings_local import (NODE_HTTP_ENDPOINT, ORCHESTRATOR_ADDRESS, SENDER_ADDRESS, SENDER_PRIV_KEY, UNISWAP_ADDRESS,
                            MARKET_ORACLE_ADDRESS, CPI_ORACLE_ADDRESS, PION_TOKEN_ADDRESS, CPI_API_KEY)


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


class PionContract(Contract):
    def __init__(self, contract_address, contract_abi):
        super().__init__(contract_address, contract_abi)

    def total_supply(self):
        return self.contract.functions.totalSupply().call()


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
        last_rebase = LastRebase.query.first()
        if last_rebase:
            return last_rebase.seconds
        print('last rebase record not found', flush=True)
        return 0

    def save_last_rebase(self, last_rebase_time):
        last_rebase = LastRebase.query.first()
        if last_rebase:
            last_rebase.seconds = last_rebase_time
        else:
            last_rebase = LastRebase(seconds=last_rebase_time)
            db.session.add(last_rebase)
        db.session.commit()
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

        return pion_usd_rate


class CPIContractOracle(Contract):
    def __init__(self, contract_address, contract_abi):
        super().__init__(contract_address, contract_abi)

    def get_cpi_value(self):
        cpi_request = requests.get(f'https://www.quandl.com/api/v3/datasets/RATEINF/CPI_USA.json?api_key={CPI_API_KEY}')

        cpi_value = int(Decimal(str(cpi_request.json()['dataset']['data'][0][1])) * DECIMALS['USD'])
        print('CPI VALUE', cpi_value, flush=True)
        return cpi_value

    def set_cpi_oracle(self):
        cpi_value = self.get_cpi_value()

        tx_params = self._get_default_tx_params()

        tx_data = self.contract.functions.pushReport(cpi_value).buildTransaction(tx_params)
        print(tx_data, flush=True)

        self._sign_and_send(tx_data)
        return cpi_value


def save_rebase_history(pion_usd_rate, cpi_value, total_supply):
    print(f'usd_rate: {pion_usd_rate}, cpi_value: {cpi_value}, total_supply: {total_supply}', flush=True)
    last_rebase = RebaseHistory.query.order_by(RebaseHistory.date.desc()).first()
    raised = None
    if last_rebase:
        if last_rebase.total_supply < total_supply:
            raised = True
        elif last_rebase.total_supply > total_supply:
            raised = False
    rebase = RebaseHistory(usd_price=pion_usd_rate, cpi_value=cpi_value, total_supply=total_supply, raised=raised)
    db.session.add(rebase)
    db.session.commit()
    print('rebase info saved to db', flush=True)


def wait_blocks():
    time.sleep(AVERAGE_BLOCK_TIME * BLOCKS_DELAY)


if __name__ == '__main__':
    rebase_contract = RebaseContract(ORCHESTRATOR_ADDRESS, REBASE_ABI)
    market_oracle_contract = MarketOracleContract(MARKET_ORACLE_ADDRESS, ORACLES_ABI)
    cpi_oracle_contract = CPIContractOracle(CPI_ORACLE_ADDRESS, ORACLES_ABI)
    pion_contract = PionContract(PION_TOKEN_ADDRESS, PION_ABI)

    seconds_to_rebase = rebase_contract.generate_rebase_time()
    execution_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_to_rebase)
    print(f'generated time = {seconds_to_rebase} \nrebase should start at {execution_time.replace(microsecond=0)} UTC',
          flush=True)
    time.sleep(seconds_to_rebase)

    pion_usd_rate = market_oracle_contract.set_market_oracle()
    cpi_value = cpi_oracle_contract.set_cpi_oracle()
    print(f'oracles data set, wait {AVERAGE_BLOCK_TIME * BLOCKS_DELAY} seconds', flush=True)
    wait_blocks()

    rebase_contract.execute_rebase()
    rebase_contract.save_last_rebase(seconds_to_rebase)
    wait_blocks()

    total_supply = pion_contract.total_supply()
    save_rebase_history(pion_usd_rate, cpi_value, total_supply)
