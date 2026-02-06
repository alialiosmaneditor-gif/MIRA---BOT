import discord
from discord.ext import commands, tasks
import os, random, asyncio, time
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

# --- قوائم البيانات الداخلية (عربي صافي) ---
arabic_words = ["مملكة", "سعودية", "اقتصاد", "تحدي", "ميرا", "برمجة", "طيارة", "مدرسة", "قهوة", "رياض"]

# --- إعدادات المتجر ---
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

# --- 📜 الدليل الشامل للأوامر (شرح مفصل) ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    guide = (
        "🎮 **مرحباً بك في دليل ميرا الاقتصادي الشامل!** 🇸🇦\n"
        "إليك شرح مفصل لكل ما تحتاجه لتصبح الهامور رقم 1:\n\n"
        
        "💰 **1. كيف تجمع المال؟ (الاقتصاد):**\n"
        "• `عمل` 💼: هي وسيلتك الأساسية، تعطيك راتباً كل **5 دقائق**. إذا كان حظك قوياً في اليانصيب، قد يتدبل راتبك!\n"
        "• `زرف` 🥷: (نظام الرد) إذا أردت المال السريع، **رد على رسالة أي شخص** واكتب 'زرف'. هناك مخاطرة! قد تنجح وتأخذ كاشه، أو تنقفط وتدفع غرامة 400 ريال.\n"
        "• `تحويل (المبلغ)` 💸: (نظام الرد) هل تريد دعم خويك؟ **رد على رسالته** واكتب 'تحويل 1000' مثلاً، وسيتم إرسال المبلغ من محفظتك لمحفظته.\n\n"
        
        "🏧 **2. حماية ثروتك (البنك والمتجر):**\n"
        "• `إيداع (المبلغ)` 🏦: أهم خطوة! الأموال في 'الكاش' معرضة للزرف. أودع مبالغك في البنك لتكون في أمان.\n"
        "• `سحب (المبلغ)` 🏧: لسحب أموالك من البنك واستخدامها في الشراء أو التحويل.\n"
        "• `متجر` 🛒: يعرض لك 'درع الحماية' ضد الزرف، و 'مفتاح الخزنة' لزيادة نجاح سرقاتك، ورتبة 'هامور' الفخمة.\n"
        "• `رصيدي` 💳: يعرض لك تفاصيل ثروتك (كاش، بنك، نقاط، ومميزات نشطة).\n\n"
        
        "🎲 **3. الحظ والمسابقات (الوقت 40 ثانية):**\n"
        "• `يانصيب` 🎰: ادفع 10,000 ريال واسحب تذكرة. الجوائز خرافية: كاش 30 ألف، أو ميزة 'الدبل المؤقت' للرواتب لمدة دقيقتين، أو الجائزة الكبرى: تدبيل كل كاشك الحالي!\n"
        "• `رياضيات` 🧮: حل المسائل الحسابية بسرعة. (الضرب يعطيك نقاطاً أكثر).\n"
        "• `عكس` 🔄: البوت يعطيك كلمة عربية، والمطلوب تكتب حروفها بالمقلوب بسرعة.\n"
        "• `أعلام` 🌍: خمن الدولة التي يمثلها العلم الظاهر.\n\n"
        
        "🏆 **4. التنافس:**\n"
        "• `توب 10` 💎: يعرض قائمة 'قاعة المشاهير' لأغنى 10 أشخاص في السيرفر حالياً.\n\n"
        "*نصيحة: دائماً أبقِ مالك في البنك، ولا تلعب اليانصيب إلا وأنت تملك فائضاً من المال!*"
    )
    await ctx.reply(guide)

# --- (بقية الأكواد: رياضيات، عكس، يانصيب، زرف، عمل، رصيدي - كما في الكود السابق) ---
@bot.command(name='عكس')
async def reverse_challenge(ctx):
    word = random.choice(arabic_words)
    reversed_w = word[::-1]
    await ctx.send(f"🔄 | أسرع واحد يعكس هالكلمة العربية: **{word}**\n*(معك 40 ثانية)* ⏱️")
    def check(m): return m.channel == ctx.channel and m.content.strip() == reversed_w
    try:
        msg = await bot.wait_for('message', check=check, timeout=40.0)
        update_val(msg.author.id, 'points', 1)
        await ctx.reply(f"🎉 بطل يا <@{msg.author.id}>! عكستها صح. ✨")
    except: await ctx.send(f"⏰ انتهى الوقت! كانت: {reversed_w}")

@bot.command(name='رياضيات')
async def math_challenge(ctx):
    num1, num2 = random.randint(1, 50), random.randint(1, 30)
    op = random.choice(['+', '-', '*'])
    if op == '+': res = num1 + num2
    elif op == '-': res = num1 - num2
    else: num1, num2 = random.randint(1, 10), random.randint(1, 10); res = num1 * num2
    await ctx.send(f"🧮 | كم ناتج: **{num1} {op} {num2}** ؟\n*(معك 40 ثانية)* ⏱️")
    def check(m): return m.channel == ctx.channel and m.content.strip() == str(res)
    try:
        msg = await bot.wait_for('message', check=check, timeout=40.0)
        update_val(msg.author.id, 'points', 1)
        await ctx.reply(f"🧠 كفو! الحل صح وهو (**{res}**).")
    except: await ctx.send(f"⏰ انتهى الوقت!")

@bot.command(name='يانصيب')
async def lottery(ctx):
    cost = 10000
    if get_val(ctx.author.id, 'cash') < cost: return await ctx.reply("❌ يبي لك 10,000 ريال! 🎟️")
    update_val(ctx.author.id, 'cash', -cost)
    await ctx.send("🎰 | جارِ سحب التذكرة... 🍀")
    await asyncio.sleep(2)
    chance = random.randint(1, 100)
    if chance <= 30:
        prize = random.randint(1, 100)
        if prize == 1:
            val = get_val(ctx.author.id, 'cash'); update_val(ctx.author.id, 'cash', val)
            await ctx.reply("🔥 **انفجار حظ!** تدبلت كل فلوسك! 🤑")
        elif prize <= 20:
            db['boost'][str(ctx.author.id)] = time.time() + 120
            await ctx.reply("⚡ **كفو!** رواتبك مدبولة لمدة دقيقتين! ⏳")
        else:
            update_val(ctx.author.id, 'cash', 30000)
            await ctx.reply("💰 **مبروك!** فزت بـ 30,000 ريال كاش! ✨")
    else: await ctx.reply("💔 خسرانة.. معوض خير!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "تحويل" in message.content and message.reference:
        try:
            amt = int(''.join(filter(str.isdigit, message.content)))
            target = (await message.channel.fetch_message(message.reference.message_id)).author
            if get_val(message.author.id, 'cash') < amt: return await message.reply("❌ كاشك ما يكفي!")
            update_val(message.author.id, 'cash', -amt); update_val(target.id, 'cash', amt)
            await message.reply(f"✅ تم تحويل **{amt:,} ريال** لـ {target.mention}! 🤝")
        except: pass
    if message.content == "زرف" and message.reference:
        target = (await message.channel.fetch_message(message.reference.message_id)).author
        if target == message.author: return
        if random.randint(1, 100) > 50:
            stolen = random.randint(100, 600)
            update_val(target.id, 'cash', -stolen); update_val(message.author.id, 'cash', stolen)
            await message.reply(f"🥷 زرفت من {target.mention} مبلغ **{stolen} ريال**! 😎")
        else:
            update_val(message.author.id, 'cash', -400); await message.reply("🚔 انقفطت! دفعت غرامة 400 ريال!")
    await bot.process_commands(message)

@bot.command(name='توب')
async def top_rich(ctx, arg=""):
    if arg == "10":
        sorted_data = sorted(db['cash'].items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير بالسيرفر:**\n\n"
        for i, (uid, bal) in enumerate(sorted_data): msg += f"{i+1}. <@{uid}> — **{bal:,} ريال** 💰\n"
        await ctx.reply(msg)
    else: await ctx.reply("اكتب `توب 10` 🐳")

@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    salary = random.randint(800, 1500)
    if str(ctx.author.id) in db['boost'] and time.time() < db['boost'][str(ctx.author.id)]: salary *= 2
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 جبت راتب **{salary} ريال**.. كفو! 💸")

@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    msg = f"🏦 **محفظتك:**\n💵 كاش: {get_val(u, 'cash'):,} | 🏧 بنك: {get_val(u, 'bank'):,} | 🐾 نقاط: {get_val(u, 'points')}"
    if str(u) in db['boost'] and time.time() < db['boost'][str(u)]: msg += "\n⚡ **ميزة التدبيل نشطة!** 🔥"
    await ctx.reply(msg)

@bot.command(name='إيداع')
async def deposit(ctx, amt: int):
    if get_val(ctx.author.id, 'cash') < amt: return await ctx.reply("❌ كاشك ما يكفي!")
    update_val(ctx.author.id, 'cash', -amt); update_val(ctx.author.id, 'bank', amt)
    await ctx.reply(f"🏦 تم إيداع **{amt:,} ريال** في البنك.")

@bot.command(name='سحب')
async def withdraw(ctx, amt: int):
    if get_val(ctx.author.id, 'bank') < amt: return await ctx.reply("❌ رصيدك بالبنك ما يكفي!")
    update_val(ctx.author.id, 'bank', -amt); update_val(ctx.author.id, 'cash', amt)
    await ctx.reply(f"🏧 تم سحب **{amt:,} ريال** لمحفظتك.")

keep_alive()
bot.run(os.environ.get('TOKEN'))
