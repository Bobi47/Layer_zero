import json
import asyncio
import config
import random

from decimal import Decimal
from client import Client
from web3 import AsyncWeb3
from web3.middleware import async_geth_poa_middleware


def read_json(filename):
    with open(filename) as f:
        return json.load(f)


async def connect_w3(rpc_url,client : Client):
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(
        endpoint_uri=rpc_url,
        request_kwargs={'proxy': client.proxy}
    ))
    w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
    return w3



class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: int | float | str | Decimal, decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = int(amount)
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals

    def __str__(self):
        return f'{self.Wei}'


def choose_rpc(chain_from :  str):
    chain_from = chain_from.upper()
    if chain_from in config.lst_of_rpc:
        return config.lst_of_rpc[chain_from]
    else:
        print(f'Имя сети {chain_from} не соответствует ARB,OP,BASE,SCR')

def choose_contract_address(chain_from: str):
    chain_from = chain_from.upper()
    lst = {
        'OP':'0xe8CDF27AcD73a434D661C84887215F7598e7d0d3',
        'ARB':'0xA45B5130f36CDcA45667738e2a258AB09f4A5f7F',
        'BASE':'0xdc181Bd607330aeeBEF6ea62e03e5e1Fb4B6F7C7',
        'LINEA':'0x81F6138153d473E8c5EcebD3DC8Cd4903506B075'
    }
    if chain_from in lst:
        return lst[chain_from]
    else:
        print(f'Имя сети {chain_from} не соответствует ARB,OP,BASE,SCR')

def choose_dsteid(chain_to: str):
    chain_to = chain_to.upper()
    lst = {
        'OP':30111,
        'ARB':30110,
        'BASE':30184,
        'LINEA':30183,
    }

    if chain_to in lst:
        return lst[chain_to]
    else:
        print(f'Имя сети {chain_to} не соответствует ARB,OP,BASE,SCR')

async def check_balance( client: Client):
    dict_of_balances = {}

    for chain_name, rpc_url in config.lst_of_rpc.items():
        w3 = await connect_w3(rpc_url=rpc_url,client=client)
        if await w3.is_connected():
            balance_wei = await w3.eth.get_balance(client.account.address)
            balance_eth = w3.from_wei(balance_wei, 'ether')  # Decimal
            balance_eth_formatted = f"{float(balance_eth):.18f}"
            dict_of_balances[chain_name] = balance_eth_formatted
        else:
            raise Exception(f"Failed to connect to {chain_name} RPC")

    return dict_of_balances

async def wait_for_balance_change(client_to: Client,
                                  last_balance,
                                  interval: float = 20):
    last_balance = float(last_balance)
    deadline = asyncio.get_event_loop().time() + config.timeout

    while True:
        current_balance_wei = await client_to.w3.eth.get_balance(client_to.account.address)
        current_balance_eth = client_to.w3.from_wei(current_balance_wei, 'ether')
        balance_eth_formatted = f"{float(current_balance_eth):.18f}"

        if float(balance_eth_formatted) > last_balance:
            print(f"✅ Средства получены! Новый баланс: {balance_eth_formatted}")
            break

        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError("❌ Истекло время ожидания поступления средств")

        await asyncio.sleep(interval)

    # ⏳ Спим после окончания слежения
    await asyncio.sleep(config.sleep_seconds)
    return balance_eth_formatted



async def check_min_balance(dict_of_balances : dict):
    dict_of_normal_balances = {}
    for key,value in dict_of_balances.items():
        if float(value) >= config.min_balance:
            dict_of_normal_balances[key] = value
    return dict_of_normal_balances


def generate_path(available_balances: dict):
    path = []
    if available_balances:
        path.append(random.choice(list(available_balances.keys())))


    networks = config.networks
    path_length = random.randint(config.count_of_bridges[0], config.count_of_bridges[1])

    used = False  # флаг, использовалась ли LINEA

    while len(path) < path_length:
        available = networks.copy()

        if used:
            available.remove(config.chain_one_bridge)

        if path:
            available = [net for net in available if net != path[-1]]

        next_net = random.choice(available)
        path.append(next_net)

        if next_net == config.chain_one_bridge:
            used = True


    if config.last_chain:

        if path[-1] in config.last_chain:
            pass
        else:
            path.append(config.last_chain)

    return path


async def balances(client:Client):
    all_balances = await check_balance(client=client)
    available_balances = await check_min_balance(all_balances)
    # print(available_balances)
    if not all_balances:
        print('Не хватает балансов везде!!!')
        return
    # available_balances = {'ARB': '0.000278255888882360','OP':'0.00021'}
    path = generate_path(available_balances)
    balance = float(available_balances[path[0]])
    balance = TokenAmount(amount=balance)
    return all_balances,available_balances,path,balance

def load_private_keys(file_path: str) -> list[str]:
    with open(file_path, 'r') as file:
        private_keys = [line.strip() for line in file if line.strip()]
    return private_keys



