import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 เปิด Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            category = await guild.create_category("TICKETS")

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"มี Ticket ของคุณอยู่แล้ว: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}".replace(" ", "-")[:90],
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket เปิดแล้ว",
            description=f"สวัสดี {interaction.user.mention} 💗\nทีมงานจะเข้ามาดูแลโดยเร็วที่สุด\n\nกดปุ่มด้านล่างเพื่อปิด Ticket",
            color=discord.Color.from_rgb(255, 170, 220)
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"สร้าง Ticket แล้ว: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 ปิด Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("กำลังปิด Ticket...", ephemeral=True)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user} | Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        embed = discord.Embed(
            title="✨ ยินดีต้อนรับ!",
            description=f"ยินดีต้อนรับ {member.mention} เข้าสู่ **{member.guild.name}** 💗",
            color=discord.Color.from_rgb(180, 210, 255)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.tree.command(name="help", description="ดูคำสั่งของบอท")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌸 Discord Shop Bot",
        description="บอทจัดการร้านและเซิร์ฟเวอร์",
        color=discord.Color.from_rgb(255, 180, 220)
    )
    embed.add_field(name="🎫 Ticket", value="ใช้ `/ticket` เพื่อสร้างแผงเปิด Ticket", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`/clear` ลบข้อความในห้อง", inline=False)
    embed.add_field(name="📢 ร้าน", value="ใช้ Ticket สำหรับรับออเดอร์/สอบถาม", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ticket", description="สร้างแผงเปิด Ticket")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💗 ติดต่อร้าน / สั่งซื้อ",
        description="กดปุ่ม **🎫 เปิด Ticket** ด้านล่างเพื่อเปิดห้องส่วนตัวกับทีมงาน",
        color=discord.Color.from_rgb(255, 170, 220)
    )
    embed.set_footer(text="Shop Support • Please do not spam tickets")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("สร้างแผง Ticket เรียบร้อยแล้ว ✨", ephemeral=True)

@bot.tree.command(name="clear", description="ลบข้อความจำนวนหนึ่ง")
@app_commands.describe(amount="จำนวนข้อความที่ต้องการลบ (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_command(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("ใส่จำนวน 1-100 เท่านั้น", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 ลบข้อความแล้ว {len(deleted)} ข้อความ", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้"
    else:
        msg = f"❌ เกิดข้อผิดพลาด: `{error}`"
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

if not TOKEN:
    raise RuntimeError("กรุณาตั้งค่า DISCORD_TOKEN ก่อนรันบอท")

bot.run(TOKEN)
