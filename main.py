from typing import List, Tuple, Optional
import os
from importlib import reload

import discord
from discord.ext import commands

import database
from database import Database, Columns
import book
from book import Book, BookList, BookData, BookDataStrict
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


# ----------------------- CUSTOM CONVERTER CLASSES -----------------------------
class BookDataStrictConverter(commands.Converter):
    async def convert(
            self, ctx: commands.Context, argument: str
    ) -> BookDataStrict:
        return BookDataStrict(
            "title_from_converter",
            "author_from_converter",
            1970, 5,
            "review_from_converter"
        )


# ------------------------- MY BOT CLASS ---------------------------------------
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
            # slash commands will take up to an hour to update then
            debug_guilds=slash_command_guilds
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
            'interest':   'smallint',
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

    '''
    async def book_with_auto_convo(  # TODO NEED TESTING
            self, ctx: commands.Context,
            book_data_strict: BookDataStrictConverter
    ):
        await ctx.send(str(book_data_strict))
        await ctx.send("book_with_auto_convo worked")
    '''

    async def book(
            self, ctx: commands.Context,
            title: Book.Title,
            author: Book.Author,  # TODO TEST NONE POSSIBILITY ON USER SIDE
            read_year: Book.ReadYear,
            interest: Book.Interest
    ):
        wrong_format_msg: Optional[str] =\
            Book.create(
                ctx.author.id,
                title, author,
                read_year, interest
            )
        await ctx.send(
            "You've added the book, "
            + ctx.author.mention + " !"
        )
        if wrong_format_msg:
            await ctx.send(
                "However format was wrong:\n"
                + wrong_format_msg
            )

    async def update(  # review updated separately with "/review"
            self, ctx: commands.Context,
            title: str, author: str,
            read_year: int, interest: int
            ):
        # TODO choose books by id not a title (add id column to books tables)
        Book.update(
            ctx.author.id, title,
            author, read_year, interest
        )
        await ctx.send(f'Book "{title}" updated.')

    async def show_plain_text(self, ctx: commands.Context):
        book_data_list: List[BookData] = Book.read_all(ctx.author.id)
        await ctx.send(
            ",\n".join(book_data.str_ru() for book_data in book_data_list)
        )

    async def show(self, ctx: commands.Context, test_string):
        await ctx.send("show command worked")

    async def delete(self, ctx: commands.Context, title: str):
        # TODO choose books by id not a title (add id column to books tables)
        Book.delete(ctx.author.id, title)
        await ctx.send(f'Book "{title}" deleted.')

    async def review(
            self, ctx: commands.Context,
            title: str, review: str):
        Book.new_review(ctx.author.id, title, review)
        await ctx.send(f'Review added to "{title}" book')

    # ---------------------------- MISC ----------------------------------------
    def app_user_name(self, user_id: int) -> str:
        return self.db.get_in_app_user_name_by_id(user_id)

    def user_book_table_name(self, user_id: int) -> str:
        return "books." + self.app_user_name(user_id)

    @staticmethod
    def book_row_to_str(book_row: Tuple[str, str, int, int]) -> str:
        title, author, read_year, interest = book_row
        return f'"{title}" - {author}. Read in {read_year}. Interest = {interest}'

    @staticmethod
    def book_row_to_str_ru(book_row: Tuple[str, str, int, int]) -> str:
        title, author, read_year, interest = book_row
        return f'"{title}" - {author}. {read_year} г. и{interest}'

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
# TODO: divide commands into modules

# TODO: implement Paginator (with buttons) to show all books
# TODO: check if book in books when updating one

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
