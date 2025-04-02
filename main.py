from client import Client
import asyncio
from Quick_swap import Quickswap



# код под EIP1559, если Legacy - надо менять

async def main():
    client=Client(rpc='',private_key='')
    Quickswapp = Quickswap(client=client)

    #Свап ETH в USDC
    # result = await Quickswapp.swap_native_to_token(
    #     contract_address='0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
    #     native_amount=1.5,
    #     slippage=2)
    # print(result)

    #Свап USDC  в ETH
    # result = await Quickswapp.swap_token_to_eth(contract_address='0xf5b509bB0909a69B1c207E495f687a596C168E12', value=0.1, slippage=1)
    # print(result)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

