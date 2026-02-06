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
    'team_with': {}, # تم تغيير المسمى من متزوج إلى فريق
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

# --- الأوامر المحدثة ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    help_text = (
        "🎮 **مرحباً بك في عالم ميرا الاقتصادي!**\n\n"
        "💰 **الاقتصاد:**\n"
        "• `عمل`: للحصول على راتب وظيفة.\n"
        "• `الأسهم`: لعرض سعر السوق.\n"
        "• `شراء سهم` / `بيع سهم`: للتداول.\n\n"
        "👥 **نظام الفريق:**\n"
        "• `فريق @الشخص (المبلغ)`: لدعوة شخص لفريقك مقابل مبلغ مالي. (الفوز في المسابقات مشترك!).\n\n"
        "🐾 **المسابقات:**\n"
        "• `حيوانات`: أسرع واحد يكتب اسم حيوان يفوز.\n\n"
        "💳 **المحفظة:**\n"
        "• `رصيدي`: عرض الكاش، الأسهم، وشريكك في الفريق."
    )
    await ctx.reply(help_text)

# --- العمل ---
@bot.command(name='عمل')
@commands.cooldown(1, 120, commands.BucketType.user)
async def work(ctx):
    job = random.choice(jobs)
    salary = random.randint(job['min'], job['max'])
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 اشتغلت **{job['name']}** وعطوك راتب **{salary} ريال** 💵")

# --- الأسهم ---
@bot.command(name='الأسهم')
async def show_stocks(ctx):
    remaining = 600 - (time.time() - db['last_stock_update'])
    m, s = divmod(int(remaining), 60)
    await ctx.reply(f"📊 سعر السهم: **{stock_price} ريال**\n⏳ التحديث القادم: **{m}د و {s}ث**")

@bot.command(name='شراء')
async def buy(ctx, item=""):
    if item != "سهم": return await ctx.reply("اكتب: `شراء سهم`")
    if get_val(ctx.author.id, 'cash') < stock_price: return await ctx.reply("محفظتك فارغة!")
    update_val(ctx.author.id, 'cash', -stock_price)
    update_val(ctx.author.id, 'stocks', 1)
    await ctx.reply(f"✅ تم الشراء! تملك الآن: {get_val(ctx.author.id, 'stocks')} سهم.")

@bot.command(name='بيع')
async def sell(ctx, item=""):
    if item != "سهم": return await ctx.reply("اكتب: `بيع سهم`")
    if get_val(ctx.author.id, 'stocks') < 1: return await ctx.reply("لا تملك أسهم لبيعها!")
    update_val(ctx.author.id, 'stocks', -1)
    update_val(ctx.author.id, 'cash', stock_price)
    await ctx.reply(f"✅ بعت سهم بـ {stock_price}! كاشك الآن: {get_val(ctx.author.id, 'cash')}")

# --- نظام الفريق (بديل الزواج) ---
@bot.command(name='فريق')
async def join_team(ctx, member: discord.Member = None, amount: int = 0):
    if not member or amount <= 0: return await ctx.reply("اكتب: `فريق @الشخص (المبلغ)`")
    if str(ctx.author.id) in db['team_with']: return await ctx.reply("أنت بالفعل في فريق!")
    if get_val(ctx.author.id, 'cash') < amount: return await ctx.reply("ليس لديك هذا المبلغ لدعم الفريق!")

    await ctx.send(f"🤝 {member.mention}، هل تقبل الانضمام لفريق {ctx.author.mention} مقابل {amount} ريال؟ (أقبل/أرفض)")
    def check(m): return m.author == member and m.channel == ctx.channel and m.content in ["أقبل", "أرفض"]
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
        if msg.content == "أقبل":
            update_val(ctx.author.id, 'cash', -amount)
            update_val(member.id, 'cash', amount)
            db['team_with'][str(ctx.author.id)] = member.id
            db['team_with'][str(member.id)] = ctx.author.id
            await ctx.send("🔥 تم تكوين الفريق بنجاح! الآن نقاط المسابقات مشتركة!")
        else: await ctx.send("تم رفض الطلب.. ❌")
    except: await ctx.send("انتهى وقت الطلب!")

# --- المسابقات ---
@bot.command(name='حيوانات')
async def animals(ctx):
    char = random.choice("أبتثجحخدذرزسشصضطظعغفقكلمنهوي")
    await ctx.send(f"🐾 | أسرع حيوان يبدأ بحرف: **{char}**")
    def check(m): return m.channel == ctx.channel and not m.author.bot and m.content.strip().startswith(char)
    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
        update_val(msg.author.id, 'animals', 1)
        res = f"🎉 بطل <@{msg.author.id}> فاز بنقطة!"
        
        # إذا كان الفائز في فريق، يحصل زميله على نقطة أيضاً
        if str(msg.author.id) in db['team_with']:
            partner = db['team_with'][str(msg.author.id)]
            update_val(partner, 'animals', 1)
            res += f" ونقطة إضافية لزميله في الفريق <@{partner}>! 🤝"
            
        await ctx.send(res)
    except: await ctx.send("⏰ انتهى الوقت ولم يعرف أحد!")

# --- الرصيد ---
@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    t = f"<@{db['team_with'][str(u)]}>" if str(u) in db['team_with'] else "لا يوجد"
    await ctx.reply(f"🏦 **محفظتك:**\n💵 كاش: {get_val(u, 'cash')}\n📈 أسهم: {get_val(u, 'stocks')}\n🐾 نقاط: {get_val(u, 'animals')}\n👥 الفريق: {t}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        m, s = divmod(int(error.retry_after), 60)
        await ctx.reply(f"⏳ ارتاح قليلاً! انتظر **{m}د و {s}ث**.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("هلا، كيف أساعدك؟")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ.get('TOKEN'))
