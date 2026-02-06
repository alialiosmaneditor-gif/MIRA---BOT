import discord
from discord.ext import commands, tasks
import os
import random
import asyncio
import time
import requests
from flask import Flask
from threading import Thread

# --- نظام البقاء متصلاً (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "ميرا متصلة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.start()

# --- إعدادات البوت الأساسية ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# قاعدة بيانات مؤقتة (Data Storage)
db = {
    'cash': {},      
    'stocks': {},
    'animals': {},
    'team_with': {},
    'last_stock_update': time.time(),
    'main_channel': None
}

stock_price = 300
jobs = [
    {"name": "طبيب 👨‍⚕️", "min": 800, "max": 1200},
    {"name": "مهندس 👷", "min": 700, "max": 1000},
    {"name": "مبرمج 💻", "min": 900, "max": 1500},
    {"name": "طيار 👨‍✈️", "min": 1200, "max": 2000}
]

# --- قائمة الأعلام بمستويات عشوائية ---
flags_levels = {
    "سهل": {"🇸🇦": "السعودية", "🇰🇼": "الكويت", "🇦🇪": "الإمارات", "🇶🇦": "قطر", "🇺🇸": "امريكا"},
    "متوسط": {"🇲🇦": "المغرب", "🇩🇿": "الجزائر", "🇯🇵": "اليابان", "🇫🇷": "فرنسا", "🇧🇷": "البرازيل"},
    "صعب": {"🇰🇮": "كيريباتي", "🇲🇿": "موزمبيق", "🇧🇹": "بوتان", "🇦🇸": "ساموا"}
}

# --- دوال المساعدة ---
def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

# --- نظام الأسهم التلقائي (كل 10 دقائق) ---
@tasks.loop(minutes=10)
async def change_stock_price():
    global stock_price
    old_price = stock_price
    stock_price = random.randint(250, 500)
    db['last_stock_update'] = time.time()
    if db['main_channel']:
        channel = bot.get_channel(db['main_channel'])
        if channel:
            trend = "ارتفع 📈" if stock_price > old_price else "نزل 📉"
            await channel.send(f"📢 **تحديث سوق الأسهم:**\nسعر السهم الجديد صار: **{stock_price} ريال** {trend}")

@bot.event
async def on_ready(): 
    print(f'ميرا جاهزة لخدمتكم: {bot.user} ✅')
    if not change_stock_price.is_running(): change_stock_price.start()

# --- 📜 شرح الأوامر (تنسيق واضح بالايموجيات) ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    help_msg = (
        "👋 **مرحباً بك في عالم ميرا! إليك قائمة الأوامر:**\n\n"
        "💰 **الاقتصاد والعمل:**\n"
        "• `عمل` 💼: اشتغل وجمع راتبك كل 5 دقايق 💸\n"
        "• `زرف @منشن` 🥷: اسرق كاش من خويك بس انتبه تنقفط 🚔\n"
        "• `رصيدي` 💳: عشان تشوف فلوسك، أسهمك، ونقاطك 💰\n\n"
        "📈 **الاستثمار (الأسهم):**\n"
        "• `الأسهم` 📊: عرض سعر السوق الحالي 📉\n"
        "• `شراء سهم` 🛒: استثمر كاشك في أسهم ميرا 💎\n"
        "• `بيع سهم` 💰: بيع لما يرتفع السعر وتصير هامور 🐳\n\n"
        "🤝 **نظام الفريق:**\n"
        "• `فريق @منشن` 👥: سو فريق مع خويك.. الفوز مشترك 🤝\n\n"
        "🎮 **المسابقات (تجمع لك نقاط):**\n"
        "• `أعلام` 🌍: تحدي عشوائي (سهل/متوسط/صعب) لخمن العلم 🚩\n"
        "• `عكس` 🔄: البوت يعطيك كلمة وأنت تعكسها بسرعة ⚡\n"
        "• `حيوانات` 🐾: أسرع واحد يكتب اسم حيوان يبدأ بالحرف المطلوب 🦁"
    )
    await ctx.reply(help_msg)

# --- أوامر الاقتصاد ---
@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    db['main_channel'] = ctx.channel.id
    job = random.choice(jobs)
    salary = random.randint(job['min'], job['max'])
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 اشتغلت **{job['name']}** وعطوك راتب **{salary} ريال**.. كفو يا وحش! 💸")

@bot.command(name='زرف')
@commands.cooldown(1, 300, commands.BucketType.user)
async def rob(ctx, member: discord.Member = None):
    if not member or member == ctx.author: return await ctx.reply("منشن الضحية اللي تبي تزرفها! 😂🏃‍♂️")
    if get_val(member.id, 'cash') < 500: return await ctx.reply("هذا المسكين طفران، اترك حاله يرزقه الله.. 😅💔")
    
    if random.randint(1, 100) > 50:
        stolen = random.randint(100, 400)
        update_val(member.id, 'cash', -stolen); update_val(ctx.author.id, 'cash', stolen)
        await ctx.reply(f"🥷 كفووو! زرفت من {member.mention} مبلغ **{stolen} ريال**! 😎💰")
    else:
        update_val(ctx.author.id, 'cash', -200)
        await ctx.reply("🤦‍♂️ حظك تعبان! انقفطت ودفعت غرامة 200 ريال 🚔💸")

# --- أوامر المسابقات ---
@bot.command(name='أعلام')
async def flags_game(ctx):
    level = random.choice(["سهل", "متوسط", "صعب"])
    flag, name = random.choice(list(flags_levels[level].items()))
    points = 3 if level == "صعب" else 1
    await ctx.send(f"🌍 | **تحدي الأعلام ({level})**\nأسرع واحد يكتب اسم هالدولة: {flag}")
    
    def check(m): return m.channel == ctx.channel and m.content.strip() == name
    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
        update_val(msg.author.id, 'animals', points)
        res = f"🎉 بطل يا <@{msg.author.id}>! هذي **{name}** وأخذت {points} نقطة ✨"
        if str(msg.author.id) in db['team_with']:
            update_val(db['team_with'][str(msg.author.id)], 'animals', points)
            res += " وخويك بالفريق أخذ مثلها! 🤝🔥"
        await ctx.send(res)
    except: await ctx.send(f"⏰ انتهى الوقت! محد عرفها، كانت **{name}** 🚩")

@bot.command(name='عكس')
async def reverse_game(ctx):
    try:
        r = requests.get("https://raw.githubusercontent.com")
        word = random.choice([w for w in r.text.split() if 3 <= len(w) <= 6])
    except: word = "اقتصاد"
    reversed_w = word[::-1]
    await ctx.send(f"🔄 | أسرع واحد يعكس هالكلمة: **{word}**")
    def check(m): return m.channel == ctx.channel and m.content.strip() == reversed_w
    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
        update_val(msg.author.id, 'animals', 1)
        await ctx.send(f"🎉 جبتها يا ذيب <@{msg.author.id}>! ⚡")
    except: await ctx.send(f"⏰ انتهى الوقت! كانت **{reversed_w}** 🔄")

# --- الأوامر العامة ---
@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    t = f"<@{db['team_with'][str(u)]}>" if str(u) in db['team_with'] else "لا يوجد"
    await ctx.reply(f"🏦 **محفظتك يا بطل:**\n💵 كاش: {get_val(u, 'cash')} ريال\n📈 أسهم: {get_val(u, 'stocks')}\n🐾 نقاط المسابقات: {get_val(u, 'animals')}\n🤝 خويك بالفريق: {t} ✨")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.content == "كيفك": await message.reply("بخير وعافية الله يسلمك، أنت عساك دوم بخير؟ 🇸🇦✨")
    elif "ميرا" in message.content: await message.reply("لبيه؟ اؤمرني 🫡")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ علامك مستعجل؟ اصبر **{int(error.retry_after)} ثانية** 🏃‍♂️")

keep_alive()
bot.run(os.environ.get('TOKEN'))
