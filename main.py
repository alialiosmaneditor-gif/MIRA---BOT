import discord
from discord.ext import commands
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
stock_price = 50 

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

@bot.event
async def on_ready(): print(f'ميرا جاهزة: {bot.user}')

# --- معالجة أخطاء الكول داون (وقت الانتظار) ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = int(error.retry_after)
        await ctx.reply(f"⏳ | اهدأ قليلاً! يمكنك السحب بعد **{seconds}** ثانية.")

# --- الأوامر ---
@bot.command(name='سحب')
@commands.cooldown(1, 120, commands.BucketType.user) # سحب واحد كل 120 ثانية
async def withdraw(ctx):
    update_val(ctx.author.id, 'cash', 500)
    await ctx.reply("💸 تم سحب 500 ريال بنجاح! نراكم بعد دقيقتين.")

@bot.command(name='الأسهم')
async def show_stocks(ctx):
    await ctx.reply(f"📊 سعر السهم الحالي: **{stock_price} ريال**")

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
