from typing import List
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
This example requires the 'members' privileged intent to use the Member converter
and the 'message_content' privileged intent for prefixed commands.
"""

description = """
An example bot to showcase the discord.ext.commands extension module.
There are a number of utility commands being showcased here.
"""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

slash_command_guilds: List[int] = [
    693476909677412363,  # Maeve test server
    # 673968890325237771  # Bookish server (forbidden for now)
]

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!m "),
    description=description,
    intents=intents,
    debug_guilds=slash_command_guilds
)
test_books = BookList()
db = Database()


# ---------------------------- EVENT HANDLERS ----------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


# ------------------------- EXAMPLE COMMAND GROUP ------------------------------
'''@bot.command()
async def roll(ctx: commands.Context, dice: str):
    """Rolls a die in NdN format."""
    try:
        rolls, limit = map(int, dice.split("d"))
    except ValueError:
        await ctx.send("Format has to be in NdN!")
        return

    # _ is used in the generation of our result as we don't need the number that comes from the usage of range(rolls).
    result = ", ".join(str(random.randint(1, limit)) for _ in range(rolls))
    await ctx.send(result)


@bot.command(description="For when you wanna settle the score some other way")
async def choose(ctx: commands.Context, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))


@bot.command()
async def repeat(ctx: commands.Context, times: int, *, content: str = "repeating..."):
    """Repeats a message multiple times."""
    for _ in range(times):
        await ctx.send(content)


@bot.command()
async def joined(ctx: commands.Context, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f"{member.name} joined in {member.joined_at}")


@bot.slash_command()
async def my_fancy_hello(ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"Hello {name}!")
'''


# ------------------------- GENERAL COMMANDS -----------------------------------
@bot.command(name='u', help='update bot modules')
async def update(ctx: commands.Context):
    try:
        reload_modules()
    except Exception:
        await ctx.send("Failed to reload non-command modules")
    try:
        reload_commands(bot)
    except Exception:
        await ctx.send("Failed to reload command modules")


# ------------------------- BOOK COMMANDS --------------------------------------
@bot.group()
async def book(ctx: commands.Context):
    """
    checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f"Command {ctx.subcommand_passed} haven't been invoked")


@book.command()
async def show(ctx: commands.Context):
    """Create book"""
    await ctx.send("BOOK LIST:\n" + str(test_books))


@book.command()
async def add(ctx: commands.Context, title: str, author: str):
    """Create book"""
    test_books.add(Book(title, author))
    await ctx.send(f'book "{title}" of author "{author}" was added')


@book.command()
async def get(ctx: commands.Context, book_id: int):
    """Read book"""
    book = test_books.get(book_id)
    await ctx.send("BOOK:\n" + str(book))


@book.command()
async def update(ctx: commands.Context, book_id: int, title: str, author: str):
    """Update book"""
    old_book = test_books.get(book_id)
    test_books.update(book_id, Book(title, author))
    await ctx.send("OLD_BOOK:\n" + str(old_book) + "\nNEW_BOOK:\n" + str(book))


@book.command()
async def delete(ctx: commands.Context, book_id: int):
    """Delete book"""
    book = test_books.get(book_id)
    test_books.delete(book_id)
    await ctx.send("DELETED_BOOK:\n" + str(book))


# ------------------------ TEST COMMANDS ---------------------------------------
@bot.group()
async def test(ctx: commands.Context):
    """
    checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f"Command {ctx.subcommand_passed} haven't been invoked")


@test.command()
async def create_users_table(ctx: commands.Context):
    columns: Columns = {
        "name": "varchar(100)",
        "user_sid": "varchar(100)",
        "is_public": "bool",
    }
    db.create_table("users", columns)
    await ctx.send("USERS TABLE CREATED")


@test.command()
async def write_me_to_users_table(ctx: commands.Context):
    author_name: str = ctx.author.name
    author_id: str = str(ctx.author.id)
    db.exec_void(
        f'INSERT INTO users (name, user_sid, is_public)'
        + f" VALUES ('{author_name}', '{author_id}', FALSE);"
    )
    await ctx.send("USERS TABLE UPDATED")


@test.command()
async def read_all_from_users_table(ctx: commands.Context):
    rows: List[tuple] = db.exec_select(
        # f'SELECT name, user_sid, is_public'
        f'SELECT *'
        + f' FROM users'
    )
    await ctx.send("USERS TABLE FETCHED. HERE ARE ALL OF ITS ROWS:")
    for i, row in enumerate(rows):
        await ctx.send(f'ROW {i}: {str(row)}')


@test.command()
async def delete_users_table(ctx: commands.Context):
    db.delete_table("users")
    await ctx.send("USERS TABLE DELETED")


"""@bot.slash_command()
async def test_slash_command_with_reply(ctx: commands.Context):
    await ctx.respond("Slash command worked")"""


@bot.slash_command(name='repeat')
async def repeat(ctx: commands.Context, word: str, n: int):
    for _ in range(n):
        await ctx.send(word + "\n")


@bot.slash_command(
    name='start',
    description='create user profile'
)
async def start(ctx: commands.Context):
    # TODO: Lookup users by id. Return an error if user is already registered.
    in_app_user_name: str = form_in_app_user_name(ctx.author)
    db.exec_void(
        f'INSERT INTO users (name, user_id, server_id, is_private, is_admin)'
        + " VALUES ('{name}', {uid}, {sid}, {is_private}, {is_admin});".format(
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
    db.create_table(
        f'books.{in_app_user_name}',
        columns,
        not_null_primary_key=1
    )
    await ctx.send(
        f'Books table for {ctx.author.mention} created'
    )


@bot.slash_command(name='book')
async def book(
        ctx: commands.Context, title: str, author: str,
        read_year: int, passion: int
): 
    db.exec_void(
        f'INSERT INTO books.{ctx.author.id}'
        + ' (title, author, read_year, passion, review)'
        + f" VALUES ('{title}', '{author}', {read_year}, {passion}, NULL);"
    )


# --------------------------- BOT SETUP ----------------------------------------
def reload_modules():
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


