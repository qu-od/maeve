from typing import Dict, List, Literal, Any
import os
import functools

import psycopg2
from psycopg2 import sql


"""
МОЖЕТ ЛИ УПАСТЬ СКОРОСТЬ ВЫПОЛНЕНИЯ КОМАНД
ЕСЛИ НА КАЖДОМ ЗАПРОСЕ МЫ БУДЕМ ОТКРЫВАТЬ И ЗАКРЫВАТЬ ИНТЕРНЕТ СОЕДИНЕНИЕ?
для редких операций (как функ. из _user_admission) это ничего страшного,
ведь они вызываются относительно_редко_
"""

# ------------------------------- TYPES ----------------------------------------
Line = str

Schema = str
TableName = str
Query = str

ColumnName = str
SqlType = Literal[
    'varchar(10)', 'varchar(50)',
    'varchar(100)', 'varchar(300)',
    'integer', 'real', 'date',
    'bool', 'bigint', 'text',
    'smallint',
]
Columns = Dict[ColumnName, SqlType]


# --------------------------- FUNCS --------------------------------------------


# ------------------------- DATABASE CLASS -------------------------------------
class Database:

    @staticmethod
    def _get_connection() -> Any:
        """
        database url and password depend on environment
        that could be local or cloud
        """
        db_url = os.getenv('DATABASE_URL')
        if db_url == 'localhost':
            db_password = os.getenv('DATABASE_PASSWORD')
            conn = psycopg2.connect(
                dbname='Maeve',
                user='postgres',
                password=db_password,
                host=db_url
            )
        else:
            conn = psycopg2.connect(
                db_url,
                sslmode='require'
            )
        return conn

    @staticmethod
    def _with_cursor(execute_func):
        def wrapper_with_cursor(self, query):
            with Database._get_connection() as conn:  # TODO: DO NOT CLOSE CONN!
                with conn.cursor() as cursor:
                    value = execute_func(self, cursor, query)
            return value
        return wrapper_with_cursor

    @_with_cursor  # wow, don't need to type "self" here apparently
    def exec_select(self, cursor, query: str) -> List[tuple]:
        cursor.execute(query)
        return cursor.fetchall()

    @_with_cursor
    def exec_void(self, cursor, query: str):
        cursor.execute(query)

    def delete_table(self, name: str):
        """ Table format: table_schema.table_name"""
        self.exec_void(f'DROP TABLE {name};')

    def create_table(self, name: TableName, columns: Columns):
        columns_for_query: str = ",\n".join(
            f'{c_name} {c_type}'
            for c_name, c_type in columns.items()
        )
        self.exec_void(
            f'CREATE TABLE {name} ({columns_for_query});'
        )
