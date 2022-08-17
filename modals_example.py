from typing import List, Tuple, Optional

import discord
from discord.ext import commands


class BookModal(discord.ui.Modal):
    def __init__(self, title: str = "Empty title"):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(
            label="Напишите немного о себе",
            placeholder="test_placeholder",
            value="test_value",
            style=discord.InputTextStyle.short,
        ))
        self.add_item(discord.ui.InputText(
            label="Любимые жанры",
            placeholder="test_placeholder",
            value="test_value",
            style=discord.InputTextStyle.long,
        ))
        self.add_item(discord.ui.InputText(
            label="Удобный формат обсуждения",
            placeholder="test_placeholder",
            value="test_value",
            style=discord.InputTextStyle.singleline,
        ))
        self.add_item(discord.ui.InputText(
            label="item 4",
            placeholder="test_placeholder",
            value="test_value",
            style=discord.InputTextStyle.multiline,
        ))
        self.add_item(discord.ui.InputText(
            label="item 5",
            placeholder="test_placeholder",
            value="test_value",
            style=discord.InputTextStyle.paragraph,
        ))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Your Modal Results",
            colour=discord.Color.blue()
        )
        embed.add_field(name="First Input", value=self.children[0].value, inline=False)
        embed.add_field(name="Second Input", value=self.children[1].value, inline=False)
        embed.add_field(name="3rd Input", value=self.children[2].value, inline=False)
        embed.add_field(name="4th Input", value=self.children[3].value, inline=False)
        embed.add_field(name="5th Input", value=self.children[4].value, inline=False)
        # TODO fix "10 elements embed problem"
        await interaction.response.send_message(embeds=embed)


class TestViewForModals(discord.ui.View):
    @discord.ui.button(
        label="Modal Test",
        style=discord.ButtonStyle.primary
    )
    async def button_callback(
            self, button: discord.ui.Button,
            interaction: discord.Interaction
    ):
        modal = BookModal(title="BookModal Triggered from Button")
        await interaction.response.send_modal(modal)

    @discord.ui.select(
        placeholder="Pick Your Modal",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="test_label 1",
                                 description="test_description 1"),
            discord.SelectOption(label="test_label 2",
                                 description="test_description 2"),
        ],
    )
    async def select_callback(self, select: discord.ui.Select,
                              interaction: discord.Interaction):
        modal = BookModal(
            title="label of selected option was: " + select.values[0]
        )
        await interaction.response.send_modal(modal)


class ModalsExample(commands.Cog):
    @commands.slash_command(name="modaltest")
    async def modal_slash(
            self, ctx: discord.ApplicationContext
    ):
        """Shows an example of a modal dialog
        being invoked from a slash command."""
        modal = discord.ui.Modal(title="Slash Command Modal")
        await ctx.interaction.response.send_modal(modal)

    @commands.message_command(name="messagemodal")
    async def modal_message(
            self, ctx: discord.ApplicationContext, message: discord.Message
    ):
        """Shows an example of a modal dialog
        being invoked from a message command."""
        modal = discord.ui.Modal(title="Message Command Modal")
        modal.title = f"Modal for Message ID: {message.id}"
        await ctx.interaction.response.send_modal(modal)

    @commands.user_command(name="usermodal")
    async def modal_user(
            self, ctx: discord.ApplicationContext, member: discord.Message
    ):
        """Shows an example of a modal dialog
        being invoked from a user command."""
        modal = discord.ui.Modal(title="User Command Modal")
        modal.title = f"Modal for User: {member.display_name}"
        await ctx.interaction.response.send_modal(modal)

    @commands.command()
    async def modaltest(self, ctx: commands.Context):
        """Shows an example of modals being invoked
        from an interaction component (e.g. a button or select menu)"""
        await ctx.send(
            "Click Button, Receive Modal",
            view=TestViewForModals()
        )


def setup(bot):
    bot.add_cog(ModalsExample(bot))
