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
    'cash': {},      # رصيد الكاش
    'animals': {},   # نقاط الحيوانات
    'flags': {},     # نقاط الأعلام
    'stocks': {}     # عدد الأسهم المملوكة
}
stock_price = 50  # سعر السهم الحالي

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

@bot.event
async def on_ready(): print(f'ميرا جاهزة: {bot.user}')

# --- قائمة الأوامر ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    embed = discord.Embed(title="🎀 دليل أوامر ميرا المكتمل 🎀", color=0xffc0cb)
    embed.add_field(name="🎮 الألعاب:", value="• **حيوانات** | **اعلام**", inline=False)
    embed.add_field(name="📈 سوق الأسهم:", value="• **الأسهم** (السعر) | **شراء** [العدد] | **بيع** [العدد]", inline=False)
    embed.add_field(name="💰 الاقتصاد:", value="• **سحب** | **رصيدي** | **توب 10**", inline=False)
    await ctx.send(embed=embed)

# --- نظام الأسهم (الجديد) ---
@bot.command(name='الأسهم')
async def show_stocks(ctx):
    await ctx.reply(f"📊 سعر السهم الحالي: **{stock_price} ريال**")

@bot.command(name='شراء')
async def buy_stocks(ctx, count: int):
    cost = count * stock_price
    if get_val(ctx.author.id, 'cash') < cost: return await ctx.reply("❌ كاشك ما يكفي!")
    update_val(ctx.author.id, 'cash', -cost)
    update_val(ctx.author.id, 'stocks', count)
    await ctx.reply(f"🛒 اشتريت {count} سهم بنجاح!")

@bot.command(name='بيع')
async def sell_stocks(ctx, count: int):
    if get_val(ctx.author.id, 'stocks') < count: return await ctx.reply("❌ ما تملك هالعدد من الأسهم!")
    gain = count * stock_price
    update_val(ctx.author.id, 'stocks', -count)
    update_val(ctx.author.id, 'cash', gain)
    await ctx.reply(f"💰 بعت {count} سهم واستلمت {gain} ريال!")

# --- الألعاب والاقتصاد ---
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

@bot.command(name='سحب')
async def withdraw(ctx):
    update_val(ctx.author.id, 'cash', 500)
    await ctx.reply("💸 استلمت 500 ريال!")

@bot.command(name='رصيدي')
async def balance(ctx):
    uid = ctx.author.id
    await ctx.reply(f"🏦 **رصيدك:**\n💵 كاش: {get_val(uid, 'cash')}\n📈 أسهم: {get_val(uid, 'stocks')}\n🐾 حيوانات: {get_val(uid, 'animals')}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("هلا عيوني!")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ['TOKEN'])
