from web3 import Web3
from eth_utils import to_checksum_address

address = '0x804D13e2476a849BD445FdC0071D80E8D68eC961'
address = to_checksum_address(address)
infura_url = 'https://linea.decubate.com'

web3=Web3(Web3.HTTPProvider(infura_url))

def get_balance(address: str, infura_url: str) -> float:
    # Преобразуем адрес в формат чек-суммы
    address = to_checksum_address(address)

    # Подключаемся к Infura
    web3 = Web3(Web3.HTTPProvider(infura_url))

    # Получаем баланс
    balance = web3.eth.get_balance(address)

    # Конвертируем баланс из Wei в эфир
    balance_in_ether = web3.from_wei(balance, 'ether')

    return balance_in_ether


balance = get_balance(address, infura_url)
print(balance)