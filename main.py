import discord
from discord.ext import commands, tasks
import os
import random
import asyncio
import time
import requests
from flask import Flask
from threading import Thread

# --- نظام البقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "ميرا متصلة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.start()

# --- إعدادات البوت ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# قاعدة بيانات مؤقتة
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

# --- بيانات الأعلام مقسمة حسب المستويات ---
flags_levels = {
    "سهل": {
        "🇸🇦": "السعودية", "🇰🇼": "الكويت", "🇦🇪": "الإمارات", "🇶🇦": "قطر", "🇴🇲": "عمان",
        "🇪🇬": "مصر", "🇮🇶": "العراق", "🇯🇴": "الأردن", "🇵🇸": "فلسطين", "🇺🇸": "امريكا"
    },
    "متوسط": {
        "🇹🇳": "تونس", "🇲🇦": "المغرب", "🇩🇿": "الجزائر", "🇸🇾": "سوريا", "🇱🇧": "لبنان",
        "🇹🇷": "تركيا", "🇯🇵": "اليابان", "🇨🇳": "الصين", "🇫🇷": "فرنسا", "🇧🇷": "البرازيل",
        "🇩🇪": "ألمانيا", "🇮🇹": "ايطاليا", "🇪🇸": "اسبانيا", "🇷🇺": "روسيا", "🇰🇷": "كوريا الجنوبية"
    },
    "صعب": {
        "🇰🇮": "كيريباتي", "🇲🇿": "موزمبيق", "🇧🇹": "بوتان", "🇦🇸": "ساموا",
        "🇱🇸": "ليسوتو", "🇸🇿": "إسواتيني", "🇬🇾": "غيانا", "🇰🇲": "جزر القمر"
    }
}

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

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
            await channel.send(f"📢 **تحديث سوق الأسهم:**\nسعر السهم صار بـ **{stock_price} ريال** ({trend})")

@bot.event
async def on_ready(): 
    print(f'ميرا جاهزة: {bot.user}')
    if not change_stock_price.is_running():
        change_stock_price.start()

# --- مسابقة أعلام بمستويات عشوائية ---
@bot.command(name='أعلام')
async def flags_game(ctx):
    db['main_channel'] = ctx.channel.id
    # اختيار مستوى عشوائي
    level = random.choice(["سهل", "متوسط", "صعب"])
    # اختيار علم من المستوى المحدد
    flag, name = random.choice(list(flags_levels[level].items()))
    
    points = 3 if level == "صعب" else 1 # الصعب يعطي نقاط أكثر
    
    await ctx.send(f"🌍 | **تحدي الأعلام (مستوى: {level})**\nأسرع واحد يعرف علم هالدولة: {flag}")
    
    def check(m): return m.channel == ctx.channel and m.content.strip() == name
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
        update_val(msg.author.id, 'animals', points)
        res = f"🎉 كفووو <@{msg.author.id}>! جبتها وهي **{name}** وأخذت **{points}** نقطة."
        
        if str(msg.author.id) in db['team_with']:
            update_val(db['team_with'][str(msg.author.id)], 'animals', points)
            res += " وخويك بالفريق تدبلت له النقاط! 🤝"
        await ctx.send(res)
    except:
        await ctx.send(f"⏰ محد عرفها! هذي كانت **{name}**.")

# --- بقية الأوامر (نفس الكود السابق مع الاحتفاظ بخصائصك) ---
@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    db['main_channel'] = ctx.channel.id
    job = random.choice(jobs)
    salary = random.randint(job['min'], job['max'])
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 اشتغلت **{job['name']}** وعطوك **{salary} ريال**.. كفو! 💸")

@bot.command(name='زرف')
@commands.cooldown(1, 300, commands.BucketType.user)
async def rob(ctx, member: discord.Member = None):
    if not member or member == ctx.author: return await ctx.reply("من تبي تزرف؟ منشن ضحية! 😂")
    if get_val(member.id, 'cash') < 500: return await ctx.reply("هذا طفران ما يسوى تعب الزرف.. 😅")
    if random.randint(1, 100) > 50:
        stolen = random.randint(100, 400)
        update_val(member.id, 'cash', -stolen); update_val(ctx.author.id, 'cash', stolen)
        await ctx.reply(f"🥷 كفو يا شنب! زرفت من {member.mention} مبلغ **{stolen} ريال**! 😎")
    else:
        update_val(ctx.author.id, 'cash', -200)
        await ctx.reply(f"🤦‍♂️ انقفطت يا خايب ودفعت غرامة 200 ريال!")

@bot.command(name='عكس')
async def reverse_game(ctx):
    try:
        r = requests.get("https://raw.githubusercontent.com")
        word = random.choice([w for w in r.text.split() if 3 <= len(w) <= 6])
    except: word = "اقتصاد"
    reversed_w = word[::-1]
    await ctx.send(f"🔄 | أسرع واحد يعكس: **{word}**")
    def check(m): return m.channel == ctx.channel and m.content.strip() == reversed_w
    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
        update_val(msg.author.id, 'animals', 1)
        await ctx.send(f"🎉 جبتها يا بطل <@{msg.author.id}>!")
    except: await ctx.send(f"⏰ انتهى الوقت! كانت: {reversed_w}")

@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    t = f"<@{db['team_with'][str(u)]}>" if str(u) in db['team_with'] else "سنجل"
    await ctx.reply(f"🏦 **محفظتك:**\n💵 كاش: {get_val(u, 'cash')}\n📈 أسهم: {get_val(u, 'stocks')}\n🐾 نقاط: {get_val(u, 'animals')}\n🤝 فريقك: {t}")

@bot.command(name='الأوامر')
async def help_menu(ctx):
    await ctx.reply("🎮 **أوامر ميرا:** `عمل` | `زرف` | `أعلام` | `عكس` | `حيوانات` | `الأسهم` | `رصيدي` | `فريق`")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.content == "كيفك": await message.reply("بخير الله يسلمك، عساك دوم طيب؟ 🇸🇦")
    elif "ميرا" in message.content: await message.reply("لبيه؟ 🫡")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ اصبر يا وحش باقي لك **{int(error.retry_after)} ثانية**.")

keep_alive()
bot.run(os.environ.get('TOKEN'))
