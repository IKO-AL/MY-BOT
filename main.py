import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import io
import asyncio

TOKEN = 'MTMzMDYxMjMxNjg3ODE4MTQ4OQ.GWzYgE.P1m8p-C7QkIIn0w2V2n_uR8xL_Tz9DqG8M7XwY'

CONFIG = {
    "High":    {"log": 1456097051493531689, "role": 1458828830197415967, "name": "الإدارة العليا", "desc": "للمشاكل الإدارية الكبيرة", "emoji": "👑"},
    "Support": {"log": 1456096932224041154, "role": 1254488623483584573, "name": "الدعم الفني", "desc": "للمساعدة التقنية العامة", "emoji": "🛠️"},
    "Kick":    {"log": 1456096641164771442, "role": 1254488625958223943, "name": "البلاغات", "desc": "لتقديم بلاغ رسمي", "emoji": "🛡️"},
    "Event":   {"log": 1456096775365722174, "role": 1456098901831712778, "name": "الفعاليات", "desc": "للمسابقات والجوائز", "emoji": "🎉"},
    "Store":   {"log": 1456096932224041154, "role": 1459890113772388362, "name": "المتجر", "desc": "لشراء الرتب والمزايا", "emoji": "💰"},
    "Girls":   {"log": 1459522223319810109, "role": 1459218745019858955, "name": "البنات", "desc": "قسم خاص بالبنات", "emoji": "🌸"}
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class TicketControl(View):
    def __init__(self, category):
        super().__init__(timeout=None)
        self.category = category

    @discord.ui.button(label="استلام", style=discord.ButtonStyle.green, emoji="✅")
    async def claim(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message(f"✅ استلم التذكرة: {interaction.user.mention}")

    @discord.ui.button(label="حفظ", style=discord.ButtonStyle.secondary, emoji="💾")
    async def save(self, interaction: discord.Interaction, button: discord.Button):
        messages = [f"{m.author.name}: {m.content}" async for m in interaction.channel.history(limit=None, oldest_first=True)]
        file = discord.File(io.BytesIO("\n".join(messages).encode()), filename="log.txt")
        log_ch = bot.get_channel(CONFIG[self.category]["log"])
        if log_ch: await log_ch.send(f"📄 سجل {CONFIG[self.category]['name']}", file=file)
        await interaction.response.send_message("✅ تم الحفظ في اللوق", ephemeral=True)

    @discord.ui.button(label="إغلاق", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("⚠️ سيتم الحذف خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketMenu(Select):
    def __init__(self):
        options = [discord.SelectOption(label=v['name'], value=k, description=v['desc'], emoji=v["emoji"]) for k, v in CONFIG.items()]
        super().__init__(placeholder="اختر القسم لفتح تذكرة...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cat = self.values[0]
        role = interaction.guild.get_role(CONFIG[cat]["role"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }
        if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        ch = await interaction.guild.create_text_channel(f"{cat}-{interaction.user.name}", overwrites=overwrites)
        await interaction.followup.send(f"✅ تم فتح تذكرتك: {ch.mention}", ephemeral=True)
        await ch.send(content=f"أهلاً {interaction.user.mention}\nيرجى ذكر مشكلتك بوضوح.", view=TicketControl(cat))

@bot.event
async def on_ready():
    print(f'✅ البوت {bot.user} شغال ومرتبط بالديسكورد!')

@bot.command()
async def setup(ctx):
    await ctx.send(content="**نظام التذاكر | Ticket System**\nاختر القسم من القائمة لفتح تذكرة.", view=View().add_item(TicketMenu()))

bot.run(TOKEN)
