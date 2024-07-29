import json
from web3 import Web3
from typing import Optional, Dict, Any
from dataclasses import dataclass
from eth_utils import to_checksum_address
from loguru import logger

logger.add('debug.log', format='{time},{level},{message}', level='DEBUG')

# Your data
WALLET_ADDRESS = '0x804D13e2476a849BD445FdC0071D80E8D68eC961'
PRIVATE_KEY = 'bb60101f991c21e48242a6585deb5fcdd9289185bc4f39fd52bf59569d40ce61'

BRIDGE_TOKEN = '0x0000000000000000000000000000000000000000'  # Bridge token address, if any

# Web3 setup
web3_eth = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/edcb17ba2f524017b1192f0cad991fe5'))
web3_linea = Web3(Web3.HTTPProvider('https://linea.decubate.com'))
web3_arbitrum = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
web3_polygon = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

@dataclass
class NetworkInfo:
    name: str
    chain_id: int
    web3: Web3
    on_chain_router_address: str
    cross_chain_router_address: str
    tokens: Dict[str, str]
    cross_swap_abi_path: Optional[str] = None
    on_chain_swap_abi_path: Optional[str] = None

network_infos = {
    'arbitrum': NetworkInfo(
        name='Arbitrum',
        chain_id=42161,
        web3=web3_arbitrum,
        on_chain_router_address='0x4c4AF8DBc524681930a27b2F1Af5bcC8062E6fB7',
        cross_chain_router_address='0xCa10E8825FA9F1dB0651Cd48A9097997DBf7615d',
        tokens={
            'wbtc': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
            'usdt': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'usdc': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'weth': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
        },
        cross_swap_abi_path='abis/cross_abi.json',
        on_chain_swap_abi_path='abis/woofi_abi.json'
    ),
    'linea': NetworkInfo(
        name='Linea',
        chain_id=59144,
        web3=web3_linea,
        on_chain_router_address='0x4c4AF8DBc524681930a27b2F1Af5bcC8062E6fB7',
        cross_chain_router_address='0xCa10E8825FA9F1dB0651Cd48A9097997DBf7615d',
        tokens={
            'wbtc': '0x123456...',
            'usdt': '0xA219439258ca9da29E9Cc4cE5596924745e12B93',
            'usdc': '0x176211869cA2b568f2A7D4EE941E073a821EE1ff',
            'weth': '0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f'
        },
        cross_swap_abi_path='abis/cross_abi.json',
        on_chain_swap_abi_path='abis/woofi_abi.json'
    ),
    'mainnet': NetworkInfo(
        name='Ethereum Mainnet',
        chain_id=1,
        web3=web3_eth,
        on_chain_router_address='0x4c4AF8DBc524681930a27b2F1Af5bcC8062E6fB7',
        cross_chain_router_address='0xCa10E8825FA9F1dB0651Cd48A9097997DBf7615d',
        tokens={
            'wbtc': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
            'usdt': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'usdc': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        },
        cross_swap_abi_path='abis/cross_abi.json',
        on_chain_swap_abi_path='abis/woofi_abi.json'
    ),
    'polygon': NetworkInfo(
        name='Polygon',
        chain_id=137,
        web3=web3_polygon,
        on_chain_router_address='0x4c4AF8DBc524681930a27b2F1Af5bcC8062E6fB7',
        cross_chain_router_address='0xCa10E8825FA9F1dB0651Cd48A9097997DBf7615d',
        tokens={
            'wbtc': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
            'usdt': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f',
            'usdc': '0x625e7708f30ca75bfd92586e17077590c60eb4cd',
            'weth': '0xe50fa9b3c56ffb159cb0fca61f5c9d750e8128c8'
        },
        cross_swap_abi_path='abis/cross_abi.json',
        on_chain_swap_abi_path='abis/woofi_abi.json'
    )
}

class WooFiSwap:
    def __init__(self, private_key: str, from_network: NetworkInfo, to_network: NetworkInfo):
        """
        Initializes the WooFiSwap object.

        Args:
            private_key (str): Private key for signing transactions.
            from_network (NetworkInfo): Network information for the source network.
            to_network (NetworkInfo): Network information for the target network.
        """
        self.from_network = from_network
        self.to_network = to_network
        self.private_key = private_key
        self.account = from_network.web3.eth.account.from_key(private_key)
        self.cross_swap_router = from_network.web3.eth.contract(
            address=from_network.cross_chain_router_address,
            abi=json.load(open(from_network.cross_swap_abi_path))
        )
        self.on_chain_swap_router = from_network.web3.eth.contract(
            address=from_network.on_chain_router_address,
            abi=json.load(open(from_network.on_chain_swap_abi_path))
        )

    def _execute_transaction(self, txn: Dict[str, Any]) -> Optional[dict]:
        """
        Executes a transaction on the blockchain.

        Args:
            txn (Dict[str, Any]): The transaction data.

        Returns:
            Optional[dict]: The transaction receipt if successful, or None if there is an error.

        Raises:
            Exception: If an error occurs during transaction execution.
        """
        try:
            signed_txn = self.from_network.web3.eth.account.sign_transaction(txn, private_key=self.private_key)
            txn_hash = self.from_network.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.from_network.web3.eth.wait_for_transaction_receipt(txn_hash)
            return receipt
        except Exception as e:
            logger.error(f'Error executing transaction: {e}')
            return None

    def _approve_token(self, token_address: str, amount: int, direction: str) -> Optional[dict]:
        """
        Approves a token for use by a contract.

        Args:
            token_address (str): The token address.
            amount (int): The amount of tokens to approve.
            direction (str): The direction of the swap ("on_chain" or "cross_chain").

        Returns:
            Optional[dict]: The transaction receipt if successful, or None if there is an error.

        Raises:
            Exception: If an error occurs during token approval.
        """
        try:
            token_contract = self.from_network.web3.eth.contract(address=token_address, abi=json.load(open('abis/erc20.json')))
            nonce = self.from_network.web3.eth.get_transaction_count(self.account.address)
            router = self.from_network.on_chain_router_address if direction == "on_chain" else self.from_network.cross_chain_router_address
            txn = token_contract.functions.approve(
                router,
                amount
            ).build_transaction({
                'chainId': self.from_network.chain_id,
                'gas': 50000,
                'gasPrice': self.from_network.web3.to_wei('5', 'gwei'),
                'nonce': nonce
            })
            return self._execute_transaction(txn)
        except Exception as e:
            logger.error(f'Error approving token: {e}')
            return None

    def cross_chain_swap(self, token_from: str, token_to: str, amount: float, slippage: float) -> Optional[Dict[str, Any]]:
        """
        Executes a cross-chain token swap.

        Args:
            token_from (str): The address of the token to swap from.
            token_to (str): The address of the token to swap to.
            amount (float): The amount of tokens to swap.
            slippage (float): The slippage percentage for the swap.

        Returns:
            Optional[Dict[str, Any]]: The transaction receipt if successful, or None if there is an error.
        """
        try:
            # Retrieve and log balance and gas price
            balance = self.from_network.web3.eth.get_balance(self.account.address)
            gas_price = self.from_network.web3.eth.gas_price
            logger.info(f'Balance: {self.from_network.web3.from_wei(balance, "ether")} ETH')
            logger.info(f'Gas Price: {self.from_network.web3.from_wei(gas_price, "gwei")} Gwei')

            # Convert amount to wei and calculate minimum output amount
            amount_in = self.from_network.web3.to_wei(amount, 'ether')
            amount_out_min = int(amount_in * (1 - slippage / 100))
            nonce = self.from_network.web3.eth.get_transaction_count(self.account.address)

            # Convert token addresses to checksum format
            token_from_checksum = self.from_network.web3.to_checksum_address(token_from)
            token_to_checksum = self.to_network.web3.to_checksum_address(token_to)

            # Approve tokens
            self._approve_token(token_from_checksum, amount_in, direction="cross_chain")

            # Prepare transaction data
            src_infos = {
                'fromToken': token_from_checksum,
                'bridgeToken': self.from_network.web3.to_checksum_address(BRIDGE_TOKEN),
                'fromAmount': amount_in,
                'minBridgeAmount': amount_out_min
            }

            dst_infos = {
                'chainId': int(self.to_network.chain_id),
                'toToken': token_to_checksum,
                'bridgeToken': self.from_network.web3.to_checksum_address(BRIDGE_TOKEN),
                'minToAmount': amount_out_min,
                'airdropNativeAmount': 0,
                'dstGasForCall': 0
            }

            txn = self.cross_swap_router.functions.crossSwap(
                {
                    'fromToken': src_infos['fromToken'],
                    'bridgeToken': src_infos['bridgeToken'],
                    'fromAmount': src_infos['fromAmount'],
                    'minBridgeAmount': src_infos['minBridgeAmount']
                },
                {
                    'chainId': dst_infos['chainId'],
                    'toToken': dst_infos['toToken'],
                    'bridgeToken': dst_infos['bridgeToken'],
                    'minToAmount': dst_infos['minToAmount'],
                    'airdropNativeAmount': dst_infos['airdropNativeAmount'],
                    'dstGasForCall': dst_infos['dstGasForCall']
                },
                {
                    'receiver': self.account.address,
                    'data': b''  # Optional data for the transaction
                },
                {
                    'sender': self.account.address,
                    'data': b''  # Optional data for the transaction
                }
            ).build_transaction({
                'chainId': self.from_network.chain_id,
                'gas': 2000000,  # Estimate a reasonable amount of gas
                'gasPrice': gas_price,
                'nonce': nonce
            })

            # Estimate gas and check if there is enough balance
            estimated_gas = self.from_network.web3.eth.estimate_gas(txn)
            max_gas_cost = estimated_gas * gas_price

            logger.info(f'Estimated Gas: {estimated_gas}')
            logger.info(f'Max Gas Cost: {self.from_network.web3.from_wei(max_gas_cost, "ether")} ETH')

            if balance < max_gas_cost:
                raise ValueError(f"Insufficient funds for gas: have {self.from_network.web3.from_wei(balance, 'ether')} ETH, need {self.from_network.web3.from_wei(max_gas_cost, 'ether')} ETH")

            return self._execute_transaction(txn)
        except Exception as e:
            logger.error(f'Error executing cross-chain swap: {e}')
            return None

    def on_chain_swap(self, token_from: str, token_to: str, amount: float, slippage: float) -> Optional[Dict[str, Any]]:
        """
        Executes an on-chain token swap.

        Args:
            token_from (str): The address of the token to swap from.
            token_to (str): The address of the token to swap to.
            amount (float): The amount of tokens to swap.
            slippage (float): The slippage percentage for the swap.

        Returns:
            Optional[Dict[str, Any]]: The transaction receipt if successful, or None if there is an error.
        """
        if not self.on_chain_swap_router:
            logger.error("On-chain swap ABI path is not set.")
            return None

        try:
            # Retrieve and log balance and gas price
            balance = self.from_network.web3.eth.get_balance(self.account.address)
            gas_price = self.from_network.web3.eth.gas_price
            logger.info(f'Balance: {self.from_network.web3.from_wei(balance, "ether")} ETH')
            logger.info(f'Gas Price: {self.from_network.web3.from_wei(gas_price, "gwei")} Gwei')

            # Convert amount to wei and calculate minimum output amount
            amount_in = self.from_network.web3.to_wei(amount, 'ether')
            amount_out_min = int(amount_in * (1 - slippage / 100))
            nonce = self.from_network.web3.eth.get_transaction_count(self.account.address)

            # Convert token addresses to checksum format
            token_from_checksum = self.from_network.web3.to_checksum_address(token_from)
            token_to_checksum = self.from_network.web3.to_checksum_address(token_to)

            # Approve tokens
            self._approve_token(token_from_checksum, amount_in, direction="on_chain")

            # Prepare transaction data
            txn = self.on_chain_swap_router.functions.swap(
                token_from_checksum,
                token_to_checksum,
                amount_in,
                amount_out_min,
                self.account.address,  # Address to receive the swapped tokens
                self.account.address   # Address sending the tokens (same as receiving in this case)
            ).build_transaction({
                'chainId': self.from_network.chain_id,
                'gas': 2000000,  # Estimate a reasonable amount of gas
                'gasPrice': gas_price,
                'nonce': nonce
            })

            logger.info(f'Transaction: {txn}')

            # Estimate gas and check if there is enough balance
            try:
                estimated_gas = self.from_network.web3.eth.estimate_gas({
                    'to': txn['to'],
                    'data': txn['data'],
                    'value': txn.get('value', 0)
                })
            except Exception as e:
                logger.error(f'Error estimating gas: {e}')
                return None

            max_gas_cost = estimated_gas * gas_price
            logger.info(f'Estimated Gas: {estimated_gas}')
            logger.info(f'Max Gas Cost: {self.from_network.web3.from_wei(max_gas_cost, "ether")} ETH')

            if balance < max_gas_cost:
                raise ValueError(f"Insufficient funds for gas: have {self.from_network.web3.from_wei(balance, 'ether')} ETH, need {self.from_network.web3.from_wei(max_gas_cost, 'ether')} ETH")

            # Execute transaction
            tx_hash = self.from_network.web3.eth.send_transaction(txn)
            receipt = self.from_network.web3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f'Transaction receipt: {receipt}')
            return receipt
        except Exception as e:
            logger.error(f'Error executing on-chain swap: {e}')
            return None



if __name__ == '__main__':
    # Выбор сети
    from_network = network_infos['mainnet']
    to_network = network_infos['linea']

    gas_price = from_network.web3.eth.gas_price
    print(f'Summary gas price about: {from_network.web3.from_wei(gas_price, "gwei")} Gwei')

    woo_fi_swap = WooFiSwap(PRIVATE_KEY, from_network, to_network)

    swap_type = 'on_chain'

    if swap_type == 'on_chain':
        receipt = woo_fi_swap.on_chain_swap(
            token_from=from_network.tokens['weth'],
            token_to=to_network.tokens['usdc'],
            amount=0.001,
            slippage=1.0
        )
    elif swap_type == 'cross_chain':
        receipt = woo_fi_swap.cross_chain_swap(
            token_from=from_network.tokens['weth'],
            token_to=to_network.tokens['usdc'],
            amount=0.001,
            slippage=1.0
        )
    else:
        raise ValueError("Invalid swap type. Choose 'on_chain' or 'cross_chain'.")

    # Печать результата
    print(receipt)