from typing import List, Dict, Tuple, Union


class Book:
    def __init__(self, title: str, author: str):
        self.title: str = title
        self.author: str = author

    def __str__(self):
        return f'"{self.title}" ({self.author})'


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
