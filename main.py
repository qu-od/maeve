from typing import List
import os
from importlib import reload

import discord
from discord.ext import commands

import database
from database import Database, Columns
import book
from book import BookList
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
            debug_guilds=slash_command_guilds
        )
        self.db = Database()
        self.test_books = BookList()

        # ----- register events
        self.bot.event(self.on_ready)

        # ----- register old-style commands
        self.bot.command(
            name='_reload',
            help='reload bot modules'
        )(self._reload)

        # ----- register slash commands
        # TODO make groups out of slash commands without decorators
        self.bot.slash_command(
            name='old_start',
            description='create user profile'
        )(self.old_start)

        self.bot.slash_command(
            name='old_book'
        )(self.old_book)

        self.bot.slash_command(
            name='start',
            description='create user profile'
        )(self.start)

        self.bot.slash_command(
            name='book'
        )(self.book)

        self.bot.slash_command(
            name='delete_profile',
            description=('deletes your entire book profile.'
                         + 'All matches, booklists and reviews'
                         )
        )(self.delete_profile)

        self.bot.slash_command(
            name='delete',
            description='Show your booklist in paginator'
        )(self.delete)

        self.bot.slash_command(
            name='update',
            description='Show your booklist in paginator'
        )(self.update)

        self.bot.slash_command(
            name='show',
            description='Show your booklist in paginator'
        )(self.show)

        self.bot.slash_command(
            name='review',
            description='Show your booklist in paginator'
        )(self.review)

        self.load_bot_command_extensions()
        self.bot.run(os.getenv("MAEVE_TOKEN"))

    # ---------------------------- EVENT HANDLERS ------------------------------
    async def on_ready(self):
        print(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        print("------")

    # ------------------------- ADMIN COMMANDS --------------------------------
    async def _reload(self, ctx: commands.Context):
        try:
            self.reload_modules()
        except Exception:
            await ctx.send("Failed to reload non-command modules")
        try:
            self.reload_commands()
        except Exception:
            await ctx.send("Failed to reload command modules")

    # ------------------------- USER COMMANDS ---------------------------------
    async def old_start(self, ctx: commands.Context):
        self.db.exec_void(
            'INSERT INTO users'
            + ' (name, user_id, server_id, is_private, privileges)'
            + " VALUES"
            + " ('{name}', {uid}, {sid}, {is_private}, '{privileges}');".format(
                name=ctx.author.name,
                uid=ctx.author.id,
                sid=(ctx.guild.id if ctx.guild else "NULL"),
                is_private=False,
                privileges=[]
            )
        )
        await ctx.send(f'User {ctx.author.mention} registered')
        columns: Columns = {
            'title':     'varchar(300)',
            # every other column may contain NULLs
            'author':    'varchar(300)',
            'read_year': 'integer',
            'passion':   'smallint',
            'review':    'text',
        }
        self.db.create_table("books." + str(ctx.author.id), columns)
        await ctx.send(
            f'Profile table for {ctx.author.mention} created'
        )

    async def old_book(
      self,
      ctx: commands.Context, title: str, author: str,
      read_year: int, passion: int
    ):
        self.db.exec_void(
            f'INSERT INTO books.{ctx.author.id}'
            + ' (title, author, read_year, passion, review)'
            + f" VALUES ('{title}', '{author}', {read_year}, {passion}, NULL);"
        )

    async def start(self, ctx: commands.Context):
        # TODO: Lookup users by id. Return error if user is already registered.
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
        user_name: str = self.db.get_user_name_by_id(ctx.author.id)
        self.db.exec_void(
            f'INSERT INTO books.{user_name}'
            + ' (title, author, read_year, passion, review)'
            + f" VALUES ('{title}', '{author}', {read_year}, {passion}, NULL);"
        )
        await ctx.send(
            "You've added the book, "
            + ctx.author.mention + " !"
        )

    async def delete_profile(self, ctx: commands.Context):
        pass

    async def delete(self, ctx: commands.Context):
        pass

    async def update(self, ctx: commands.Context):
        pass

    async def show(self, ctx: commands.Context):
        pass

    async def review(self, ctx: commands.Context):
        pass

    # ---------------------------- LOADS --------------------------------------
    def load_bot_command_extensions(self):
        self.bot.load_extension('book_cmds')
        self.bot.load_extension('profile_cmds')
        self.bot.load_extension('match_cmds')

    # --------------------------- RELOADS --------------------------------------
    def reload_modules(self):
        reload(database)
        reload(book)
        reload(wheel)

    def reload_commands(self):
        self.bot.reload_extension('book_cmds')
        self.bot.reload_extension('profile_cmds')
        self.bot.reload_extension('match_cmds')


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

# --------------------------- BOT SETUP ----------------------------------------
'''def reload_modules():
    reload(database)
    reload(book)
    reload(wheel)


def reload_commands():
    bot.reload_extension('book_cmds')
    bot.reload_extension('profile_cmds')
    bot.reload_extension('match_cmds')


def load_bot_command_extensions():
    bot.load_extension('book_cmds')
    bot.load_extension('profile_cmds')
    bot.load_extension('match_cmds')


load_bot_command_extensions()
bot.run(os.getenv("MAEVE_TOKEN"))
'''


if __name__ == "__main__":
    bot = MaeveBot()
