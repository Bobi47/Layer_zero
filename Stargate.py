from decimal import Decimal

from client import Client
from web3 import AsyncWeb3
from models import read_json, TokenAmount, choose_dsteid


class Stargate:
    def __init__(self, client: Client):
        self.client = client

    async def get_raw_tx_params(self, value: int = 0):

        latest_block = await self.client.w3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.client.w3.eth.max_priority_fee

        return {
            "chainId": await self.client.w3.eth.chain_id,
            "nonce": await self.client.w3.eth.get_transaction_count(self.client.account.address),
            "from": self.client.account.address,
            "value": value,
            "maxFeePerGas": base_fee + max_priority_fee,
            "maxPriorityFeePerGas": max_priority_fee,
            "type": 2  # обязательно указываем, что это EIP-1559 tx
        }

    async def bridge(self, contract_address: str, native_amount: Decimal, slippage: int | float, chain_to : str):

        address_contract_router = AsyncWeb3.to_checksum_address(contract_address)
        contract_router = self.client.w3.eth.contract(
            address=address_contract_router,
            abi=read_json(filename='ABI/stargate_op.json')
        )

        amount_in = TokenAmount(amount=native_amount)


        amount_out_min = TokenAmount(
            amount=native_amount*((100 - slippage)/100)
        )


        bytes32_address = AsyncWeb3.to_bytes(hexstr=self.client.account.address).rjust(32, b'\x00')

        sendParam = (
            int(choose_dsteid(chain_to=chain_to)),
            bytes32_address,
            amount_in.Wei,
            amount_out_min.Wei,
            AsyncWeb3.to_bytes(hexstr='0x'),
            AsyncWeb3.to_bytes(hexstr='0x'),
            AsyncWeb3.to_bytes(hexstr='0x01'),
        )


        fee_nativeFee = await contract_router.functions.quoteSend(sendParam, False).call()


        data = contract_router.encodeABI(
            fn_name='send',
            args=[
                sendParam,
                fee_nativeFee,
                self.client.account.address
            ]
        )

        value = amount_in.Wei +fee_nativeFee[0]

        tx_hash = await self.client.send_transaction(
            to=contract_router.address,
            data=data,
            value=value,
            eip1559 = False,
            increase_gas=1
        )

        if tx_hash:
            try:
                await self.client.verif_tx(tx_hash=tx_hash)
                print(
                    f'tx_hash: {tx_hash.hex()}')
                return tx_hash.hex(), amount_out_min
            except Exception as err:
                print(f'Transaction error!! tx_hash: {tx_hash.hex()}; error: {err}')
        else:
            print(f'Transaction error!!')
