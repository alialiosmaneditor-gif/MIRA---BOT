import discord
from discord.ext import commands, tasks
import os, random, asyncio, time, requests
from flask import Flask
from threading import Thread

# --- نظام البقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "ميرا المتطورة جاهزة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# --- قاعدة بيانات مطورة ---
db = {
    'cash': {}, 'bank': {}, 'points': {}, 'items': {}, 
    'team_with': {}, 'boost': {}, 'main_channel': None
}

# --- إعدادات المتجر واليانصيب ---
store_items = {
    "🛡️ درع حماية": {"price": 10000, "desc": "يحميك من الزرف 🛡️"},
    "🔑 مفتاح الخزنة": {"price": 30000, "desc": "يزيد فرصة نجاح زرفك 🔑"},
    "🌟 رتبة هامور": {"price": 600000, "desc": "رتبة الهوامير الفخمة 🐳"}
}

def get_val(uid, cat): return db[cat].get(str(uid), 0)
def update_val(uid, cat, amt): 
    uid = str(uid)
    db[cat][uid] = db[cat].get(uid, 0) + amt

@bot.event
async def on_ready():
    print(f"تم تشغيل ميرا بنجاح: {bot.user} ✅")

# --- 📜 قائمة الأوامر المنسقة ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    msg = (
        "👋 **هلا بك في عالم ميرا! إليك الأوامر المحدثة:**\n\n"
        "💰 **الاقتصاد (بالرد):**\n"
        "• `تحويل (المبلغ)` 💸 : رد على شخص لتحويل الكاش.\n"
        "• `زرف` 🥷 : رد على شخص لزرفه.\n"
        "• `توب 10` 🏆 : عرض أغنى 10 هوامير بالسيرفر.\n\n"
        "🎟️ **نظام اليانصيب:**\n"
        "• `يانصيب` : جرب حظك بـ **10,000 ريال**! 🎰\n\n"
        "🎮 **المسابقات (الوقت 40 ثانية):**\n"
        "• `رياضيات` 🧮 : تحدي الحساب الذهني السريع (جديد! 🔥)\n"
        "• `أعلام` 🌍 : خمن علم الدولة.\n"
        "• `حيوانات` 🐾 : أسرع واحد يكتب اسم الحيوان.\n\n"
        "🏧 **البنك والمتجر:**\n"
        "• `إيداع` | `سحب` | `متجر` | `رصيدي` 💎"
    )
    await ctx.reply(msg)

# --- 🧮 تحدي الرياضيات المطور (بديل العكس) ---
@bot.command(name='رياضيات')
async def math_challenge(ctx):
    # إنشاء مسألة عشوائية
    num1 = random.randint(1, 50)
    num2 = random.randint(1, 30)
    operator = random.choice(['+', '-', '*'])
    
    if operator == '+': result = num1 + num2
    elif operator == '-': result = num1 - num2
    else: # ضرب
        num1 = random.randint(1, 12) # تصغير الأرقام في الضرب ليكون ممتعاً
        num2 = random.randint(1, 12)
        result = num1 * num2

    await ctx.send(f"🧮 | **أسرع دافور يحلها:**\nكم ناتج: **{num1} {operator} {num2}** ؟\n*(معك 40 ثانية للحل)* ⏱️")

    def check(m):
        return m.channel == ctx.channel and m.content.strip() == str(result) and not m.author.bot

    try:
        msg = await bot.wait_for('message', check=check, timeout=40.0)
        points = 2 if operator == '*' else 1 # الضرب يعطي نقاط أكثر
        update_val(msg.author.id, 'points', points)
        await ctx.reply(f"🧠 **عبقري!** <@{msg.author.id}> جاب الحل صح وهو (**{result}**) وفاز بـ {points} نقطة! ✨")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ **انتهى الوقت!** محد عرف يحلها.. الحل كان (**{result}**) 🧐")

# --- 🎰 نظام اليانصيب ---
@bot.command(name='يانصيب')
async def lottery(ctx):
    cost = 10000
    if get_val(ctx.author.id, 'cash') < cost:
        return await ctx.reply("❌ يبي لك 10,000 ريال عشان تشتري تذكرة! 🎟️")
    
    update_val(ctx.author.id, 'cash', -cost)
    await ctx.send("🎰 | جارِ سحب التذكرة... يا رب حظك يكسر الصخر! 🍀")
    await asyncio.sleep(2)
    
    win_chance = random.randint(1, 100)
    if win_chance <= 30: # نسبة الفوز 30%
        prize_type = random.randint(1, 100)
        if prize_type == 1: # جائزة 1% تدبيل كامل
            current_cash = get_val(ctx.author.id, 'cash')
            update_val(ctx.author.id, 'cash', current_cash)
            await ctx.reply("🔥 **يا ساتر!!** فزت بجائزة الـ 1% وتدبلت كل فلوسك الحين! 🤑💎")
        elif prize_type <= 20: # دبل مؤقت
            db['boost'][str(ctx.author.id)] = time.time() + 120
            await ctx.reply("⚡ **كفو!** فزت بميزة (الدبل المؤقت)؛ أي راتب يجي من العمل بيتدبل لمدة دقيقتين! ⏳")
        else: # كاش 30 ألف
            update_val(ctx.author.id, 'cash', 30000)
            await ctx.reply("💰 **مبروك!** فزت بـ **30,000 ريال** كاش! ✨")
    else:
        await ctx.reply("💔 حظ أوفر.. التذكرة طلعت خسرانة! 🎟️")

# --- 🥷 نظام الرد (التحويل والزرف) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # تحويل بالرد
    if "تحويل" in message.content and message.reference:
        try:
            amt = int(''.join(filter(str.isdigit, message.content)))
            original = await message.channel.fetch_message(message.reference.message_id)
            target = original.author
            if get_val(message.author.id, 'cash') < amt: return await message.reply("❌ فلوسك ما تكفي! 💸")
            update_val(message.author.id, 'cash', -amt); update_val(target.id, 'cash', amt)
            await message.reply(f"✅ تم تحويل **{amt:,} ريال** لـ {target.mention}! 🤝")
        except: pass

    # زرف بالرد
    if message.content == "زرف" and message.reference:
        original = await message.channel.fetch_message(message.reference.message_id)
        target = original.author
        if target == message.author: return await message.reply("تزرف نفسك؟ 😂")
        if get_val(target.id, 'cash') < 500: return await message.reply("هذا طفران لا توجع قلبه 😅")
        
        if random.randint(1, 100) > 50:
            stolen = random.randint(100, 600)
            update_val(target.id, 'cash', -stolen); update_val(message.author.id, 'cash', stolen)
            await message.reply(f"🥷 **كفو!** زرفت من {target.mention} مبلغ **{stolen} ريال**! 😎💰")
        else:
            update_val(message.author.id, 'cash', -400)
            await message.reply("🚔 **انقفطت!** دفعت غرامة 400 ريال! 🚨")

    await bot.process_commands(message)

# --- 🏆 توب 10 ---
@bot.command(name='توب')
async def top_rich(ctx, arg=""):
    if arg == "10":
        sorted_data = sorted(db['cash'].items(), key=lambda x: x, reverse=True)[:10]
        msg = "🏆 **قائمة أغنى 10 هوامير في السيرفر:**\n\n"
        for i, (uid, bal) in enumerate(sorted_data):
            msg += f"{i+1}. <@{uid}> — **{bal:,} ريال** 💰\n"
        await ctx.reply(msg)
    else: await ctx.reply("اكتب `توب 10` عشان تشوف القائمة! 🐳")

# --- 🏧 الرصيد والعمل ---
@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    salary = random.randint(800, 1500)
    if str(ctx.author.id) in db['boost'] and time.time() < db['boost'][str(ctx.author.id)]:
        salary *= 2
        await ctx.reply(f"💼 اشتغلت وجبت راتب **مدبول**: {salary} ريال! ⚡🔥")
    else:
        await ctx.reply(f"💼 اشتغلت وعطوك راتب **{salary} ريال**.. كفو! 💸")
    update_val(ctx.author.id, 'cash', salary)

@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    msg = f"🏦 **محفظتك يا بطل:**\n💵 كاش: {get_val(u, 'cash'):,} ريال\n🏧 بنك: {get_val(u, 'bank'):,} ريال\n🐾 نقاط: {get_val(u, 'points')}"
    if str(u) in db['boost'] and time.time() < db['boost'][str(u)]:
        msg += "\n⚡ **ميزة التدبيل:** فعالة حالياً! 🔥"
    await ctx.reply(msg)

keep_alive()
bot.run(os.environ.get('TOKEN'))
