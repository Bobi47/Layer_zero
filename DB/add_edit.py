from DB.Class_DB import DB,Base,Wallet
import time
from client import Client
from datetime import datetime


db = DB('sqlite:///wallets_of_stargate.db')  # Создаём объект DB, указывая строку подключения к SQLite
db.create_tables(Base)                       # Создаём таблицы (если их ещё нет), используя класс Base


# db.insert([
#     Wallet(private_key='pk1', address='addr1', numbers_of_swap=1, numbers_of_lending=2, time=int(time.time())),
#     Wallet(private_key='pk2', address='addr2', numbers_of_swap=3, numbers_of_lending=1, time=int(time.time()))
# ])  # Добавляем два кошелька (Wallet) в таблицу
#
#
# wallets = db.all(Wallet)  # Получаем все объекты Wallet из базы
# for w in wallets:
#     print(w.address, w.private_key)  # Выводим address и private_key каждого кошелька
#
#
# wallet = db.one(Wallet, Wallet.private_key == 'pk1')
# wallet.address = wallet.address + '1'
''''''

def create_db(client: Client,hash):
    if len(hash) == 66:
        wallets = db.all(Wallet)
        lst_of_addresses = []
        for w in wallets:
            lst_of_addresses.append(w.address)

        if  client.account.address in lst_of_addresses:
            wallet = db.one(Wallet,
                            Wallet.address == client.account.address)
            wallet.numbers_of_transactions+=1
            wallet.time_last_activity = int(time.time())
            wallet.datetime_last_activity = datetime.now().replace(microsecond=0)
            db.commit()
        else:
            db.insert([
                Wallet(private_key=client.private_key,
                       address=client.account.address,
                       numbers_of_transactions=1,
                       time_last_activity=int(time.time()),
                       datetime_last_activity=datetime.now().replace(microsecond=0)
                       ),
            ])
    else:
        print('Базу данных не создаём')
