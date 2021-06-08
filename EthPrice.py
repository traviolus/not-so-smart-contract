from web3 import Web3
from web3.gas_strategies.time_based import medium_gas_price_strategy
from pyband import Client
from pyband.obi import PyObi
from pyband.message import MsgRequest
from pyband.wallet import PrivateKey
from pyband.transaction import Transaction
from typing import Tuple

import requests
import sys
import time
import os


RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')
MNEMONIC = os.getenv('MNEMONIC')
CHAIN_ID = os.getenv('CHAIN_ID')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
ACCOUNT_ADDRESS = os.getenv('ACCOUNT_ADDRESS')
INFURA_URL = os.getenv('INFURA_URL')


class BandChainConnection():
    def __init__(self):
        self.rpc_endpoint = RPC_ENDPOINT
        self.mnemonic = MNEMONIC
        self.chain_id = CHAIN_ID
        self.obi = PyObi('{symbols:[string],multiplier:u64}/{rates:[u64]}')
        self.client = None
        self.account = None
        self.sender = None
        self.pk = None

    def get_calldata(self, coin_symbol: str) -> bytes:
        calldata = self.obi.encode({"symbols": [coin_symbol], "multiplier": 1000000})
        return calldata

    def connect(self) -> None:
        self.pk = PrivateKey.from_mnemonic(self.mnemonic)
        self.client = Client(self.rpc_endpoint)
        self.sender = self.pk.to_pubkey().to_address()
        self.account = self.client.get_account(self.sender)

    def send_transaction(self, coin_symbol: str, client_id: str = 'Get data from BandChain') -> str:
        if not self.client:
            self.connect()
        calldata = self.get_calldata(coin_symbol.upper())
        message = MsgRequest(
            oracle_script_id=37,
            calldata=calldata,
            ask_count=16,
            min_count=10,
            client_id=client_id,
            fee_limit=[],
            prepare_gas=200000,
            execute_gas=1000000,
            sender=self.sender
        )
        transaction = (
            Transaction()
            .with_messages(message)
            .with_account_num(self.account.account_number)
            .with_sequence(self.account.sequence)
            .with_chain_id(self.chain_id)
            .with_gas(2000000)
            .with_fee(0)
        )
        raw_data = transaction.get_sign_data()
        signature = self.pk.sign(raw_data)
        raw_transaction = transaction.get_tx_data(signature, self.pk.to_pubkey())
        transaction_id = self.client.send_tx_block_mode(raw_transaction).tx_hash
        return transaction_id.hex()

    def get_data_from_transaction(self, transaction_id: str) -> Tuple[int, dict]:
        if not self.client:
            self.connect()
        result = None
        tries = 0
        response = requests.get(self.rpc_endpoint + "/txs/" + transaction_id)
        response.raise_for_status()
        response_dict = response.json()
        if not response_dict["logs"]:
            return -1, {"msg": "Invalid request."}
        events = response.json()["logs"][0]["events"]
        rid = events[2]["attributes"][0]["value"]
        while not result:
            if tries == 10:
                return -1, {"msg": "No result."}
            tries += 1
            time.sleep(7)
            request_info = self.client.get_request_by_id(rid)
            result = request_info.result
        request_id = result.request_id
        decoded_result = self.obi.decode_output(result.result)
        return request_id, decoded_result


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
                        "name": "_requestId",
                        "type": "uint256"
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
                    },
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

    def set_price(self, coin_symbol: str, request_id: int, new_price: int) -> None:
        transaction = self.contract.functions.set(coin_symbol, request_id, new_price).buildTransaction({
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
    conn = BandChainConnection()
    transaction_id = conn.send_transaction(coin_symbol)
    print(transaction_id)
    request_id, result = conn.get_data_from_transaction(transaction_id)
    if request_id == -1:
        print(result['msg'])
        return
    new_price = result['rates'][0]
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    obj.set_price(coin_symbol, request_id, new_price)
    return


def getPrice(coin_symbol: str) -> None:
    obj = KovanNetwork()
    obj.connect(CONTRACT_ADDRESS)
    result = obj.get_price(coin_symbol)
    if result[0] == 0:
        print(f"The price for this coin has never set.")
        return
    print(f"Request ID: {result[0]}\nPrice: {result[1]/1000000}")
    return


if len(sys.argv) != 3:
    print("Invalid argument")
    sys.exit(0)
cmd = sys.argv[1]
coin_input = sys.argv[2].lower()
if cmd == 'get':
    getPrice(coin_input)
if cmd == 'set':
    updatePrice(coin_input)
