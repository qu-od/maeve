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
from wheel import codify


# --------------------------- BOT CONFIG ---------------------------------------
"""
This example requires the 'members' privileged intent to use the Member converter
and the 'message_content' privileged intent for prefixed commands.
"""

description = """
An example bot to showcase the discord.ext.commands extension module.
There are a number of utility commands being showcased here.
"""

slash_command_guilds: List[int] = [
    693476909677412363,  # Maeve test server
    # 673968890325237771  # Bookish server (forbidden for now)
]

class Bot:
  db = None
  bot = None
  test_books = None

  def __init__(self):
    self.db = Database()

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    self.bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("!m "),
        description=description,
        intents=intents,
        debug_guilds=slash_command_guilds
    )
    self.test_books = BookList()

    bot.event(self.on_ready)
    bot.command(name='u', help='update bot modules')(self.update)
    bot.group()(self.book)
    book.command()(self.show)
    book.command()(self.add)
    book.command()(self.get)
    book.command()(self.update)
    book.command()(self.delete)
    bot.group()(self.test)
    test.command()(self.create_users_table)
    test.command()(self.write_me_to_users_table)
    test.command()(self.read_all_from_users_table)
    test.command()(self.delete_users_table)
    bot.slash_command(name='repeat')(self.repeat)
    bot.slash_command(
        name='start',
        description='create user profile'
    )(self.start)
    bot.slash_command(name='book')(self.book)

    load_bot_command_extensions()
    bot.run(os.getenv("MAEVE_TOKEN"))

  # ---------------------------- EVENT HANDLERS ----------------------------------
  async def on_ready(self):
      print(f"Logged in as {bot.user} (ID: {bot.user.id})")
      print("------")

  # ------------------------- GENERAL COMMANDS -----------------------------------
  async def update(self,ctx: commands.Context):
      try:
          reload_modules()
      except Exception:
          await ctx.send("Failed to reload non-command modules")
      try:
          reload_commands(bot)
      except Exception:
          await ctx.send("Failed to reload command modules")


  # ------------------------- BOOK COMMANDS --------------------------------------
  async def book(self, ctx: commands.Context):
      """
      checks if a subcommand is being invoked.
      """
      if ctx.invoked_subcommand is None:
          await ctx.send(f"Command {ctx.subcommand_passed} haven't been invoked")

  async def show(self, ctx: commands.Context):
      """Create book"""
      await ctx.send("BOOK LIST:\n" + str(test_books))

  async def add(self, ctx: commands.Context, title: str, author: str):
      """Create book"""
      test_books.add(Book(title, author))
      await ctx.send(f'book "{title}" of author "{author}" was added')

  async def get(self, ctx: commands.Context, book_id: int):
      """Read book"""
      book = test_books.get(book_id)
      await ctx.send("BOOK:\n" + str(book))

  async def update(self, ctx: commands.Context, book_id: int, title: str, author: str):
      """Update book"""
      old_book = test_books.get(book_id)
      test_books.update(book_id, Book(title, author))
      await ctx.send("OLD_BOOK:\n" + str(old_book) + "\nNEW_BOOK:\n" + str(book))

  async def delete(self, ctx: commands.Context, book_id: int):
      """Delete book"""
      book = test_books.get(book_id)
      test_books.delete(book_id)
      await ctx.send("DELETED_BOOK:\n" + str(book))


  # ------------------------ TEST COMMANDS ---------------------------------------
  async def test(self, ctx: commands.Context):
      """
      checks if a subcommand is being invoked.
      """
      if ctx.invoked_subcommand is None:
          await ctx.send(f"Command {ctx.subcommand_passed} haven't been invoked")

  async def create_users_table(self, ctx: commands.Context):
      columns: Columns = {
          "name": "varchar(100)",
          "user_sid": "varchar(100)",
          "is_public": "bool",
      }
      db.create_table("users", columns)
      await ctx.send("USERS TABLE CREATED")

  async def write_me_to_users_table(self, ctx: commands.Context):
      author_name: str = ctx.author.name
      author_id: str = str(ctx.author.id)
      db.exec_void(
          f'INSERT INTO users (name, user_sid, is_public)'
          + f" VALUES ('{author_name}', '{author_id}', FALSE);"
      )
      await ctx.send("USERS TABLE UPDATED")

  async def read_all_from_users_table(self, ctx: commands.Context):
      rows: List[tuple] = db.exec_select(
          # f'SELECT name, user_sid, is_public'
          f'SELECT *'
          + f' FROM users'
      )
      await ctx.send("USERS TABLE FETCHED. HERE ARE ALL OF ITS ROWS:")
      for i, row in enumerate(rows):
          await ctx.send(f'ROW {i}: {str(row)}')

  async def delete_users_table(self, ctx: commands.Context):
      db.delete_table("users")
      await ctx.send("USERS TABLE DELETED")


  """@bot.slash_command()
  async def test_slash_command_with_reply(ctx: commands.Context):
      await ctx.respond("Slash command worked")"""

  async def repeat(self, ctx: commands.Context, word: str, n: int):
      for _ in range(n):
          await ctx.send(word + "\n")

  async def start(self, ctx: commands.Context):
      db.exec_void(
          f'INSERT INTO users (name, user_id, server_id, is_private, privileges)'
          + " VALUES ('{name}', {uid}, {sid}, {is_private}, '{privileges}');".format(
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
      db.create_table("books." + str(ctx.author.id), columns)
      await ctx.send(
          f'Profile table for {ctx.author.mention} created'
      )

  async def book(
    self,
    ctx: commands.Context, title: str, author: str,
    read_year: int, passion: int
  ): 
      db.exec_void(
          f'INSERT INTO books.{ctx.author.id}'
          + ' (title, author, read_year, passion, review)'
          + f" VALUES ('{title}', '{author}', {read_year}, {passion}, NULL);"
      )

  # --------------------------- BOT SETUP ----------------------------------------
  def reload_modules(self):
      reload(self.database)
      reload(self.book)
      reload(self.wheel)


  def reload_commands(self):
      bot.reload_extension('book_cmds')
      bot.reload_extension('profile_cmds')
      bot.reload_extension('match_cmds')


  def load_bot_command_extensions(self):
      bot.load_extension('book_cmds')
      bot.load_extension('profile_cmds')
      bot.load_extension('match_cmds')

bot = Bot()
