import discord
from discord.ext import commands
import json, os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATA =================
def load():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"apps": {}}, f)
    with open("data.json", "r") as f:
        return json.load(f)

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= CREATE =================
class CreateView(discord.ui.View):
    def __init__(self, name, log):
        super().__init__(timeout=300)
        self.name = name
        self.log = log
        self.questions = []
        self.mode = None
        self.role = None

    @discord.ui.button(label="➕ إضافة سؤال", style=discord.ButtonStyle.blurple)
    async def add_question(self, interaction: discord.Interaction, button: discord.ui.Button):

        if len(self.questions) >= 5:
            return await interaction.response.send_message("❌ الحد 5 أسئلة", ephemeral=True)

        class QModal(discord.ui.Modal, title="سؤال"):
            q = discord.ui.TextInput(label="اكتب السؤال")

            async def on_submit(self, interaction: discord.Interaction):
                self.view.questions.append(self.q.value)
                await interaction.response.send_message("✅ تمت الإضافة", ephemeral=True)

        modal = QModal()
        modal.view = self
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🎖️ تحديد رتبة", style=discord.ButtonStyle.gray)
    async def set_role(self, interaction: discord.Interaction, button: discord.ui.Button):

        class RoleModal(discord.ui.Modal, title="Role ID"):
            role_id = discord.ui.TextInput(label="حط ID الرتبة")

            async def on_submit(self, interaction: discord.Interaction):
                self.view.role = self.role_id.value
                await interaction.response.send_message("✅ تم حفظ الرتبة", ephemeral=True)

        modal = RoleModal()
        modal.view = self
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📌 دمج", style=discord.ButtonStyle.gray)
    async def merge(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "merge"
        await interaction.response.send_message("تم اختيار الدمج", ephemeral=True)

    @discord.ui.button(label="📂 روم لحاله", style=discord.ButtonStyle.gray)
    async def single(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "single"
        await interaction.response.send_message("تم اختيار روم منفصل", ephemeral=True)

    @discord.ui.button(label="💾 حفظ", style=discord.ButtonStyle.green)
    async def save_app(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.questions:
            return await interaction.response.send_message("❌ أضف أسئلة", ephemeral=True)

        if not self.mode:
            return await interaction.response.send_message("❌ اختر نوع", ephemeral=True)

        data = load()

        data["apps"][self.name] = {
            "questions": self.questions,
            "log": self.log,
            "mode": self.mode,
            "role": self.role
        }

        save(data)

        await interaction.response.send_message("✅ تم الحفظ", ephemeral=True)
        self.stop()

# ================= REVIEW =================
class ReviewButtons(discord.ui.View):
    def __init__(self, user, role_id=None):
        super().__init__(timeout=None)
        self.user = user
        self.role_id = role_id

    @discord.ui.button(label="✅ قبول", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        class Reason(discord.ui.Modal, title="سبب القبول"):
            reason = discord.ui.TextInput(label="السبب (اختياري)", required=False)

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    msg = "✅ تم قبولك"
                    if self.reason.value:
                        msg += f"\nالسبب: {self.reason.value}"

                    await self.view.user.send(msg)

                    if self.view.role_id:
                        role = interaction.guild.get_role(int(self.view.role_id))
                        if role:
                            await self.view.user.add_roles(role)

                except:
                    pass

                await interaction.response.send_message("تم القبول", ephemeral=True)

        modal = Reason()
        modal.view = self
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ رفض", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):

        class Reason(discord.ui.Modal, title="سبب الرفض"):
            reason = discord.ui.TextInput(label="اكتب السبب")

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    await self.view.user.send(f"❌ تم رفضك\nالسبب: {self.reason.value}")
                except:
                    pass

                await interaction.response.send_message("تم الرفض", ephemeral=True)

        modal = Reason()
        modal.view = self
        await interaction.response.send_modal(modal)

# ================= APPLY =================
class ApplyModal(discord.ui.Modal):
    def __init__(self, name, questions, log, role):
        super().__init__(title=name)
        self.name = name
        self.questions = questions
        self.log = log
        self.role = role

        self.inputs = []

        for q in questions:
            t = discord.ui.TextInput(label=q)
            self.add_item(t)
            self.inputs.append(t)

    async def on_submit(self, interaction: discord.Interaction):

        channel = bot.get_channel(int(self.log))

        embed = discord.Embed(title=f"📩 {self.name}", color=0x2b2d31)

        for i, inp in enumerate(self.inputs):
            embed.add_field(name=self.questions[i], value=inp.value, inline=False)

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        await channel.send(
            embed=embed,
            view=ReviewButtons(interaction.user, self.role)
        )

        await interaction.response.send_message("✅ تم الإرسال", ephemeral=True)

# ================= VIEW =================
class ApplyView(discord.ui.View):
    def __init__(self, apps):
        super().__init__(timeout=None)

        select = discord.ui.Select(
            placeholder="اختر التقديم",
            options=[discord.SelectOption(label=name) for name in apps]
        )

        async def callback(interaction: discord.Interaction):
            data = load()
            app = data["apps"][select.values[0]]

            await interaction.response.send_modal(
                ApplyModal(
                    select.values[0],
                    app["questions"],
                    app["log"],
                    app.get("role")
                )
            )

        select.callback = callback
        self.add_item(select)

# ================= COMMANDS =================
@bot.tree.command(name="create_app")
async def create_app(interaction: discord.Interaction, name: str, log: str):
    await interaction.response.send_message(
        "ابدأ إعداد التقديم",
        view=CreateView(name, log),
        ephemeral=True
    )

@bot.tree.command(name="delete_app")
async def delete_app(interaction: discord.Interaction, name: str):
    data = load()

    if name in data["apps"]:
        del data["apps"][name]
        save(data)
        await interaction.response.send_message("✅ تم الحذف", ephemeral=True)
    else:
        await interaction.response.send_message("❌ غير موجود", ephemeral=True)

@bot.tree.command(name="setup")
async def setup(interaction: discord.Interaction):
    data = load()

    if not data["apps"]:
        return await interaction.response.send_message("❌ ما فيه تقديمات", ephemeral=True)

    embed = discord.Embed(
        title="📋 التقديمات",
        description="\n".join(data["apps"].keys()),
        color=0x2b2d31
    )

    await interaction.channel.send(embed=embed, view=ApplyView(data["apps"]))
    await interaction.response.send_message("تم", ephemeral=True)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("BOT READY")

bot.run(TOKEN)