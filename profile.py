from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass

import discord

from database import Database


# ------------------------------ TYPES -----------------------------------------
ProfileData = Tuple[
    Optional[str],
    Optional[int],
    Optional[str],
    bool
]


# ----------------------------- CLASSES ----------------------------------------
@dataclass()
class UserBookStats:
    books: int
    reviews: int


class UserProfile:
    db = Database()

    def __init__(self, user_id: int):
        self.user_id: int = user_id
        (
            self.name,
            self.start_guild_id,
            self.about_me,
            self.is_private
            ) = self._get_user_profile_data_row()
        self.user_book_stats: UserBookStats = self._get_user_book_stats()

    def _get_user_profile_data_row(self) -> ProfileData:
        return self.db.exec_select(
            "SELECT name, server_id, about_me, is_private"
            + f" FROM users WHERE user_id = {self.user_id}"
        )[0]

    def _get_user_book_stats(self) -> UserBookStats:
        user_name: str =\
            self.db.get_in_app_user_name_by_id(self.user_id)
        num_of_books: int = len(self.db.exec_select(
            f"SELECT title FROM books.{user_name}"
        ))
        num_of_reviews: int = len(self.db.exec_select(
            f"SELECT title FROM books.{user_name} WHERE review IS NOT NULL"
            # TODO query NEED TESTING
        ))
        return UserBookStats(books=num_of_books, reviews=num_of_reviews)
