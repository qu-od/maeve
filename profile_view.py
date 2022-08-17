from typing import List, Tuple, Dict, Optional

import discord
from discord.ext import commands

from database import Database


class UserProfileData:
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.name, self.start_guild_id, self.about_me, self.is_private = \
            self.get_user_data()

    def get_user_data(self):
        pass



class UserProfileEmbed:
    def __init__(self):
        pass

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="test_initial_embed"
        )
        return embed


class ProfileViewButtons(discord.ui.View):

    @discord.ui.button(
        label='Изменить раздел "о себе"',
        style=discord.ButtonStyle.green,
        row=0
    )
    async def func_1(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        button_label_buffer: str = button.label
        button.label = button_label_buffer + " pushed"
        new_embed = discord.Embed(
            title="NEW TITLE",
            description=f'pushed button with label: "{button.label}"'
        )
        await interaction.response.edit_message(embed=new_embed)

    @discord.ui.button(
        label='Изменить приватность',
        style=discord.ButtonStyle.blurple,
        row=1
    )
    async def func_1(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        button_label_buffer: str = button.label
        button.label = button_label_buffer + " pushed"
        new_embed = discord.Embed(
            title="NEW TITLE",
            description=f'pushed button with label: "{button.label}"'
        )
        await interaction.response.edit_message(embed=new_embed)

    @discord.ui.button(
        label="Помощь",
        style=discord.ButtonStyle.blurple,
        row=2
    )
    async def func_2(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        button.label += " pushed"
        new_embed = discord.Embed(
            title="NEW TITLE",
            description=f'pushed button with label: "{button.label}"'
        )
        await interaction.response.edit_message(embed=new_embed)

    @discord.ui.button(
        label="Позвать модера",
        style=discord.ButtonStyle.gray,
        row=2
    )
    async def func_3(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        button.label += " pushed"
        new_embed = discord.Embed(
            title="NEW TITLE",
            description=f'pushed button with label: "{button.label}"'
        )
        await interaction.response.edit_message(embed=new_embed)


class ProfileView(commands.Cog):

    @commands.slash_command(
        name='профиль',
        description='Ваш профиль в библиотеке'
    )
    async def create_profile_view(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            embed=discord.Embed(title="Test embed"),
            view=ProfileViewButtons(timeout=60)
        )


def setup(bot):
    bot.add_cog(ProfileView(bot))
