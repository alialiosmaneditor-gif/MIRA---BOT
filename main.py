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

db = {
    'cash': {}, 'stocks': {}, 'points': {}, 'team_with': {},
    'last_stock_update': time.time(), 'main_channel': None
}

stock_price = 300
jobs = [{"name": "طيار 👨‍✈️", "min": 1200, "max": 2000}, {"name": "مبرمج 💻", "min": 900, "max": 1500}]

# --- بيانات الأعلام المحدثة ---
flags_levels = {
    "سهل": {"🇸🇦": "السعودية", "🇰🇼": "الكويت", "🇪🇬": "مصر"},
    "متوسط": {"🇲🇦": "المغرب", "🇯🇵": "اليابان", "🇧🇷": "البرازيل"},
    "صعب": {"🇧🇹": "بوتان", "🇰🇮": "كيريباتي"},
    "أسطوري 👑": {"🇻🇦": "الفاتيكان", "🇸🇿": "إسواتيني"}
}

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

# --- نظام الأسهم التلقائي ---
@tasks.loop(minutes=10)
async def change_stock_price():
    global stock_price
    old = stock_price
    stock_price = random.randint(250, 500)
    if db['main_channel']:
        channel = bot.get_channel(db['main_channel'])
        if channel:
            trend = "📈" if stock_price > old else "📉"
            await channel.send(f"📢 **البورصة تحركت!** السعر الجديد: **{stock_price} ريال** {trend}")

@bot.event
async def on_ready(): 
    print(f'ميرا جاهزة: {bot.user} ✅')
    change_stock_price.start()

# --- 📜 الأوامر المحدثة ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    embed = (
        "🎮 **تحديات ميرا المطورة:**\n\n"
        "🚩 `أعلام` : مستويات من سهل لـ أسطوري مع تلميحات 💡\n"
        "🔄 `عكس` : كلمات مشفرة ولا نهائية 🧩\n"
        "🐾 `حيوانات` : تحدي السرعة (جاوب بسرعة وتدبل نقاطك) ⚡\n"
        "🔢 `رياضيات` : مسابقة الحساب الذهني السريع 🧮\n"
        "💰 `عمل` | `زرف` | `توب` | `رصيدي` | `الأسهم`"
    )
    await ctx.reply(embed)

# --- مسابقة الأعلام مع تلميحات ---
@bot.command(name='أعلام')
async def flags_game(ctx):
    level = random.choice(list(flags_levels.keys()))
    flag, name = random.choice(list(flags_levels[level].items()))
    points = 5 if "أسطوري" in level else (3 if level == "صعب" else 1)
    
    await ctx.send(f"🌍 | **تحدي الأعلام ({level})**\nخمن الدولة: {flag}\n*(جائزة: {points} نقطة)* 💰")
    
    def check(m): return m.channel == ctx.channel and m.content.strip() == name
    try:
        msg = await bot.wait_for('message', check=check, timeout=15)
        update_val(msg.author.id, 'points', points)
        await ctx.send(f"🎉 بطل يا <@{msg.author.id}>! جبتها صح وهي **{name}** ✨")
    except asyncio.TimeoutError:
        await ctx.send(f"💡 تلميحات: الدولة تبدأ بحرف (**{name[0]}**) وتنتهي بـ (**{name[-1]}**)")
        try:
            msg = await bot.wait_for('message', check=check, timeout=10)
            update_val(msg.author.id, 'points', points)
            await ctx.send(f"🎉 أخيراً! <@{msg.author.id}> جابها صح 👏")
        except: await ctx.send(f"⏰ انتهى الوقت! كانت **{name}**")

# --- مسابقة عكس مع تشفير ---
@bot.command(name='عكس')
async def reverse_game(ctx):
    try:
        r = requests.get("https://raw.githubusercontent.com")
        word = random.choice([w for w in r.text.split() if 3 <= len(w) <= 5])
    except: word = "ميرا"
    
    encrypted = " . ".join(list(word)) # تشفير بسيط بوضع نقاط بين الحروف
    await ctx.send(f"🔄 | فك التشفير واعكس الكلمة: **[ {encrypted} ]**")
    def check(m): return m.channel == ctx.channel and m.content.strip() == word[::-1]
    try:
        msg = await bot.wait_for('message', check=check, timeout=15)
        update_val(msg.author.id, 'points', 2)
        await ctx.send(f"⚡ ذكاء خارق يا <@{msg.author.id}>! عكستها صح 💎")
    except: await ctx.send(f"⏰ راحت عليك! العكس كان: **{word[::-1]}**")

# --- مسابقة الرياضيات ---
@bot.command(name='رياضيات')
async def math_game(ctx):
    a, b = random.randint(1, 20), random.randint(1, 20)
    op = random.choice(['+', '-', '*'])
    result = a + b if op == '+' else (a - b if op == '-' else a * b)
    
    await ctx.send(f"🧮 | أسرع عبقري يحلها: **{a} {op} {b} = ؟**")
    def check(m): return m.channel == ctx.channel and m.content.strip() == str(result)
    try:
        start_time = time.time()
        msg = await bot.wait_for('message', check=check, timeout=15)
        elapsed = time.time() - start_time
        pts = 2 if elapsed < 5 else 1 # مكافأة سرعة
        update_val(msg.author.id, 'points', pts)
        await ctx.send(f"🧠 كفو يا دافور <@{msg.author.id}>! الحل صح وأخذت {pts} نقطة 🚀")
    except: await ctx.send(f"⏰ انتهى الوقت! الحل هو **{result}**")

# --- الأوامر العامة ---
@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    await ctx.reply(f"🏦 **محفظتك:**\n💵 كاش: {get_val(u, 'cash')} ريال\n📈 أسهم: {get_val(u, 'stocks')}\n🐾 نقاط: {get_val(u, 'points')} ✨")

@bot.command(name='توب')
async def top_players(ctx):
    if not db['points']: return await ctx.reply("لا يوجد نقاط مسجلة حالياً! 😶")
    sorted_pts = sorted(db['points'].items(), key=lambda x: x[1], reverse=True)[:5]
    msg = "🏆 **أساطير المسابقات (Top 5):**\n"
    for i, (uid, p) in enumerate(sorted_pts):
        try:
            user = await bot.fetch_user(int(uid))
            msg += f"{i+1}. {user.name} — {p} نقطة ✨\n"
        except: continue
    await ctx.reply(msg)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("لبيه؟ اؤمرني بالايموجيات اللي تحبها 🫡✨")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('TOKEN'))
