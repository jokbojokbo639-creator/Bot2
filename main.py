import discord
from discord.ext import commands
import datetime
import asyncio
import time
import os
from collections import defaultdict

# ==========================
# CONFIG
# ==========================

TOKEN = os.getenv("TOKEN")

LOG_CHANNEL_ID = 1525906374628741192

SPAM_LIMIT = 3
SPAM_WINDOW = 3

MENTION_LIMIT = 4

INVITE_BLOCK = True
LINK_BLOCK = True
CAPS_BLOCK = True
RAID_LIMIT = 5
RAID_WINDOW = 10
CHANNEL_CREATE_LIMIT = 3
CHANNEL_CREATE_WINDOW = 10
ROLE_CREATE_LIMIT = 3
ROLE_CREATE_WINDOW = 10

# ==========================
# INTENTS
# ==========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
intents.voice_states = True
intents.guild_messages = True
intents.guild_reactions = True
intents.moderation = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ==========================
# DATABASE (TEMP)
# ==========================

warnings = defaultdict(lambda: {
    "count": 0,
    "reason": "لا يوجد"
})

spam = defaultdict(list)
mentions = defaultdict(list)
joins = defaultdict(list)
raid_joins = defaultdict(list)
channel_creates = defaultdict(list)
role_creates = defaultdict(list)
# ==========================
# READY
# ==========================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

    print("=" * 40)
    print(f"Logged in as {bot.user}")
    print(f"Servers : {len(bot.guilds)}")
    print("Bot Ready ✅")
    print("=" * 40)
    # ==========================
# PUNISH SYSTEM
# ==========================

async def punish(member: discord.Member, reason: str = "Auto Moderation"):
    level = warnings[member.id]["count"]

    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    punishment = "⚠️ تحذير"

    try:

        if level == 2:
            await member.timeout(
                datetime.timedelta(minutes=10),
                reason=reason
            )
            punishment = "🔇 ميوت 10 دقائق"

        elif level == 3:
            await member.timeout(
                datetime.timedelta(minutes=30),
                reason=reason
            )
            punishment = "🔇 ميوت 30 دقيقة"

        elif level == 4:
            await member.timeout(
                datetime.timedelta(hours=2),
                reason=reason
            )
            punishment = "🔇 ميوت ساعتين"

        elif level == 5:
            await member.timeout(
                datetime.timedelta(hours=4),
                reason=reason
            )
            punishment = "🔇 ميوت 4 ساعات"

        elif level == 6:
            await member.timeout(
                datetime.timedelta(hours=8),
                reason=reason
            )
            punishment = "🔇 ميوت 8 ساعات"

        elif level == 7:
            await member.kick(reason=reason)
            punishment = "👢 طرد"

        elif level >= 8:
            await member.ban(reason=reason)
            punishment = "🔨 باند"

        if log_channel:
            embed = discord.Embed(
                title="🚨 Auto Moderation",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )

            embed.add_field(
                name="👤 العضو",
                value=member.mention,
                inline=False
            )

            embed.add_field(
                name="📊 عدد التحذيرات",
                value=str(level),
                inline=True
            )

            embed.add_field(
                name="📌 العقوبة",
                value=punishment,
                inline=True
            )

            embed.add_field(
                name="📝 السبب",
                value=reason,
                inline=False
            )

            await log_channel.send(embed=embed)

    except discord.Forbidden:

        if log_channel:
            await log_channel.send(
                f"❌ لا أملك صلاحية معاقبة {member.mention}"
            )

    except Exception as e:
        print(e)
        # ==========================
# BYPASS SYSTEM
# ==========================

def is_protected(member: discord.Member) -> bool:
    """
    الأعضاء الذين لا تطبق عليهم أنظمة الحماية
    """

    # مالك السيرفر
    if member == member.guild.owner:
        return True

    perms = member.guild_permissions

    # أي شخص لديه صلاحيات إدارة
    if (
        perms.administrator
        or perms.manage_guild
        or perms.manage_messages
        or perms.manage_channels
        or perms.manage_roles
        or perms.kick_members
        or perms.ban_members
        or perms.moderate_members
    ):
        return True

    return False
    # ==========================
# MESSAGE EVENT
# ==========================

@bot.event
async def on_message(message: discord.Message):

    # تجاهل رسائل البوتات
    if message.author.bot:
        return

    # نتأكد أنها داخل سيرفر
    if not message.guild:
        return

    # تجاهل المالك والإدارة
    if is_protected(message.author):
        await bot.process_commands(message)
        return

    uid = message.author.id
    now = time.time()

    # ==========================
    # ANTI SPAM
    # ==========================

    spam[uid].append(now)

    spam[uid] = [
        t for t in spam[uid]
        if now - t < SPAM_WINDOW
    ]

    if len(spam[uid]) >= SPAM_LIMIT:

        try:
            await message.delete()
        except:
            pass

        warnings[uid]["count"] += 1
        warnings[uid]["reason"] = "Spam"

        await punish(
            message.author,
            "Spam"
        )

        try:
            await message.channel.send(
                f"🚫 {message.author.mention} يمنع السبام.",
                delete_after=5
            )
        except:
            pass

        return
        
        # ==========================
    # ANTI MENTION SPAM
    # ==========================

    if len(message.mentions) >= MENTION_LIMIT:

        try:
            await message.delete()
        except:
            pass

        warnings[uid]["count"] += 1
        warnings[uid]["reason"] = "Mention Spam"

        await punish(
            message.author,
            "Mention Spam"
        )

        try:
            await message.channel.send(
                f"🚫 {message.author.mention} يمنع المنشن الجماعي.",
                delete_after=5
            )
        except:
            pass

        return
            # ==========================
    # ANTI DISCORD INVITES
    # ==========================

    if INVITE_BLOCK:

        content = message.content.lower()

        invite_links = (
            "discord.gg/",
            "discord.com/invite/",
            "discordapp.com/invite/"
        )

        if any(link in content for link in invite_links):

            try:
                await message.delete()
            except:
                pass

            warnings[uid]["count"] += 1
            warnings[uid]["reason"] = "Discord Invite"

            await punish(
                message.author,
                "Discord Invite"
            )

            try:
                await message.channel.send(
                    f"🚫 {message.author.mention} يمنع نشر روابط دعوات الديسكورد.",
                    delete_after=5
                )
            except:
                pass

            return
                # ==========================
    # ANTI LINKS
    # ==========================

    if LINK_BLOCK:

        content = message.content.lower()

        # روابط الديسكورد ممنوعة دائمًا
        discord_invites = (
            "discord.gg/",
            "discord.com/invite/",
            "discordapp.com/invite/"
        )

        # المواقع المسموح بها
        allowed_domains = (
            "youtube.com",
            "youtu.be",
            "google.com",
            "github.com",
            "instagram.com",
            "tiktok.com",
            "facebook.com",
            "x.com",
            "twitter.com",
        )

        # منع دعوات الديسكورد
        if any(invite in content for invite in discord_invites):

            try:
                await message.delete()
            except:
                pass

            warnings[uid]["count"] += 1
            warnings[uid]["reason"] = "Discord Invite"

            await punish(message.author, "Discord Invite")

            await message.channel.send(
                f"🚫 {message.author.mention} يمنع نشر دعوات الديسكورد.",
                delete_after=5
            )

            return

        # التحقق من الروابط الأخرى
        if "http://" in content or "https://" in content or "www." in content:

            if not any(domain in content for domain in allowed_domains):

                try:
                    await message.delete()
                except:
                    pass

                warnings[uid]["count"] += 1
                warnings[uid]["reason"] = "Unknown Link"

                await punish(message.author, "Unknown Link")

                await message.channel.send(
                    f"🚫 {message.author.mention} هذا الرابط غير مسموح.",
                    delete_after=5
                )

                return
                    # ==========================
    # ANTI CAPS
    # ==========================

    if CAPS_BLOCK:

        text = message.content.strip()

        # تجاهل الرسائل القصيرة
        if len(text) >= 8:

            letters = [c for c in text if c.isalpha()]

            if letters:

                uppercase = sum(c.isupper() for c in letters)

                percentage = uppercase / len(letters)

                # إذا كانت أكثر من 80% من الأحرف كبيرة
                if percentage >= 0.80:

                    try:
                        await message.delete()
                    except:
                        pass

                    warnings[uid]["count"] += 1
                    warnings[uid]["reason"] = "Caps Spam"

                    await punish(
                        message.author,
                        "Caps Spam"
                    )

                    try:
                        await message.channel.send(
                            f"🚫 {message.author.mention} يرجى عدم الكتابة بالأحرف الكبيرة فقط.",
                            delete_after=5
                        )
                    except:
                        pass

                    return

    await bot.process_commands(message)
    # ==========================
# ANTI RAID
# ==========================

@bot.event
async def on_member_join(member: discord.Member):

    if is_protected(member):
        return

    now = time.time()

    raid_joins[member.guild.id].append(now)

    raid_joins[member.guild.id] = [
        t for t in raid_joins[member.guild.id]
        if now - t < RAID_WINDOW
    ]

    if len(raid_joins[member.guild.id]) >= RAID_LIMIT:

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            embed = discord.Embed(
                title="🚨 تم اكتشاف Raid",
                description=(
                    f"دخل **{len(raid_joins[member.guild.id])}** أعضاء "
                    f"خلال **{RAID_WINDOW}** ثوانٍ."
                ),
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )

            await log.send(embed=embed)
        # ==========================
# VOICE MUTE
# ==========================

@bot.tree.command(
    name="vmute",
    description="كتم عضو في الروم الصوتي"
)
async def vmute(
    interaction: discord.Interaction,
    member: discord.Member
):

    # التحقق من الصلاحيات
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ليس لديك صلاحية.",
            ephemeral=True
        )

    # تجاهل المالك والإدارة
    if is_protected(member):
        return await interaction.response.send_message(
            "❌ لا يمكن كتم الإدارة أو مالك السيرفر.",
            ephemeral=True
        )

    # يجب أن يكون العضو داخل روم صوتي
    if member.voice is None:
        return await interaction.response.send_message(
            "❌ العضو ليس داخل روم صوتي.",
            ephemeral=True
        )

    try:

        await member.edit(
            mute=True,
            reason=f"Voice Mute | {interaction.user}"
        )

        await interaction.response.send_message(
            f"🔇 تم كتم {member.mention} في الروم الصوتي."
        )

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(
                f"🔇 {interaction.user.mention} قام بكتم {member.mention} في الفويس."
            )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ {e}",
            ephemeral=True
        )
        # ==========================
# VOICE UNMUTE
# ==========================

@bot.tree.command(
    name="vunmute",
    description="فك كتم عضو في الروم الصوتي"
)
async def vunmute(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ليس لديك صلاحية.",
            ephemeral=True
        )

    if member.voice is None:
        return await interaction.response.send_message(
            "❌ العضو ليس داخل روم صوتي.",
            ephemeral=True
        )

    try:

        await member.edit(
            mute=False,
            reason=f"Voice Unmute | {interaction.user}"
        )

        await interaction.response.send_message(
            f"🔊 تم فك كتم {member.mention}."
        )

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(
                f"🔊 {interaction.user.mention} قام بفك كتم {member.mention}."
            )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ {e}",
            ephemeral=True
        )
        # ==========================
# VOICE MUTE ALL
# ==========================

@bot.tree.command(
    name="vmuteall",
    description="كتم جميع أعضاء الرومات الصوتية"
)
async def vmuteall(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ليس لديك صلاحية.",
            ephemeral=True
        )

    muted = 0

    for member in interaction.guild.members:

        if member.voice is None:
            continue

        if is_protected(member):
            continue

        try:
            await member.edit(
                mute=True,
                reason=f"Voice Mute All | {interaction.user}"
            )
            muted += 1

        except Exception:
            pass

    await interaction.response.send_message(
        f"🔇 تم كتم **{muted}** عضو في الرومات الصوتية."
    )

    log = bot.get_channel(LOG_CHANNEL_ID)

    if log:
        await log.send(
            f"🔇 {interaction.user.mention} استخدم أمر Voice Mute All.\n"
            f"عدد الأعضاء: **{muted}**"
        )
        # ==========================
# VOICE UNMUTE ALL
# ==========================

@bot.tree.command(
    name="vunmuteall",
    description="فك كتم جميع أعضاء الرومات الصوتية"
)
async def vunmuteall(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ليس لديك صلاحية.",
            ephemeral=True
        )

    unmuted = 0

    for member in interaction.guild.members:

        if member.voice is None:
            continue

        if is_protected(member):
            continue

        try:
            await member.edit(
                mute=False,
                reason=f"Voice Unmute All | {interaction.user}"
            )
            unmuted += 1

        except Exception:
            pass

    await interaction.response.send_message(
        f"🔊 تم فك كتم **{unmuted}** عضو في الرومات الصوتية."
    )

    log = bot.get_channel(LOG_CHANNEL_ID)

    if log:
        await log.send(
            f"🔊 {interaction.user.mention} استخدم أمر Voice Unmute All.\n"
            f"عدد الأعضاء: **{unmuted}**"
        )
        # ==========================
# USER INFO
# ==========================

@bot.tree.command(
    name="userinfo",
    description="عرض معلومات عضو"
)
async def userinfo(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    member = member or interaction.user

    embed = discord.Embed(
        title="👤 معلومات العضو",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="👤 الاسم",
        value=member.name,
        inline=True
    )

    embed.add_field(
        name="📝 الاسم المعروض",
        value=member.display_name,
        inline=True
    )

    embed.add_field(
        name="🆔 ID",
        value=member.id,
        inline=False
    )

    embed.add_field(
        name="📅 إنشاء الحساب",
        value=f"<t:{int(member.created_at.timestamp())}:F>",
        inline=False
    )

    embed.add_field(
        name="📥 دخول السيرفر",
        value=f"<t:{int(member.joined_at.timestamp())}:F>",
        inline=False
    )

    embed.add_field(
        name="🎭 أعلى رتبة",
        value=member.top_role.mention,
        inline=False
    )

    embed.add_field(
        name="🤖 بوت؟",
        value="✅ نعم" if member.bot else "❌ لا",
        inline=True
    )

    embed.add_field(
        name="⚠️ التحذيرات",
        value=str(warnings[member.id]["count"]),
        inline=True
    )

    await interaction.response.send_message(embed=embed)
        # ==========================
# NICKNAME
# ==========================

@bot.tree.command(
    name="nickname",
    description="تغيير لقب عضو"
)
async def nickname(
    interaction: discord.Interaction,
    member: discord.Member,
    nickname: str = None
):

    if not interaction.user.guild_permissions.manage_nicknames:
        return await interaction.response.send_message(
            "❌ ليس لديك صلاحية.",
            ephemeral=True
        )

    # تجاهل الإدارة والمالك
    if is_protected(member):
        return await interaction.response.send_message(
            "❌ لا يمكن تغيير لقب الإدارة أو مالك السيرفر.",
            ephemeral=True
        )

    # لا يمكن تعديل عضو أعلى رتبة
    if member.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            "❌ لا يمكنك تعديل عضو رتبته أعلى أو مساوية لرتبتك.",
            ephemeral=True
        )

    # يجب أن تكون رتبة البوت أعلى
    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "❌ رتبة البوت أقل من رتبة العضو.",
            ephemeral=True
        )

    try:
        await member.edit(
            nick=nickname,
            reason=f"By {interaction.user}"
        )

        embed = discord.Embed(
            title="✏️ تم تغيير اللقب",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(
            name="👤 العضو",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="📝 اللقب الجديد",
            value=nickname if nickname else "تمت إزالة اللقب",
            inline=False
        )

        embed.add_field(
            name="🛡️ بواسطة",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ {e}",
            ephemeral=True
        )

bot.run(TOKEN)
