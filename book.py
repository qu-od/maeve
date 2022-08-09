from typing import List, Dict, Tuple, Optional, Union, Any
import datetime


# ----------------------------- BOOK CLASS -------------------------------------
class Book:
    Title = str
    Author = Optional[str]
    ReadYear = Optional[int]
    Passion = Optional[int]
    BookArg = Union[Title, Author, ReadYear, Passion]

    def __init__(
            self, title: Title,
            author: Author = None,
            read_year: ReadYear = None,
            passion: Passion = None
    ):
        self.title: str = title
        self.author: Optional[str] = author
        self.read_year: Optional[int] = read_year
        self.passion: Optional[int] = passion

    def __str__(self):
        return (
            f'"{self.title}" ({self.author})."'
            + f" Read in {self.read_year}. P{self.passion}"
        )

    def str_ru(self):
        return (
            f'"{self.title}" ({self.author})."'
            + f" Прочитано в {self.read_year}. Ж{self.passion}"
        )

    # ----------------------- INPUT FORMATTING ---------------------------------
    @staticmethod
    def format(
        title: Title, author: Author,
        read_year: ReadYear, passion: Passion
    ) -> Tuple[Title, Author, ReadYear, Passion, bool, str]:
        format_matrix: List[Tuple[Any, bool, Optional[str]]] = [
            Book._format_title(title),
            Book._format_author(author),
            Book._format_read_year(read_year),
            Book._format_passion(passion),
        ]
        book_args: List[Any] =\
            [book_arg for book_arg, _, _ in format_matrix]
        was_args_right: bool =\
            all(was_arg_right for _, was_arg_right, _ in format_matrix)
        error_msg: str =\
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
        if len(author) > 300:
            return author[:300], False, "Author cropped"
        else:
            return author, True, None

    @staticmethod
    def _format_read_year(
            read_year: ReadYear
    ) -> Tuple[ReadYear, bool, Optional[str]]:
        if read_year > datetime.datetime.now().year:
            return None, False, "Year is bigger than the present year"
        elif read_year < 1900:
            return None, False, "Year value is too small"
        else:
            return read_year, True, None

    @staticmethod
    def _format_passion(
            passion: Passion
    ) -> Tuple[Passion, bool, Optional[str]]:
        if passion > 5:
            return None, False, "Passion value is too big"
        elif passion < 1:
            return None, False, "Passion value is too small"
        else:
            return passion, True, None

    # ------------------ DATABASE CRUD OPERATIONS ------------------------------
    def create(self):
        pass

    def read(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass


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
