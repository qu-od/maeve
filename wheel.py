from typing import Iterable, Any, Optional, List, Literal
from itertools import zip_longest
import asyncio

import discord

def codify(msg: str) -> str:
    return f'```{msg}```'


def alphanums_to_lower(raw_str: str) -> str:
    return "".join(list(filter(
        lambda c: c.isalnum(), [c for c in raw_str]
    ))).lower()


def form_in_app_user_name(member: discord.member) -> str:
    return (
        alphanums_to_lower(member.name)[:10]
        + "_" + member.discriminator
    )


def grouper(iterable: Iterable, n, fillvalue: Any = None) -> Iterable:
    """Collect data into non-overlapping fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, fillvalue=x) --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def fetch_member_in_guild_by_id(
        bot_guilds: List[discord.Guild], user_id: int
) -> Optional[discord.Member]:
    user: Optional[discord.Member] = None
    for guild in bot_guilds:
        try:
            user = guild.get_member(user_id)
        except discord.Forbidden:
            continue
        except discord.HTTPException:
            continue
    return user


def book_noun_by_numeral(
        num_of_books: int) -> Literal["книга", "книги", "книг"]:
    last_digit: int = num_of_books % 10
    if last_digit == 1:
        return "книга"
    elif last_digit in [2, 3, 4]:
        return "книги"
    else:
        return "книг"


def book_numeral(num_of_books: int) -> str:
    last_digit: int = num_of_books % 10
    num: str = str(num_of_books)
    if last_digit == 1:
        return num + " книга"
    elif last_digit in [2, 3, 4]:
        return num + " книги"
    else:
        return num + " книг"
