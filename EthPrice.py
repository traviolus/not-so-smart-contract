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
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "_coin",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "_newPrice",
                        "type": "uint256"
                    }
                ],
                "name": "set",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "_coin",
                        "type": "string"
                    }
                ],
                "name": "get",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def connect(self, contract_address: str) -> None:
        self.web3.eth.defaultAccount = self.account
        self.web3.eth.setGasPriceStrategy(medium_gas_price_strategy)
        self.contract_address = self.web3.toChecksumAddress(contract_address)
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
        return

    def get_price(self, coin_symbol: str) -> int:
        return self.contract.functions.get(coin_symbol).call()

    def set_price(self, coin_symbol: str, new_price: int) -> None:
        transaction = self.contract.functions.set(coin_symbol, new_price).buildTransaction({
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': int(self.web3.eth.get_transaction_count(self.account))
        })
        signed = self.web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
        tx = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        print(tx.hex())
        self.web3.eth.waitForTransactionReceipt(tx)
        return


def getIdMappingFromApi() -> dict:
    COINGECKO_MAPPING_URL = "https://api.coingecko.com/api/v3/coins/list?include_platform=false"
    response = requests.get(COINGECKO_MAPPING_URL)
    response_dict = {coin["symbol"]: coin["id"] for coin in response.json()}
    return response_dict


def getEthPriceFromApi(coin_symbol: str) -> int:
    id_mapping = getIdMappingFromApi()
    coin_id = id_mapping.get(coin_symbol, None)
    if not coin_id:
        return -1
    COINGECKO_API_URL = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    response = requests.get(COINGECKO_API_URL)
    response_dict = response.json()
    price = int(response_dict[coin_id]['usd'] * 1000000)
    return price


def updatePrice(coin_symbol: str) -> None:
    new_price = getEthPriceFromApi(coin_symbol)
    if new_price == -1:
        print('Invalid coin symbol.')
        return
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    obj.set_price(coin_symbol, new_price)
    return


def getPrice(coin_symbol: str) -> float:
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    return obj.get_price(coin_symbol)/1000000


if len(sys.argv) != 3:
    print("Invalid argument")
    sys.exit(0)
cmd = sys.argv[1]
coin_input = sys.argv[2].lower()
if cmd == 'get':
    print(getPrice(coin_input))
if cmd == 'set':
    updatePrice(coin_input)
