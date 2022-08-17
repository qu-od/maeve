from typing import List, Dict, Tuple, Optional, Union, Any
import datetime
from dataclasses import dataclass

import discord

from database import Database
from wheel import fetch_member_in_guild_by_id


# --------------------- BOOK DATA DATACLASSES ----------------------------------
class BookData:
    def __init__(
        self, title: str,
        author: Optional[str] = None,
        read_year: Optional[int] = None,
        interest: Optional[int] = None,
        review: Optional[str] = None
    ):
        self.title: str = title
        self.author: Optional[str] = author
        self.read_year: Optional[int] = read_year
        self.interest: Optional[int] = interest
        self.review: Optional[str] = review

    def __str__(self):
        return (
            f'"{self.title}" ({self.author})."'
            + f" Read in {self.read_year}."
            + f" P{self.interest}. {self.cropped_review}..."
        )

    def str_ru(self):
        return (
            f'"{self.title}" ({self.author})."'
            + f" {self.read_year} г. и{self.interest}"
        )

    def cropped_review(self, review_len: Optional[int] = 100) -> str:
        return self.review[:review_len]


class BookDataStrict:  # just to speed up books user input one day
    def __init__(
        self, title: str,
        author: str, read_year: int,
        interest: int, review: str
    ):
        self.title: str = title
        self.author: str = author
        self.read_year: int = read_year
        self.interest: int = interest
        self.review: str = review


class UserBooks:
    def __init__(
        self, user: discord.User, books: List[BookData]
    ):
        self.user: discord.User = user
        self.books: List[BookData] = books


# ----------------------------- BOOK CLASS -------------------------------------
class Book:
    Title = str
    Author = Optional[str]
    ReadYear = Optional[int]
    Interest = Optional[int]
    AnyBookArg = Union[Title, Author, ReadYear, Interest]
    BookArgs = Tuple[Title, Author, ReadYear, Interest]
    # As you can see, BookArgs doesn't include review.
    # But BookData dataclass will do so.
    # TODO make BookData in a dataclass
    FormattingResults = Tuple[
        Title, Author,
        ReadYear, Interest,
        bool, Optional[str]
    ]

    db = Database()

    # INIT was there.

    # ----------------------- INPUT FORMATTING ---------------------------------
    @staticmethod
    def format(
        title: Title, author: Author,
        read_year: ReadYear, interest: Interest
    ) -> Tuple[Title, Author, ReadYear, Interest, bool, Optional[str]]:
        format_matrix: List[Tuple[Any, bool, Optional[str]]] = [
            Book._format_title(title),
            Book._format_author(author),
            Book._format_read_year(read_year),
            Book._format_interest(interest),
        ]
        book_args: List[Any] =\
            [book_arg for book_arg, _, _ in format_matrix]
        was_args_right: bool =\
            all(was_arg_right for _, was_arg_right, _ in format_matrix)
        error_msg: Optional[str] =\
            ".\n".join(msg for _, _, msg in format_matrix if msg)
        ans_list: list = book_args + [was_args_right] + [error_msg]
        return tuple(ans_list)

    @staticmethod
    def _format_title(
            title: Title
    ) -> Tuple[Title, bool, Optional[str]]:
        if not title:
            raise ValueError("Title can not be None")
        elif len(title) > 300:
            return title[:300], False, "Title cropped"
        else:
            return title, True, None

    @staticmethod
    def _format_author(
            author: Author
    ) -> Tuple[Author, bool, Optional[str]]:
        if author and (len(author) > 300):
            return author[:300], False, "Author cropped"
        else:
            return author, True, None

    @staticmethod
    def _format_read_year(
            read_year: ReadYear
    ) -> Tuple[ReadYear, bool, Optional[str]]:
        if read_year is None:
            return None, True, None
        elif read_year > datetime.datetime.now().year:
            return None, False, "Year is bigger than the present year"
        elif read_year < 1900:
            return None, False, "Year value is too small"
        else:
            return read_year, True, None

    @staticmethod
    def _format_interest(
            interest: Interest
    ) -> Tuple[Interest, bool, Optional[str]]:
        if interest is None:
            return None, True, None
        if interest > 3:
            return None, False, "Interest value is too big"
        elif interest < 1:
            return None, False, "Interest value is too small"
        else:
            return interest, True, None

    # ------------------ DATABASE CRUD OPERATIONS ------------------------------
    @staticmethod
    def create(user_id: int, *raw_book_args: BookArgs) -> Optional[str]:
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        formatting_results: Book.FormattingResults =\
            Book.format(*raw_book_args)
        book_args: Book.BookArgs = tuple(formatting_results[:4])
        is_succ, err_msg = formatting_results[4:]
        Book.db.exec_void(
            f'INSERT INTO books.{user_name}'
            + ' (title, author, read_year, interest, review)'
            + f" VALUES ('{book_args[0]}',"
            + f" {Book.opt_str(book_args[1])},"
            + f" {Book.opt_int(book_args[2])},"
            + f" {Book.opt_str(book_args[3])}, NULL);"
        )
        return err_msg if not is_succ else None

    @staticmethod
    def update(user_id: int, *raw_book_args: BookArgs) -> Optional[str]:
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        formatting_results: Book.FormattingResults = \
            Book.format(*raw_book_args)
        book_args: Book.BookArgs = tuple(formatting_results[:4])
        is_succ, err_msg = formatting_results[4:]
        Book.db.exec_void(
            f"UPDATE books.{user_name}"
            + f" SET author = {Book.opt_str(book_args[1])},"
            + f" read_year = {Book.opt_int(book_args[2])},"
            + f" interest = {Book.opt_int(book_args[3])}"
            + f" WHERE title = '{book_args[0]}';"
        )
        return err_msg if not is_succ else None

    @staticmethod
    def read(user_id: int, title: str) -> BookData:
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        book_rows: List[tuple] = Book.db.exec_select(
            "SELECT title, author, read_year, interest, review"
            + f" FROM books.{user_name} WHERE title = '{title}';"
        )
        return BookData(*book_rows[0])

    @staticmethod
    def read_all(user_id: int) -> List[BookData]:
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        book_rows: List[tuple] = Book.db.exec_select(
            "SELECT title, author, read_year, interest, review"
            + f" FROM books.{user_name};"
        )
        return [BookData(*book_row) for book_row in book_rows]

    @staticmethod
    def delete(user_id: int, title: str):
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        Book.db.exec_void(
            f"DELETE FROM books.{user_name} WHERE title = '{title}';"
        )

    @staticmethod
    def new_review(user_id: int, title: str, review: str):
        user_name: str = Book.db.get_in_app_user_name_by_id(user_id)
        Book.db.exec_void(
            f"UPDATE books.{user_name} SET review = '{review}'"
            + f"WHERE title = '{title}';"
        )

    # ---------------------------- FOR BOOKS_VIEW ------------------------------
    def get_public_user_booklists(
            self, bot_guilds: List[discord.Guild]
    ) -> List[UserBooks]:
        query_rows: List[tuple] = Book.db.exec_select(
            "SELECT user_id FROM users WHERE is_private = FALSE;"
        )
        ids_of_public_users: List[int] = [
            row_tuple[0] for row_tuple in query_rows
        ]
        public_users: Optional[List[discord.Member]] = []
        for user_id in ids_of_public_users:
            user = fetch_member_in_guild_by_id(bot_guilds, user_id)
            if not user:
                continue
            public_users.append(user)
        return [
            UserBooks(user, self.read_all(user.id))
            for user in public_users
        ]

    def get_user_books_by_user_name(
            self, bot_guilds: List[discord.Guild],
            user_name: str
    ) -> UserBooks:
        public_user_booklists: List[UserBooks] = \
            self.get_public_user_booklists(bot_guilds)
        for user_books in public_user_booklists:
            if user_books.user.name == user_name:
                return user_books

    # ------------------------------- MISC -------------------------------------
    @staticmethod
    def opt_str(maybe_str: Optional[str]) -> str:
        return f"'{maybe_str}'" if maybe_str else "NULL"

    @staticmethod
    def opt_int(maybe_int: Optional[int]) -> str:
        return str(maybe_int) if maybe_int else "NULL"


# --------------------------- BOOKLIST CLASS -----------------------------------
class BookList(dict):
    def __init__(self):
        self.books: Dict[int, Book] = {}

    def __str__(self):
        return "\n".join([
            "#" + str(book_id) + " " + str(book)
            for book_id, book in self.books.items()
        ])

    def _find_minimal_available_index(self):
        i = 0
        while True:
            if i not in self.books.keys():
                break
            i += 1
        return i

    def add(self, book: Book):
        i = self._find_minimal_available_index()
        self.books[i] = book

    def get(self, i: int):
        return self.books[i]

    def update(self, i: int, new_book: Book):
        self.books[i] = new_book

    def delete(self, i: int):
        self.books.pop(i)
