from typing import List, Tuple, Dict, Optional

import discord
from discord.ext import commands

from profile import UserProfile


class UserProfileEmbed:
    def __init__(
            self, user: discord.User,
            user_profile: UserProfile,
            user_start_guild_name: str
    ):
        self.user: discord.User = user
        self.user_profile: UserProfile = user_profile
        self.start_guild_name: str = user_start_guild_name
        self.user_discord_name: str = user.name

    def form(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.user.name}#{self.user.discriminator}",
            description="С сервера " + self.start_guild_name,
            colour=discord.Colour.brand_green(),
        )
        embed.set_thumbnail(url=self.user.avatar.url)
        embed.add_field(
            name="О себе:",
            value=self.user_profile.about_me or "Нет информации",
            inline=False
        )
        embed.add_field(
            name="Открыт ли профиль:",
            value="Да" if self.user_profile.is_public else "Нет",
            inline=False
        )
        embed.add_field(
            name="Книжек:",
            value=self.user_profile.user_book_stats.books,
            inline=True
        )
        embed.add_field(
            name="Отзывов:",
            value=self.user_profile.user_book_stats.reviews,
            inline=True
        )
        return embed


class ProfileView(discord.ui.View):
    @staticmethod
    def empty_embed(title: str) -> discord.Embed():
        return discord.Embed(title=title)

    @discord.ui.button(
        label='Изменить раздел "о себе"',
        style=discord.ButtonStyle.green,
        row=0
    )
    async def update_about_me(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.empty_embed('invoke "/о себе" command')
        )

    @discord.ui.button(
        label='Изменить приватность',
        style=discord.ButtonStyle.gray,
        row=1
    )
    async def toggle_is_private(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.empty_embed('update is_private in user row and reform embed')
        )


    @discord.ui.button(
        label="Помощь",
        style=discord.ButtonStyle.blurple,
        row=2
    )
    async def get_help_message(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.empty_embed('send help message to user in dm')
        )



    @discord.ui.button(
        label="Позвать модера",
        style=discord.ButtonStyle.blurple,
        row=2
    )
    async def call_moderator(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.empty_embed("invoke /call dev command which sends"
                                   + " message from a user to a dev's dm")
        )


class ProfileViewCog(commands.Cog):

    @commands.slash_command(
        name='профиль',
        description='Ваш профиль в библиотеке'
    )
    async def create_profile_view(self, ctx: discord.ApplicationContext):
        user_profile = UserProfile(ctx.author.id)
        await ctx.respond(
            embed=UserProfileEmbed(
                ctx.author,
                user_profile,
                ctx.bot.get_guild(user_profile.start_guild_id).name
            ).form(),
            view=ProfileView(timeout=60)
        )


def setup(bot):
    bot.add_cog(ProfileViewCog(bot))
