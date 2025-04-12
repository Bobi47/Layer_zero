from sqlalchemy import create_engine, text  # Импортируем функции для создания движка БД (create_engine) и текстового запроса (text)
from sqlalchemy.exc import DatabaseError     # Импортируем класс ошибки DatabaseError для обработки ошибок работы с БД
from sqlalchemy.orm import Session          # Импорт сессии ORM, через которую работаем с объектами БД
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # Импорт базового класса для декларативных моделей, а также типов аннотаций Mapped и mapped_column
from sqlalchemy import Integer, String, DateTime      # Импортируем типы столбцов Integer и String
from sqlalchemy import select               # Импорт функции select для написания запросов
from datetime import datetime

import time                                 # Модуль time для получения текущего времени (timestamp)





class DB:
    def __init__(self, db_url: str, **kwargs):
        """
        Initializes a class.

        :param str db_url: a URL containing all the necessary parameters to connect to a DB
        """
        self.db_url = db_url  # Сохраняем URL подключения к базе данных
        self.engine = create_engine(self.db_url, **kwargs)  # Создаём «движок» SQLAlchemy с заданными параметрами
        self.Base = None      # Это будет ссылка на нашу базу декларативных моделей (присвоим позже)
        self.s: Session = Session(bind=self.engine)  # Создаём ORM-сессию, привязанную к движку
        self.conn = self.engine.connect()            # Устанавливаем соединение (Connection) для низкоуровневых запросов

    def create_tables(self, base):
        """
        Creates tables.

        :param base: a base class for declarative class definitions
        """
        self.Base = base                                   # Сохраняем базовый класс (DeclarativeBase)
        self.Base.metadata.create_all(self.engine)         # Создаём таблицы в базе на основании метаданных класса base

    def all(self, entities=None, *criterion, stmp=None) -> list:
        """
        Fetches all rows.

        :param entities: an ORM entity
        :param stmp: stmp
        :param criterion: criterion for rows filtering
        :return list: the list of rows
        """
        if stmp is not None:
            return list(self.s.scalars(stmp).all())  # Если передан stmp (готовый выраженный запрос), используем его и возвращаем все объекты

        if entities and criterion:
            return self.s.query(entities).filter(*criterion).all()  # Если указан класс сущности и критерии, делаем запрос с фильтрацией

        if entities:
            return self.s.query(entities).all()  # Если указан класс сущности, но нет критериев, возвращаем все записи

        return []  # Если ничего не указано, возвращаем пустой список

    def one(self, entities=None, *criterion, stmp=None, from_the_end: bool = False):
        """
        Fetches one row.

        :param entities: an ORM entity
        :param stmp: stmp
        :param criterion: criterion for rows filtering
        :param from_the_end: get the row from the end
        :return list: found row or None
        """
        if entities and criterion:
            rows = self.all(entities, *criterion)  # Если есть сущность и критерии, получаем список всех подходящих строк
        else:
            rows = self.all(stmp=stmp)             # Иначе, если есть stmp, получаем строки через stmp

        if rows:
            if from_the_end:
                return rows[-1]  # Если нужно взять «с конца», берём последний элемент
            return rows[0]       # Иначе — первый
        return None              # Если нет строк, возвращаем None

    def execute(self, query, *args):
        """
        Executes SQL query.

        :param query: the query
        :param args: any additional arguments
        """
        result = self.conn.execute(text(query), *args)  # Выполняем сырой SQL-запрос через Connection
        self.commit()                                   # Сразу делаем commit изменений
        return result

    def commit(self):
        """
        Commits changes.
        """
        try:
            self.s.commit()       # Пробуем зафиксировать изменения в сессии
        except DatabaseError:
            self.s.rollback()     # Если поймали ошибку БД, откатываем транзакцию

    def insert(self, row: object | list[object]):
        """
        Inserts rows.

        :param Union[object, list[object]] row: an ORM entity or list of entities
        """
        if isinstance(row, list):
            self.s.add_all(row)   # Если передан список сущностей, добавляем все сразу
        elif isinstance(row, object):
            self.s.add(row)       # Если одна сущность, добавляем её
        else:
            raise ValueError('Wrong type!')  # Если тип данных некорректен

        self.commit()  # После добавления фиксируем изменения


class Base(DeclarativeBase):
    pass  # Базовый класс для наших декларативных моделей


class Wallet(Base):
    __tablename__ = 'wallets'  # Название таблицы в БД

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Первичный ключ с автоинкрементом
    private_key: Mapped[str] = mapped_column(String, unique=True)                  # Уникальный ключ (приватник)
    address: Mapped[str] = mapped_column(String)                                   # Адрес кошелька
    numbers_of_transactions: Mapped[int] = mapped_column(Integer)                          # Количество swap-операций
    time_last_activity: Mapped[int] = mapped_column(Integer)  # Время (timestamp)
    datetime_last_activity: Mapped[datetime] = mapped_column(DateTime)

