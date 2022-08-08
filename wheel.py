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



