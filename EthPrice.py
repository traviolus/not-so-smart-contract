from web3 import Web3
from web3.gas_strategies.time_based import medium_gas_price_strategy
import requests
import sys
import os


CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
ACCOUNT_ADDRESS = os.getenv('ACCOUNT_ADDRESS')
INFURA_URL = os.getenv('INFURA_URL')


class KovanNetwork:
    def __init__(self):
        self.account = ACCOUNT_ADDRESS
        self.url = INFURA_URL
        self.web3 = Web3(Web3.HTTPProvider(self.url))
        self.contract_address = ''
        self.contract = ''
        self.abi = [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "get",
                "outputs": [
                    {
                        "internalType": "string",
                        "name": "",
                        "type": "string"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "_newPrice",
                        "type": "string"
                    }
                ],
                "name": "set",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    def connect(self, contract_address: str) -> None:
        self.web3.eth.defaultAccount = self.account
        self.web3.eth.setGasPriceStrategy(medium_gas_price_strategy)
        self.contract_address = self.web3.toChecksumAddress(contract_address)
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
        return

    def get_price(self) -> str:
        return self.contract.functions.get().call()

    def set_price(self, new_price: str) -> None:
        transaction = self.contract.functions.set(new_price).buildTransaction({
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': int(self.web3.eth.get_transaction_count(self.account))
        })
        signed = self.web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
        tx = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        print(tx.hex())
        self.web3.eth.waitForTransactionReceipt(tx)
        return


def getEthPriceFromApi() -> str:
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(COINGECKO_API_URL)
    response_dict = response.json()
    price = str(response_dict['ethereum']['usd'])
    return price


def updatePrice() -> None:
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    obj.set_price(getEthPriceFromApi())
    return


def getPrice() -> str:
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    return obj.get_price()


cmd = sys.argv[1]
if cmd == 'get':
    print(getPrice())
if cmd == 'set':
    updatePrice()
