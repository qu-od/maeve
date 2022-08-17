from typing import List, Dict, Callable, Optional
import asyncio

import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands, pages

from book import BookData, UserBooks, Book
from wheel import (
    grouper, book_numeral,
)


class BooksPageEmbed:
    def __init__(
        self,
        user_books: UserBooks,
        num_of_books_on_page: int = 5,  # TODO figure out optimal value
        current_page: int = 1,  # remove from init maybe?
        book_in_focus: int = 1,  # remove from init maybe?
    ):
        self.user_books: UserBooks = user_books
        self.num_of_books_on_page: int = num_of_books_on_page
        self.num_of_pages: Optional[int] = \
            (len(self.user_books.books) // self.num_of_books_on_page) + 1
        self._current_page: int = current_page
        self._book_in_focus: int = book_in_focus
        # do not save public_user_books state cuz it might change anytime
        # always retrieve public_user_books when page is changed

    @property
    def current_page(self):
        """current_page property docstring"""
        return self._current_page

    @current_page.setter
    def current_page(self, new_page: int):
        if new_page < 1:
            self._current_page = self.num_of_pages
        elif new_page > self.num_of_pages:
            self._current_page = 1
        else:
            self._current_page = new_page

    @current_page.deleter
    def current_page(self):
        del self._current_page

    @property
    def book_in_focus(self):
        """book_in_focus property docstring"""
        return self._book_in_focus

    @book_in_focus.setter
    def book_in_focus(self, new_focus: int):
        if new_focus < 1:
            self._book_in_focus = self.num_of_books_on_page
        elif new_focus > self.num_of_books_on_page:
            self._book_in_focus = 1
        else:
            self._book_in_focus = new_focus

    @book_in_focus.deleter
    def book_in_focus(self):
        del self._book_in_focus

    def make_embed(self) -> discord.Embed:
        paginated_booklist: List[List[BookData]] = \
            list(grouper(self.user_books.books, self.num_of_books_on_page, fillvalue=None))
        page_of_booklist: List[BookData] = \
            paginated_booklist[self._current_page - 1]
        return self._embed_page_from_booklist_page(
            self.user_books.user, page_of_booklist
        )

    def _embed_page_from_booklist_page(
            self,
            user: discord.User,
            page_of_users_books: List[BookData],
            showed_review_len: int = 100
    ) -> discord.Embed:
        embed = discord.Embed(
            title=user.name,
            colour=discord.Colour.brand_green()
        )
        embed.set_thumbnail(url=user.avatar.url)
        for i, book in enumerate(page_of_users_books):
            if not book:
                embed.add_field(name="***", value="***", inline=False)
                continue
            in_focus: bool = (self._book_in_focus - 1) == i
            embed_value: str = (
                    self._showed_author(book.author)
                    + self._showed_read_year(book.read_year)
                    + self._showed_interest(book.interest)
                    + self._showed_review(book.review, showed_review_len)
                )
            embed.add_field(
                name=self._showed_title(book.title, in_focus),
                value=embed_value if embed_value else "***",
                inline=False
            )
        return embed

    @staticmethod
    def _showed_title(title: str, in_focus: bool) -> str:
        if in_focus:
            return f"**->>> {title} <<<-**"
        else:
            return title

    @staticmethod
    def _showed_author(author: Optional[str]) -> str:
        if not author:
            return ''
        return author

    @staticmethod
    def _showed_read_year(read_year: Optional[int]) -> str:
        if not read_year:
            return ''
        return f" {read_year} г."

    @staticmethod
    def _showed_interest(interest: Optional[int]) -> str:
        if not interest:
            return ''
        return " " + "📡" * interest

    @staticmethod
    def _showed_review(
            review: Optional[str],
            showed_review_len: int
    ) -> str:
        if not review:
            return ''
        if len(review) > showed_review_len:
            return " " + review[:showed_review_len] + "..."
        else:
            return " " + review


class SimpleButton(discord.ui.Button):
    def __init__(
            self, button_name: str, style: discord.ButtonStyle,
            books_page_embed: BooksPageEmbed

    ):
        self.label_dict: Dict[str, str] = {
            "left":  "⬅️",
            "right": "➡️",
            "up":    "⬆️",
            "down":  "⬇️",
            "get_review": "см. отзыв"
        }
        self.books_page_embed: BooksPageEmbed = books_page_embed
        super().__init__(
            label=self.label_dict[button_name],
            style=style
        )

    async def callback(self, interaction: discord.Interaction):
        # TODO use proper setters to set current_page and book_in_focus
        if self.label == self.label_dict["left"]:
            self.books_page_embed.current_page -= 1
        if self.label == self.label_dict["right"]:
            self.books_page_embed.current_page += 1
        if self.label == self.label_dict["up"]:
            self.books_page_embed.book_in_focus -= 1
        if self.label == self.label_dict["down"]:
            self.books_page_embed.book_in_focus += 1
        if self.label == self.label_dict["get_review"]:
            # TODO implement callback for get_review
            raise NotImplementedError
        new_embed = self.books_page_embed.make_embed()
        await interaction.message.edit(embed=new_embed)


class UsersDropdown(discord.ui.Select):
    def __init__(
            self, bot: discord.Bot,
    ):
        self.bot = bot
        options: List[discord.SelectOption] = [
            discord.SelectOption(
                label=user_books.user.name,
                description=book_numeral(len(user_books.books)),
                emoji="⚪"
            )
            for user_books in Book().get_public_user_booklists(self.bot.guilds)
        ]
        super().__init__(
            placeholder="выберите участника...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        next_user_name: str = self.values[0]
        # retrieve the latest state of books for a user
        user_books: UserBooks = \
            Book().get_user_books_by_user_name(
                self.bot.guilds, next_user_name
            )
        new_embed: discord.Embed = \
            BooksPageEmbed(user_books).make_embed()
        await interaction.message.edit(embed=new_embed)


class BooksView(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.books_page_embed: Optional[BooksPageEmbed] = None
        # somehow it can't retrieve users on Cag init
        self.test_embed: discord.Embed()\
            = discord.Embed(title="test embed")

    @commands.slash_command(
        name='книжки',
        description='Что читали другие участники'
    )
    async def create_book_view(self, ctx: discord.ApplicationContext):
        view = discord.ui.View(timeout=None)
        # TODO change timeout value to 60 secs
        any_user_books: UserBooks = (
            Book().get_public_user_booklists(self.bot.guilds)[0]
        )
        self.books_page_embed = BooksPageEmbed(any_user_books)
        view.add_item(SimpleButton(
            "left",
            discord.ButtonStyle.primary,
            self.books_page_embed,
        ))
        view.add_item(SimpleButton(
            "up",
            discord.ButtonStyle.primary,
            self.books_page_embed,
        ))
        view.add_item(SimpleButton(
            "get_review",
            discord.ButtonStyle.green,
            self.books_page_embed,
        ))
        view.add_item(SimpleButton(
            "down",
            discord.ButtonStyle.primary,
            self.books_page_embed,
        ))
        view.add_item(SimpleButton(
            "right",
            discord.ButtonStyle.primary,
            self.books_page_embed,
        ))
        view.add_item(UsersDropdown(self.bot))
        await ctx.respond(
            embed=self.books_page_embed.make_embed(),
            view=view
        )


def setup(bot):
    bot.add_cog(BooksView(bot))

