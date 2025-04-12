import random


networks = ['OP', 'ARB', 'BASE', 'LINEA']
chain_one_bridge = 'LINEA' # Сеть, которую мы будем юзать один раз ARB,OP,BASE,LINEA
count_of_bridges = [2,2] #Колличество свапов
last_chain = False # ''  ARB,OP,BASE,LINEA в какой сети должны оказать средства после завершения работы скрипта
min_balance = 0.0002 #мин баланс, для отправления транзы


slippage = 0.5 # int
sleep_seconds = random.randint(1,3) # задержка между свапами в секундах 86400 - сутки
timeout = 1800 #int сколько максимум ждем пополнения кошелька

lst_of_rpc = {
    'OP': '', #https://dashboard.alchemy.com/
    'ARB': '',
    'BASE': '',
    'LINEA': ''
}


max_concurrent_tasks = 2