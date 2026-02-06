import discord
from discord.ext import commands, tasks
import os, random, asyncio, json, time
from flask import Flask
from threading import Thread
from datetime import datetime

# --- 🌐 تشغيل السيرفر (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Mira Advanced System v2026: Online 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 📁 إعدادات البوت والقاعدة ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

DB_FILE = "database.json"
STOCKS_CH_ID = 123456789012345678 # ⚠️ ضع آيدي قناة الأسهم هنا

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f: return json.load(f)
    return {'cash': {}, 'bank': {}, 'marry': {}, 'job': {}, 'exp': {}}

db = load_db()

def save_db():
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def get_v(uid, cat, default=0):
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = default
    return db[cat][uid]

def add_v(uid, cat, amt):
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = 0
    db[cat][uid] += amt
    save_db()

# --- 🎰 نظام الياناصيب المطور ---
@bot.command(name='ياناصيب')
async def lottery(ctx):
    user_id = ctx.author.id
    price = 100000
    prize = 400000
    
    if get_v(user_id, 'cash') < price:
        return await ctx.reply(f"رصيدك ما يكفي لشراء التذكرة ❌")

    options = "الخيارات المتاحة: اكتب **[متأكد]** للشراء أو **[الغاء]** للتراجع ✅"
    await ctx.reply(f"سعر التذكرة `{price:,}` ريال، والجائزة `{prize:,}` ريال. نسبة فوزك 20% 🎰\n{options}")

    def check(m): return m.author == ctx.author and m.content in ["متأكد", "الغاء"]
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "متأكد":
            add_v(user_id, 'cash', -price)
            loading = await ctx.send("🎰 | جاري سحب التذكرة...")
            await asyncio.sleep(2)
            if random.random() <= 0.20:
                add_v(user_id, 'cash', prize)
                await loading.edit(content=f"مبروووك! انفجرت الجائزة بوجهك وفزت بـ `{prize:,}` ريال 🎊")
            else:
                await loading.edit(content=f"للأسف خسرنا التذكرة، معوض خير يا وحش 💸")
        else:
            await ctx.send("تم إلغاء العملية بناءً على طلبك 🚫")
    except asyncio.TimeoutError:
        await ctx.send("انتهى وقت الرد، ميرا أغلقت الملف ⌛")

# --- 💔 نظام الخلع ---
@bot.command(name='خلع')
async def divorce(ctx):
    uid = str(ctx.author.id)
    if uid not in db['marry']:
        return await ctx.reply("أنت لست متزوجاً أصلاً تبي تخلع مين؟ 😂")
    
    partner_id = db['marry'][uid]
    options = "الخيارات المتاحة: اكتب **[متأكد]** للخلع أو **[الغاء]** للتراجع ✅"
    await ctx.reply(f"هل أنت متأكد من قرار الخلع من <@{partner_id}>؟ 💔\n{options}")

    def check(m): return m.author == ctx.author and m.content in ["متأكد", "الغاء"]
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "متأكد":
            db['marry'].pop(uid, None)
            db['marry'].pop(str(partner_id), None)
            save_db()
            await ctx.send(f"تم الانفصال رسمياً.. الله يكتب اللي فيه الخير 🥀")
        else:
            await ctx.send("تم التراجع، الله يديم المودة 🤍")
    except asyncio.TimeoutError:
        await ctx.send("انتهى الوقت، ميرا كنسلت الطلب ⌛")

# --- 🥷 نظام الرد (تحويل + زرف) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.reference:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            target = ref_msg.author
            
            # التحويل بالرد
            if "تحويل" in message.content:
                amt_list = [int(s) for s in message.content.split() if s.isdigit()]
                if amt_list:
                    amt = amt_list[0]
                    if get_v(message.author.id, 'cash') >= amt:
                        add_v(message.author.id, 'cash', -amt)
                        add_v(target.id, 'cash', amt)
                        await message.reply(f"تم تحويل `{amt:,}` ريال بنجاح إلى {target.mention} ✅")
                    else:
                        await message.reply("كاشك ما يغطي العملية ❌")
            
            # الزرف بالرد
            elif message.content == "زرف" and target != message.author:
                if random.random() > 0.5:
                    stolen = random.randint(500, 2000)
                    add_v(target.id, 'cash', -stolen); add_v(message.author.id, 'cash', stolen)
                    await message.reply(f"عملية ناجحة! زرفت `{stolen:,}` ريال 🥷")
                else:
                    add_v(message.author.id, 'cash', -1000)
                    await message.reply("انقفطت ودفعت غرامة `1000` ريال 🚔")
        except: pass

    await bot.process_commands(message)

# --- 💳 الرصيد المنسق ---
@bot.command(name='رصيدي')
async def balance(ctx):
    uid = str(ctx.author.id)
    c, b = get_v(uid, 'cash'), get_v(uid, 'bank')
    marry = f"<@{db['marry'][uid]}> ❤️" if uid in db['marry'] else "عزوبي 🍃"
    
    msg = f"👤 **بطاقة التعريف الشخصية** ✨\n"
    msg += f"━━━━━━━━━━━━━━\n"
    msg += f"💵 **الكاش:** `{c:,}` ريال\n"
    msg += f"🏧 **البنك:** `{b:,}` ريال\n"
    msg += f"💍 **الحالة:** {marry}\n"
    msg += f"━━━━━━━━━━━━━━"
    await ctx.reply(msg)

# --- 💼 العمل المطور ---
JOBS = [("طيار 👨‍✈️", 5000), ("مبرمج 💻", 4000), ("طبيب 🩺", 6000), ("مهندس 🏗️", 4500)]

@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    job, pay = random.choice(JOBS)
    salary = random.randint(pay-1000, pay+1000)
    add_v(ctx.author.id, 'cash', salary)
    await ctx.reply(f"اشتغلت **{job}** وعطوك راتب `{salary:,}` ريال 💵")

# --- 📈 الأسهم ---
STOCKS = {"أرامكو": 100, "تيسلا": 250, "سولانا": 150}
@tasks.loop(minutes=10)
async def stock_update():
    channel = bot.get_channel(STOCKS_CH_ID)
    if not channel: return
    msg = "📊 **تحديث الأسهم الحالية** 📉\n━━━━━━━━━━━━━━\n"
    for s in STOCKS:
        change = random.randint(-15, 20)
        STOCKS[s] = max(10, STOCKS[s] + change)
        msg += f"🔹 **{s}**: `{STOCKS[s]}` ريال\n"
    msg += "━━━━━━━━━━━━━━\nتحديث تلقائي كل 10 دقائق ⌛"
    await channel.send(msg)

@bot.event
async def on_ready():
    print(f"Mira Online: {bot.user} ✅")
    if not stock_update.is_running(): stock_update.start()

keep_alive()
bot.run(os.environ.get('TOKEN'))
