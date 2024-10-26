import random
import string

import yaml
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Token
from .serializers import TokenSerializer
from web3 import Web3


def generate_random_string(length=20):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


class TokenCreateView(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)

        self.private_key = config['blockchain']['private_key']
        self.infura_url = config['blockchain']['infura_url']
        self.contract_address = config['blockchain']['contract_address']
        self.contract_abi = config['blockchain']['contract_abi']

    def post(self, request):
        data = request.data
        unique_hash = generate_random_string()
        while Token.objects.filter(unique_hash=unique_hash).exists():
            unique_hash = generate_random_string()

        serializer = TokenSerializer(data=data)
        if serializer.is_valid():
            token = serializer.save(unique_hash=unique_hash)

            # Подключение к контракту
            web3 = Web3(Web3.HTTPProvider(self.infura_url))
            wallet_address = "0xd22D2e846f99646ABcB0C111A208dEB7955CbD1d"
            web3.eth.default_account = wallet_address
            contract = web3.eth.contract(address=self.contract_address, abi=self.contract_abi)

            if not web3.is_connected():
                return Response({"error": "Не удалось подключиться к Ethereum"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Создание транзакции
            nonce = web3.eth.get_transaction_count(web3.eth.default_account)
            transaction = contract.functions.mint(
                web3.eth.default_account,
                token.unique_hash,
                token.media_url
            ).build_transaction({
                'chainId': 11155111,
                'gas': 70000,
                'maxFeePerGas': web3.to_wei('2', 'gwei'),
                'maxPriorityFeePerGas': web3.to_wei('1', 'gwei'),
                'nonce': nonce
            })

            # Подписывание транзакции
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=self.private_key)

            # Отправка подписанной транзакции
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Сохранение хеша транзакции в объект Token
            token.tx_hash = web3.to_hex(tx_hash)
            token.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
