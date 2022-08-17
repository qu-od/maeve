from typing import Dict, List, Literal, Any, Optional, Tuple
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
# TODO secure database queries from something something!
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

    # ----------------------------- TABLE QUERIES ------------------------------
    def delete_table(self, name: str):
        """ Table format: table_schema.table_name"""
        self.exec_void(f'DROP TABLE {name};')

    def create_table(
            self,
            name: TableName,
            columns: Columns,
            not_null_primary_key: Optional[int] = None
    ):
        if (not_null_primary_key < 1) \
                or (not_null_primary_key > len(columns)):
            print("Wrong value for not_null_primary_key parameter")
            return
        lines_for_columns_query: List[str] = [
            f'{c_name} {c_type}'
            for c_name, c_type in columns.items()
        ]
        if not_null_primary_key:
            lines_for_columns_query[not_null_primary_key - 1] += ' NOT NULL'
            primary_key_column_name: str =\
                lines_for_columns_query[not_null_primary_key - 1].split(' ')[0]
            lines_for_columns_query.append(
                f'PRIMARY KEY ({primary_key_column_name})'
            )
        columns_query: str = ',\n'.join(lines_for_columns_query)
        self.exec_void(
            f'CREATE TABLE {name} ({columns_query});'
        )

    # ----------------------------- SPECIAL QUERIES ----------------------------
    def get_in_app_user_name_by_id(self, user_id: int) -> str:
        rows: List[tuple] = self.exec_select(
            f"SELECT name FROM users WHERE user_id = {user_id};"
        )
        return rows[0][0]

    def get_user_data_rows(
            self, user_id: int
    ) -> Tuple[Optional[str], Optional[int], Optional[str], bool]:
        raise NotImplementedError
        # rows: List[tuple] = self.exec_select(""
        #
        # )
        # return rows[0]


