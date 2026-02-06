import discord
from discord.ext import commands, tasks
import os
import random
import asyncio
import time
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
    'last_stock_update': time.time()
}

stock_price = 300
jobs = [
    {"name": "طبيب 👨‍⚕️", "min": 800, "max": 1200},
    {"name": "مهندس 👷", "min": 700, "max": 1000},
    {"name": "مبرمج 💻", "min": 900, "max": 1500},
    {"name": "طيار 👨‍✈️", "min": 1200, "max": 2000},
    {"name": "معلم 👨‍🏫", "min": 500, "max": 800},
    {"name": "طباخ 👨‍🍳", "min": 400, "max": 700}
]

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt):
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

@tasks.loop(minutes=10)
async def change_stock_price():
    global stock_price
    stock_price = random.randint(250, 500)
    db['last_stock_update'] = time.time()

@bot.event
async def on_ready():
    print(f'ميرا جاهزة: {bot.user}')
    if not change_stock_price.is_running():
        change_stock_price.start()

# --- العمل (وقت الانتظار: 5 دقائق) ---
@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    job = random.choice(jobs)
    salary = random.randint(job['min'], job['max'])
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 اشتغلت **{job['name']}** وعطوك راتب **{salary} ريال** 💵")

# --- الزرف (وقت الانتظار: 5 دقائق) ---
# يمكنك إضافة كود لأمر "الزرف" هنا مع cooldown لمدة 5 دقائق (300 ثانية)
@bot.command(name='زرف')
@commands.cooldown(1, 300, commands.BucketType.user)
async def rob(ctx, member: discord.Member = None):
    # أضف هنا منطق أمر الزرف الخاص بك
    pass # placeholder

# --- بقية الأوامر الاقتصادية ---
@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    t = f"<@{db['team_with'][str(u)]}>" if str(u) in db['team_with'] else "لا يوجد"
    await ctx.reply(f"🏦 **محفظتك:**\n💵 كاش: {get_val(u, 'cash')}\n📈 أسهم: {get_val(u, 'stocks')}\n🐾 نقاط: {get_val(u, 'animals')}\n👥 الفريق: {t}")

@bot.command(name='الأوامر')
async def help_menu(ctx):
    await ctx.reply(
        "🎮 **أوامر ميرا المحدثة:**\n"
        "💰 `عمل`: تشتغل كل 5 دقائق.\n"
        "🥷 `زرف @الشخص`: تزرف أحد كل 5 دقائق.\n"
        "🤝 `فريق @الشخص (مبلغ)`: تسوي تيم.\n"
        "📊 `الأسهم` / `شراء سهم` / `بيع سهم`.\n"
        "🐾 `حيوانات`: مسابقة الحروف."
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        m, s = divmod(int(error.retry_after), 60)
        await ctx.reply(f"⏳ اصبر يا وحش! باقي لك **{m}د و {s}ث**.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("هلا، اؤمر؟")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('TOKEN'))
