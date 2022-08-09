from typing import List, Tuple, Optional
import os
from importlib import reload

import discord
from discord.ext import commands

import database
from database import Database, Columns
import book
from book import Book, BookList
import wheel
from wheel import form_in_app_user_name


# --------------------------- BOT CONFIG ---------------------------------------
"""
This example requires the 'members' privileged intent to use 
the Member converter
and the 'message_content' privileged intent
for prefixed commands.
"""

description = """
An example bot to showcase the discord.ext.commands extension module.
There are a number of utility commands being showcased here.
"""

slash_command_guilds: List[int] = [
    693476909677412363,  # Maeve test server
    # 673968890325237771  # Bookish server (forbidden for now)
]


class MaeveBot:
    bot = None
    db = None
    test_books = None

    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.members = True
        self.intents.message_content = True
        self.bot = commands.Bot(
            command_prefix=commands.when_mentioned_or("!m "),
            description=description,
            intents=self.intents,
            # comment debug_guilds to enable slash commands globally
            # debug_guilds=slash_command_guilds
        )
        self.db = Database()
        self.test_books = BookList()

        # ----- register events
        self.bot.event(self.on_ready)

        # ----- register prefix commands
        self.bot.command(
            name='_reload',
            help='reload bot modules'
        )(self._reload)

        # ----- register slash commands
        # TODO make groups out of slash commands without decorators
        self.bot.slash_command(
            name='start',
            description='Создать профиль.'
        )(self.start)

        self.bot.slash_command(
            name='book',
            description='Добавить книгу.'
        )(self.book)

        self.bot.slash_command(
            name='delete_profile',
            description='Удалить профиль и всё книги.'
        )(self.delete_profile)

        self.bot.slash_command(
            name='delete',
            description='Удалить запись о книге.'
        )(self.delete)

        self.bot.slash_command(
            name='update',
            description='Редактировать запись о книге.'
        )(self.update)

        self.bot.slash_command(
            name='show_plain_text',
            description='Запросить сообщение со списком книг.'
        )(self.show_plain_text)

        self.bot.slash_command(
            name='show',
            description='Запросить тетрадку со списком книг.'
        )(self.show)

        self.bot.slash_command(
            name='review',
            description='Добавить рецензию на книгу.'
        )(self.review)

        self.load_bot_command_extensions()
        self.bot.run(os.getenv("MAEVE_TOKEN"))

    # ---------------------------- EVENT HANDLERS ------------------------------
    async def on_ready(self):
        print(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        print("------")

    # ------------------------- ADMIN COMMANDS --------------------------------
    async def _reload(self, ctx: commands.Context):
        if not self.is_admin(ctx.author.id):
            return  # silently
        try:
            self.reload_modules()
        except Exception:
            await ctx.send("Failed to reload non-command modules")
            return
        try:
            self.reload_commands()
        except Exception:
            await ctx.send("Failed to reload command modules")
            return
        await ctx.send("Modules and commands was reloaded successfully!")

    # ------------------------- USER COMMANDS ---------------------------------
    async def start(self, ctx: commands.Context):
        if self.is_user_registered(ctx.author.id):
            await ctx.send(f"User {ctx.author.mention} already registered!")
            return
        await ctx.send(f"New user {ctx.author.mention} detected. Hello!")
        in_app_user_name: str = form_in_app_user_name(ctx.author)
        self.db.exec_void(
            "INSERT INTO users"
            + " (name, user_id, server_id, is_private, is_admin)"
            + " VALUES"
            + " ('{name}', {uid}, {sid}, {is_private}, {is_admin});".format(
                name=in_app_user_name,
                uid=ctx.author.id,
                sid=(ctx.guild.id if ctx.guild else "NULL"),
                is_private=False,
                is_admin=False,
            )
        )
        await ctx.send(f'User {ctx.author.mention} registered in users')
        columns: Columns = {
            'title':     'varchar(300)',
            # every other column may contain NULLs
            'author':    'varchar(300)',
            'read_year': 'integer',
            'passion':   'smallint',
            'review':    'text',
        }
        self.db.create_table(
            f'books.{in_app_user_name}',
            columns,
            not_null_primary_key=1
        )
        await ctx.send(
            f'Books table for {ctx.author.mention} created'
        )

    async def book(
            self, ctx: commands.Context,
            title: str, author: str,
            read_year: int, passion: int
    ):
        user_name: str = self.db.get_in_app_user_name_by_id(ctx.author.id)
        formatting_results: Tuple[
                Book.Title, Book.Author,
                Book.ReadYear, Book.Passion,
                bool, Optional[str]] = \
            Book.format(title, author, read_year, passion)
        new_book = Book(*formatting_results[:4])
        # TODO new_book.add()
        # TODO make None -> NULL conversion
        self.db.exec_void(
            f'INSERT INTO books.{user_name}'
            + ' (title, author, read_year, passion, review)'
            + f" VALUES ('{new_book.title}', '{new_book.author}',"
            + f" {new_book.read_year}, {new_book.passion}, NULL);"
        )
        await ctx.send(
            "You've added the book, "
            + ctx.author.mention + " !"
        )
        if not formatting_results[4]:
            await ctx.send(
                "However format was wrong:\n"
                + formatting_results[5]
            )

    async def delete_profile(self, ctx: commands.Context):
        if not self.is_user_registered(ctx.author.id):
            await ctx.send(
                "You must register first to be able to delete your profile."
            )
            return
        # TODO output book table to the user packed in files before deleting
        user_name: str = self.app_user_name(ctx.author.id)
        self.db.delete_table("books." + user_name)
        await ctx.send("Books table deleted.")
        self.db.exec_void(
            f"DELETE FROM users WHERE user_id = {ctx.author.id}"
        )
        await ctx.send(f"{ctx.author.mention} deleted from users.")

    async def delete(self, ctx: commands.Context, title: str):
        # TODO choose books by id not a title (add id column to books tables)
        self.db.exec_void(
            f"DELETE FROM {self.user_book_table_name(ctx.author.id)}"
            + f" WHERE title = '{title}';"
        )
        await ctx.send(f'Book "{title}" deleted.')

    async def update(  # review updated separately with "/review"
            self, ctx: commands.Context,
            title: str, author: str,
            read_year: int, passion: int
            ):
        # TODO choose books by id not a title (add id column to books tables)
        table_name: str = self.user_book_table_name(ctx.author.id)
        self.db.update_book(table_name, title, author, read_year, passion)
        await ctx.send(f'Book "{title}" updated.')

    async def show_plain_text(self, ctx: commands.Context):
        # reviews aren't shown there in any way
        table_name: str = self.user_book_table_name(ctx.author.id)
        book_rows: List[tuple] = self.db.exec_select(
            f"SELECT title, author, read_year, passion FROM {table_name}"
        )
        await ctx.send(",\n".join(list(map(self.book_row_to_str, book_rows))))

    async def show(self, ctx: commands.Context):
        pass

    async def review(self, ctx: commands.Context):
        pass

    # ---------------------------- MISC ----------------------------------------
    def app_user_name(self, user_id: int) -> str:
        return self.db.get_in_app_user_name_by_id(user_id)

    def user_book_table_name(self, user_id: int) -> str:
        return "books." + self.app_user_name(user_id)

    @staticmethod
    def book_row_to_str(book_row: Tuple[str, str, int, int]) -> str:
        title, author, read_year, passion = book_row
        return f'"{title}" - {author}. Read in {read_year}. Passion = {passion}'

    def is_user_registered(self, user_id: int) -> bool:
        user_rows: List[tuple] = self.db.exec_select(
            f"SELECT name FROM users WHERE user_id = {user_id};"
        )
        return bool(user_rows)

    def is_admin(self, user_id: int) -> bool:
        user_rows: List[tuple] = self.db.exec_select(
            f"SELECT is_admin FROM users WHERE user_id = {user_id};"
        )
        return user_rows and user_rows[0][0]

    # ---------------------------- LOADS ---------------------------------------
    def load_bot_command_extensions(self):
        self.bot.load_extension('book_cmds')
        self.bot.load_extension('profile_cmds')
        self.bot.load_extension('match_cmds')
        # self.bot.load_extension('booklist_pages')

    # --------------------------- RELOADS --------------------------------------
    @staticmethod
    def reload_modules():
        reload(database)
        reload(book)
        reload(wheel)

    def reload_commands(self):
        self.bot.reload_extension('book_cmds')
        self.bot.reload_extension('profile_cmds')
        self.bot.reload_extension('match_cmds')
        # self.bot.load_extension('booklist_pages')


# TODO: better user errors and feedback on command execution
# TODO: remove globals (into classes) and divide commands into modules
# TODO: add admin-only check on admin commands

# TODO: delete profile (and books table)
# TODO: show all his books to user. Using pagination
# TODO: delete one book
# TODO: update one book
# TODO: add review to the book

# TODO: sharing the booklist
# TODO: finding book intersections
# TODO: book title standardization (standard_input_format + variation rules)
# TODO: scraping message history of FB guild for book mentions
# TODO: Collecting book mentions and reviews from FB guild

# TODO: translate command names and arguments
# TODO: remove that "app is not responding marker somehow"
# TODO: test unpredictable user behavior (ask testers for help)
# TODO: make a RESTFUL API for Maeve database (ask somebody for a frontend)


if __name__ == "__main__":
    bot = MaeveBot()
