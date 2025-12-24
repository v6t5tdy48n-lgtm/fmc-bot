import discord
from discord.ext import commands
import json
import os          # ✅ ICI
import time
import asyncio
from datetime import datetime, timedelta

WELCOME_CHANNEL_ID = 1452305380167385239
LOG_CHANNEL_ID = 1452327704182526093
MEATING_CHANNEL_ID = 1452444928033554463

WELCOME_IMAGE_URL = "https://cdn.discordapp.com/attachments/1374090923494998118/1452370379296473119/IMG_2030.gif"

intents = discord.Intents.default()
intents.members = True
intents.invites = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

INVITES = {}
BLOCK_FILE = "data/blocked_users.json"


# ================= UTIL =================

def load_blocked():
    if not os.path.exists(BLOCK_FILE):
        return []
    with open(BLOCK_FILE, "r") as f:
        return json.load(f)

def save_blocked(data):
    os.makedirs(os.path.dirname(BLOCK_FILE), exist_ok=True)
    with open(BLOCK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def now_string():
    return datetime.now().strftime("%d/%m at %H:%M")


# ================= READY =================

@bot.event
async def on_ready():
    print(f"✅ Connected as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

    for guild in bot.guilds:
        try:
            INVITES[guild.id] = await guild.invites()
        except discord.Forbidden:
            print(f"⚠️ Missing permissions to read invites in {guild.name}")


# ================= BLOCK VIEW =================

class BlockView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(
        label="🚫 Stop receiving FMC Bot joining messages",
        style=discord.ButtonStyle.danger
    )
    async def block(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "❌ This button is not for you.",
                ephemeral=True
            )

        blocked = load_blocked()
        if self.user_id not in blocked:
            blocked.append(self.user_id)
            save_blocked(blocked)

        await interaction.response.send_message(
            "✅ You will no longer receive private messages from FMC Bot.",
            ephemeral=True
        )


# ================= MEMBER JOIN =================

@bot.event
async def on_member_join(member):
    if member.id in load_blocked():
        return

    inviter = "Unknown"
    new_invites = await member.guild.invites()

    for old in INVITES.get(member.guild.id, []):
        for new in new_invites:
            if old.code == new.code and old.uses < new.uses:
                inviter = new.inviter.mention

    INVITES[member.guild.id] = new_invites

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

    embed = discord.Embed(
        title="👋 Welcome Here",
        description=f"{member.mention} was invited by {inviter}.\nCheck your private messages.",
        color=discord.Color.from_rgb(220, 240, 255)
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=WELCOME_IMAGE_URL)

    if channel:
        await channel.send(embed=embed)

    dm = discord.Embed(
        title=f"👋 Welcome to FMC {member.mention}",
        description=(
            "Apply to become **Member, Ultra Teams, STAFF, or a higher rank** "
            "[here](https://discord.com/channels/1452302135927635978/1452327848151879712)\n\n"
            "**Open a ticket for support, wars, partnerships, or more** "
            "[here](https://discord.com/channels/1452302135927635978/1452307468569935984)\n\n"
            "Please read and follow the rules "
            "[here](https://discord.com/channels/1452302135927635978/1452305916182532106)\n\n"
            "Thank you for joining us!\n\n"
            "https://discord.gg/xEGPvej7QW"
        ),
        color=discord.Color.from_rgb(220, 240, 255)
    )

    try:
        await member.send(embed=dm, view=BlockView(member.id))
    except discord.Forbidden:
        pass


# ================= ROLE ACCEPT LOG =================

@bot.event
async def on_member_update(before, after):
    guild = after.guild
    log_channel = guild.get_channel(LOG_CHANNEL_ID)

    if not log_channel:
        return

    for role in after.roles:
        if role not in before.roles:
            embed = discord.Embed(
                title=f"👋 Accepted as {role.name}",
                description=(
                    f"{after.mention} has been accepted as **{role.mention}**\n\n"
                    f"He was added by **a staff member**\n"
                    f"📅 {now_string()}"
                ),
                color=discord.Color.blue()
            )

            embed.set_thumbnail(url=after.display_avatar.url)
            await log_channel.send(embed=embed)


# ================= SLASH GROUP /meating =================

class Meating(app_commands.Group):
    def __init__(self):
        super().__init__(name="meating", description="Meeting commands")

    @app_commands.command(name="create", description="Create a new meeting")
    @app_commands.describe(
        date="Meeting date (01/01/2000)",
        time="Meeting time (18h30)",
        private_server="Private server?",
        location="Location",
        join_account="Roblox ID (optional)",
        extra_description="Additional description (optional)"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        private_server: bool,
        location: str,
        join_account: str | None = None,
        extra_description: str | None = None
    ):
        if interaction.channel.id != MEATING_CHANNEL_ID:
            return await interaction.response.send_message(
                "❌ This command is used in the wrong channel.",
                ephemeral=True
            )

        description = (
            f"📆 **Date :** {date}\n"
            f"🕦 **Time :** {time}\n"
        )

        if private_server:
            description += (
                "🛣️ On a **Private Server** "
                "([Click here for more information]"
                "(https://discord.com/channels/1452302135927635978/1453393254664900700))\n"
            )
        else:
            description += "🛣️ On a **Public Server**\n"

        description += f"📍 **Location :** {location}\n"

        if join_account:
            description += f"📲 **Join the Account :** {join_account}\n"

        if extra_description:
            description += f"➕ **Description :** {extra_description}\n"

        embed = discord.Embed(
    title="🥷 New Meating",
    description=description,
    color=discord.Color.from_rgb(220, 240, 255)
)

embed.set_image(url="https://cdn.discordapp.com/attachments/1374090923494998118/1453399141508972554/0EAF8801-D993-4186-B1A5-846D03505B9A.jpg?ex=694d4eee&is=694bfd6e&hm=b9cddf71b1a2b9a34008cda9c38918cea8e5731120b64b1e5d8f4c5d2cfa4dfd&")

        await interaction.response.send_message(
            content="-# ||<@&1453392087994339526> <@&1452380941900320831>||",
            embed=embed
        )


bot.tree.add_command(Meating())


# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))