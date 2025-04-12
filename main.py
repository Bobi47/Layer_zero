import asyncio
import random
from decimal import Decimal

import config
from Stargate import Stargate
from models import (
    choose_rpc,
    choose_contract_address,
    wait_for_balance_change,
    balances,
    check_balance,
    load_private_keys,
)
from client import Client
from DB.add_edit import create_db


async def run_wallet(private_key: str, semaphore: asyncio.Semaphore = None):
    if semaphore:
        async with semaphore:
            await bridge_flow(private_key)
    else:
        await bridge_flow(private_key)


async def bridge_flow(private_key: str):
    all_balances, available_balances, path, balance = await balances(
        client=Client(rpc="", private_key=private_key)
    )
    print(path)

    for number in range(len(path) - 1):
        client_from = Client(rpc=choose_rpc(path[number]), private_key=private_key)
        client_to = Client(rpc=choose_rpc(path[number + 1]), private_key=private_key)

        all_balances = await check_balance(client=client_to)
        Stargatee = Stargate(client=client_from)

        decrease_factor = 1.0
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            try:
                amount_factor = round(random.uniform(0.9, 0.92), 2)
                native_amount = float(balance.Ether * Decimal(str(amount_factor)) * Decimal(decrease_factor))

                tx_hash,amount_out_min = await Stargatee.bridge(
                    contract_address=choose_contract_address(path[number]),
                    native_amount=native_amount,
                    slippage=config.slippage,
                    chain_to=path[number + 1]
                )

                print(f'Сделали транзу из {path[number]} в {path[number + 1]}, будет получено {amount_out_min.Ether:.18f}')
                create_db(client=client_from, hash=tx_hash)

                await wait_for_balance_change(
                    client_to=client_to,
                    last_balance=all_balances[path[number + 1]],
                )
                break

            except ValueError as e:
                if 'insufficient funds' in str(e).lower():
                    print(f"❌ Недостаточно средств. Попытка #{attempt + 1}. Уменьшаем сумму на 10% и пробуем снова...")
                    decrease_factor *= 0.9
                    attempt += 1
                    await asyncio.sleep(10)
                else:
                    raise

        else:
            print("🚫 Превышено количество попыток из-за недостатка средств.")


async def runner():
    tasks = []

    semaphore = asyncio.Semaphore(config.max_concurrent_tasks) if config.max_concurrent_tasks else None

    wallets = load_private_keys('wallets.txt')

    for pk in wallets:
        tasks.append(run_wallet(pk, semaphore))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(runner())
