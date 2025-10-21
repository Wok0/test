import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button

# Récupère le token depuis Railway
TOKEN = os.environ["DISCORD_TOKEN"]  # ← juste le nom de la variable, pas le token lui-même


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs à modifier
STAFF_ROLE_ID = 1131318992246677624
TICKET_CATEGORY_ID = 987654321098765432
TICKET_COMMAND_ROLE_ID = 1131318992246677624


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        await bot.tree.sync()
        print("Commandes slash synchronisées !")
    except Exception as e:
        print(f"Erreur lors de la sync : {e}")


class CloseButton(Button):
    def __init__(self):
        super().__init__(label="Fermer le ticket", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        await interaction.response.send_message("🕓 Fermeture du ticket...", ephemeral=True)
        await channel.delete()


class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="Problème technique"),
            discord.SelectOption(label="Commande", description="Question sur une commande"),
            discord.SelectOption(label="Autre", description="Autre demande"),
            discord.SelectOption(label="Serveur", description="Demande d'accès au serveur"),
        ]
        super().__init__(placeholder="📩 Choisis le type de ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        ticket_type = self.values[0]
        author = interaction.user
        ticket_name = f"ticket-{author.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎟️ Ticket {ticket_type}",
            description=f"{author.mention}, votre ticket a été créé ! Un membre du staff va bientôt vous répondre.",
            color=discord.Color.green()
        )

        view = View()
        view.add_item(CloseButton())

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Votre ticket a été créé : {channel.mention}", ephemeral=True)

        self.view.clear_items()
        self.view.add_item(TicketSelect())


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


@bot.tree.command(name="ticket", description="Crée le menu de création de tickets (réservé au staff)")
async def ticket(interaction: discord.Interaction):
    role = interaction.guild.get_role(TICKET_COMMAND_ROLE_ID)
    if role not in interaction.user.roles:
        await interaction.response.send_message("❌ Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📩 Crée ton ticket",
        description="Choisis le type de ticket ci-dessous pour contacter le staff.\n\n"
                    "🛠️ **Support** — Problème technique\n"
                    "💰 **Commande** — Question ou achat\n"
                    "💬 **Autre** — Toute autre demande"
                    "👀 **Serveur** — Demande d'accès au serveur",
        color=discord.Color.blurple()
    )

    view = TicketView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Le menu des tickets a été envoyé avec succès.", ephemeral=True)


bot.run(TOKEN)

