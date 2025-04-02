import asyncio
import time
from client import Client
from web3 import AsyncWeb3
from models import read_json


class Quickswap:
    def __init__(self, client: Client):
        self.client = client

    async def get_raw_tx_params(self, value: int = 0):

        latest_block = await self.client.w3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.client.w3.eth.max_priority_fee  # можешь изменить при необходимости

        return {
            "chainId": await self.client.w3.eth.chain_id,
            "nonce": await self.client.w3.eth.get_transaction_count(self.client.account.address),
            "from": self.client.account.address,
            "value": value,
            "maxFeePerGas": base_fee + max_priority_fee,
            "maxPriorityFeePerGas": max_priority_fee,
            "type": 2  # обязательно указываем, что это EIP-1559 tx
        }

    async def swap_native_to_token(self, contract_address: str, native_amount: float, slippage: int):

        address_contract_router = AsyncWeb3.to_checksum_address(contract_address)
        contract_router = self.client.w3.eth.contract(
            address=address_contract_router,
            abi=read_json(filename='abi/contract_QuickSwap_v2.json')
        )

        address_to_token = AsyncWeb3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359')
        to_token_contract = self.client.w3.eth.contract(
            address=address_to_token,
            abi=read_json(filename='./abi/usdccc.json')
        )

        token_decimals = await to_token_contract.functions.decimals().call()

        amount_out_min = int(
            native_amount
            * await self.client.get_token_price('POL')
            * (1 - slippage / 100)
            * 10 ** token_decimals
        )

        path_of_addresses = [
            AsyncWeb3.to_checksum_address('0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'),
            AsyncWeb3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359')
        ]

        deadline = int(time.time()) + 1200

        value = AsyncWeb3.to_wei(native_amount, 'ether')

        tx_params = await contract_router.functions.swapExactETHForTokens(
            amount_out_min,
            path_of_addresses,
            self.client.account.address,
            deadline,
        ).build_transaction(
            await self.get_raw_tx_params(value=value)
        )

        signed_tx = self.client.w3.eth.account.sign_transaction(tx_params, self.client.private_key)
        tx_hash_bytes = await self.client.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return await self.client.verif_tx(tx_hash_bytes)

    async def swap_token_to_eth(self, contract_address: str, value: float, slippage: int):

        address_contract_router = AsyncWeb3.to_checksum_address(contract_address)
        contract_router = self.client.w3.eth.contract(
            address=address_contract_router,
            abi=read_json(filename='abi/Contractc_QuckSwap_v3.json')
        )

        address_from_token = AsyncWeb3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359')
        from_token_contract = self.client.w3.eth.contract(
            address=address_from_token,
            abi=read_json(filename='./abi/usdccc.json')
        )

        approve_balance = await from_token_contract.functions.allowance(
            self.client.account.address,
            address_contract_router
        ).call()

        from_token_decimals = await from_token_contract.functions.decimals().call()

        # approve
        if value > approve_balance:
            value = int(
                value * 10 ** from_token_decimals
            )

            # approve
            tx_params = await from_token_decimals.functions.approve(
                contract_router.address,
                value
            ).build_transaction(await self.get_raw_tx_params())

            signed_tx = self.client.w3.eth.account.sign_transaction(tx_params, self.client.private_key)
            tx_hash_bytes = await self.client.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            a = await self.client.verif_tx(tx_hash_bytes)
            print(f'Успешно апрувнили {value}, {a}')
            await asyncio.sleep(10)

        amountIn = int(value * 10 ** from_token_decimals)

        amountOutMinimum = int(
            value
            * await self.client.get_token_price('POL')
            * (1 - slippage / 100)
            * 10 ** 18
        )

        address_0 = AsyncWeb3.to_checksum_address('0x0000000000000000000000000000000000000000')

        path = [
            AsyncWeb3.to_checksum_address('0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'),
            AsyncWeb3.to_checksum_address('0x8f3cf7ad23cd3cadbd9735aff958023239c6a063'),
            AsyncWeb3.to_checksum_address('0xa3fa99a148fa48d14ed51d610c367c61876997f1'),
            AsyncWeb3.to_checksum_address('0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270'),
        ]
        b_path = []
        for address in path:
            b_path.append(
                AsyncWeb3.to_bytes(hexstr=address)
            )
        joined_path = b''.join(b_path)

        data = contract_router.encodeABI(
            fn_name='exactInput',
            args=[(
                joined_path,
                address_0,
                int(time.time() + 1200),
                amountIn,
                amountOutMinimum
            )]
        )

        data_2 = contract_router.encodeABI(
            fn_name='unwrapWNativeToken',
            args=[
                amountOutMinimum,
                self.client.account.address
            ]
        )

        tx_hash = await self.client.send_transaction(
            to=address_contract_router,
            data=contract_router.encodeABI('multicall', args=[
                [data, data_2]
            ]),
            max_priority_fee_per_gas=self.client.max_priority_fee()
        )

        if tx_hash:
            try:
                await self.client.verif_tx(tx_hash=tx_hash)
                print(
                    f'tx_hash: {tx_hash.hex()}')
            except Exception as err:
                print(f'Transaction error!! tx_hash: {tx_hash.hex()}; error: {err}')
        else:
            print(f'Transaction error!!')
