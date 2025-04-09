import random
import string
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Token
from .serializers import TokenSerializer
from web3 import Web3
from .config import Config
from web3.exceptions import ContractLogicError, TransactionNotFound, TimeExhausted

config = Config()


def generate_random_string(length=20):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


class TokenCreateView(APIView):

    def post(self, request):
        data = request.data
        unique_hash = generate_random_string()
        while Token.objects.filter(unique_hash=unique_hash).exists():
            unique_hash = generate_random_string()

        serializer = TokenSerializer(data=data)
        if serializer.is_valid():
            token = serializer.save(unique_hash=unique_hash)

            try:
                # Подключение к контракту
                web3 = Web3(Web3.HTTPProvider(config.infura_url))
                if not web3.is_connected():
                    return Response({"error": "Не удалось подключиться к Ethereum"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                wallet_address = "0xd22D2e846f99646ABcB0C111A208dEB7955CbD1d"
                web3.eth.default_account = wallet_address
                contract = web3.eth.contract(address=config.contract_address, abi=config.contract_abi)

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
                signed_txn = web3.eth.account.sign_transaction(transaction, private_key=config.private_key)

                # Отправка подписанной транзакции
                tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

                # Ожидание подтверждения транзакции (опционально)
                web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                # Сохранение хеша транзакции в объект Token
                token.tx_hash = web3.to_hex(tx_hash)
                token.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except ContractLogicError:
                return Response({"error": "Ошибка логики контракта при вызове функции mint"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except TransactionNotFound:
                return Response({"error": "Транзакция не найдена в сети Ethereum"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except TimeExhausted:
                return Response({"error": "Время ожидания подтверждения транзакции истекло"},
                                status=status.HTTP_504_GATEWAY_TIMEOUT)
            except Exception as e:
                return Response({"error": f"Произошла непредвиденная ошибка: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractGetTotalSupplyView(RetrieveAPIView):
    def get(self, request):
        try:
            web3 = Web3(Web3.HTTPProvider(config.infura_url))
            if not web3.is_connected():
                return Response({"error": "Не удалось подключиться к Ethereum"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            contract = web3.eth.contract(address=config.contract_address, abi=config.contract_abi)

            try:
                total_supply = contract.functions.totalSupply().call()
            except ContractLogicError:
                return Response({"error": "Ошибка при вызове функции смарт-контракта"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"total_supply": total_supply}, status=status.HTTP_200_OK)

        except Exception as e:
            # Обработка других неожиданных ошибок
            return Response({"error": f"Произошла непредвиденная ошибка: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListOfTokensView(APIView):
    def get(self, request):
        try:
            tokens = list(Token.objects.all())
            serializer = TokenSerializer(tokens, many=True)
            return Response({"all_tokens": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Не удалось получить список токенов: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
