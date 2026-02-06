import discord
from discord.ext import commands, tasks # أضفنا tasks للتوقيت
import os
import random
import asyncio
from flask import Flask
from threading import Thread

# --- نظام الحماية للبقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "ميرا متصلة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.start()

# --- إعدادات ميرا ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# قاعدة البيانات (مؤقتة)
db = {
    'cash': {},      
    'animals': {},   
    'flags': {},     
    'stocks': {}     
}
stock_price = 300 # السعر الابتدائي

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

# --- نظام تغيير سعر الأسهم تلقائياً ---
@tasks.loop(minutes=10)
async def change_stock_price():
    global stock_price
    stock_price = random.randint(250, 500)
    print(f"تم تحديث سعر السهم إلى: {stock_price}")

@bot.event
async def on_ready(): 
    print(f'ميرا جاهزة: {bot.user}')
    change_stock_price.start() # بدء تشغيل حلقة تحديث الأسعار عند تشغيل البوت

# --- معالجة أخطاء الكول داون ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = int(error.retry_after)
        await ctx.reply(f"⏳ | اهدأ قليلاً! يمكنك السحب بعد **{seconds}** ثانية.")

# --- أمر الأوامر ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    help_text = (
        "📜 **قائمة أوامر ميرا:**\n\n"
        "💰 `سحب` - للحصول على 500 ريال\n"
        f"📊 `الأسهم` - السعر الحالي (**{stock_price}** ريال)\n"
        "🛒 `شراء سهم` - لشراء سهم بالسعر الحالي\n"
        "💰 `بيع سهم` - لبيع سهم بالسعر الحالي\n"
        "🏦 `رصيدي` - عرض أموالك وممتلكاتك\n"
        "🐾 `حيوانات` - مسابقة أسرع كتابة"
    )
    await ctx.reply(help_text)

# --- نظام البيع والشراء ---
@bot.command(name='شراء')
async def buy_stock(ctx, item: str = ""):
    if item != "سهم":
        return await ctx.reply("❌ اكتب: `شراء سهم` لشراء سهم واحد.")
    
    uid = ctx.author.id
    if get_val(uid, 'cash') < stock_price:
        return await ctx.reply(f"❌ ما عندك كاش كافي! السعر الحالي {stock_price} ريال.")
    
    update_val(uid, 'cash', -stock_price)
    update_val(uid, 'stocks', 1)
    await ctx.reply(f"✅ تم شراء سهم بـ **{stock_price}** ريال! رصيدك من الأسهم: {get_val(uid, 'stocks')}")

@bot.command(name='بيع')
async def sell_stock(ctx, item: str = ""):
    if item != "سهم":
        return await ctx.reply("❌ اكتب: `بيع سهم` لبيع سهم واحد.")
    
    uid = ctx.author.id
    if get_val(uid, 'stocks') < 1:
        return await ctx.reply("❌ ما عندك أسهم تبيعها!")
    
    update_val(uid, 'stocks', -1)
    update_val(uid, 'cash', stock_price)
    await ctx.reply(f"✅ بعت سهم بـ **{stock_price}** ريال! رصيدك الكاش الآن: {get_val(uid, 'cash')}")

# --- باقي الأوامر ---
@bot.command(name='سحب')
@commands.cooldown(1, 120, commands.BucketType.user)
async def withdraw(ctx):
    update_val(ctx.author.id, 'cash', 500)
    await ctx.reply("💸 تم سحب 500 ريال بنجاح!")

@bot.command(name='الأسهم')
async def show_stocks(ctx):
    await ctx.reply(f"📊 سعر السهم الحالي: **{stock_price} ريال**\n(يتغير السعر كل 10 دقائق)")

@bot.command(name='رصيدي')
async def balance(ctx):
    uid = ctx.author.id
    await ctx.reply(f"🏦 **رصيدك:**\n💵 كاش: {get_val(uid, 'cash')}\n📈 أسهم: {get_val(uid, 'stocks')}\n🐾 حيوانات: {get_val(uid, 'animals')}")

@bot.command(name='حيوانات')
async def animals(ctx):
    char = random.choice("أبتثجحخدذرزسشصضطظعغفقكلمنهوي")
    await ctx.send(f"🐾 | أسرع حيوان يبدأ بحرف: **{char}**")
    def check(m): return m.channel == ctx.channel and not m.author.bot and m.content.strip().startswith(char)
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        update_val(msg.author.id, 'animals', 1)
        await ctx.send(f"🎉 كفو <@{msg.author.id}>!")
    except: await ctx.send("⏰ انتهى الوقت!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("هلا عيوني!")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ['TOKEN'])
