import discord
from discord.ext import commands
import os
import random
import asyncio
from flask import Flask
from threading import Thread

# --- نظام الحماية للبقاء متصلاً 24 ساعة ---
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

# قواعد البيانات (نقاط الألعاب والفلوس)
# ملاحظة: في النسخة المجانية، البيانات تصفّر عند إعادة تشغيل البوت
db = {
    'cash': {},      # رصيد المال
    'animals': {},   # نقاط لعبة الحيوانات
    'flags': {}      # نقاط لعبة الأعلام
}

def update_score(user_id, category, amount=1):
    uid = str(user_id)
    db[category][uid] = db[category].get(uid, 0) + amount

@bot.event
async def on_ready():
    print(f'ميرا جاهزة: {bot.user}')

# --- قائمة الأوامر ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    embed = discord.Embed(title="🎀 دليل أوامر ميرا المحدثة 🎀", color=0xffc0cb)
    embed.add_field(name="🎮 الألعاب:", value="• **حيوانات** ⇽ أسرع حرف حيوان\n• **اعلام** ⇽ خمن علم الدولة", inline=False)
    embed.add_field(name="💰 الاقتصاد:", value="• **سحب** ⇽ الحصول على 500 ريال\n• **رصيدي** ⇽ عرض كل نقاطك\n• **توب 10** ⇽ قائمة المتصدرين 🏆", inline=False)
    embed.set_footer(text="نادني بـ ميرا للسوالف ✨")
    await ctx.send(embed=embed)

# --- لعبة الحيوانات ---
@bot.command(name='حيوانات')
async def animals_game(ctx):
    letters = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
    char = random.choice(letters)
    await ctx.send(f"🐾 | أسرع شخص يكتب اسم **حيوان** يبدأ بحرف: **{char}**")

    def check(m): return m.channel == ctx.channel and not m.author.bot and m.content.strip().startswith(char)
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        update_score(msg.author.id, 'animals')
        await ctx.send(f"🎉 كفو! <@{msg.author.id}> جاوب صح. زادت نقاطك في الحيوانات! 🏆")
    except asyncio.TimeoutError:
        await ctx.send("⏰ انتهى الوقت وما حد عرف الجواب!")

# --- لعبة الأعلام ---
flags_dict = {"🇸🇦": "السعودية", "🇪🇬": "مصر", "🇰🇼": "الكويت", "🇦🇪": "الامارات", "🇶🇦": "قطر", "🇧跑": "البحرين", "🇴🇲": "عمان", "🇮🇶": "العراق"}
@bot.command(name='اعلام')
async def flags_game(ctx):
    flag, country = random.choice(list(flags_dict.items()))
    await ctx.send(f"🌍 | خمن اسم الدولة صاحب هذا العلم: {flag}")

    def check(m): return m.channel == ctx.channel and m.content.strip() == country
    try:
        msg = await bot.wait_for('message', check=check, timeout=20.0)
        update_score(msg.author.id, 'flags')
        await ctx.send(f"✅ صح! هذه دولة **{country}**. أحسنت <@{msg.author.id}> 🌟")
    except asyncio.TimeoutError:
        await ctx.send(f"💔 انتهى الوقت! الدولة كانت: {country}")

# --- نظام المال والتوب 10 ---
@bot.command(name='سحب')
async def withdraw(ctx):
    update_score(ctx.author.id, 'cash', 500)
    await ctx.reply("💸 تم سحب 500 ريال بنجاح!")

@bot.command(name='رصيدي')
async def my_balance(ctx):
    uid = str(ctx.author.id)
    c = db['cash'].get(uid, 0)
    a = db['animals'].get(uid, 0)
    f = db['flags'].get(uid, 0)
    await ctx.reply(f"🏦 **رصيد {ctx.author.display_name}:**\n💵 كاش: {c}\n🐾 حيوانات: {a}\n🌍 أعلام: {f}")

@bot.command(name='توب 10')
async def top_10(ctx):
    embed = discord.Embed(title="🏆 قائمة المتصدرين - Top 10", color=0xffd700)
    
    for category, name in [('cash', '💰 الأغنى (كاش)'), ('animals', '🐾 أذكياء الحيوانات'), ('flags', '🌍 خبراء الأعلام')]:
        sorted_users = sorted(db[category].items(), key=lambda x: x[1], reverse=True)[:10]
        val = ""
        for i, (uid, score) in enumerate(sorted_users, 1):
            val += f"{i}. <@{uid}> ⇽ **{score}**\n"
        embed.add_field(name=name, value=val if val else "لا يوجد بيانات بعد", inline=False)
    
    await ctx.send(embed=embed)

# --- نظام الردود التلقائية ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content:
        await message.reply(random.choice(["عيونها؟", "هلا، وش بغيت؟", "أسمعك يا عسل"]))
    await bot.process_commands(message)

# --- التشغيل ---
keep_alive()
bot.run(os.environ['TOKEN'])
