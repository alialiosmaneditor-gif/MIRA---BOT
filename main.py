import discord
from discord.ext import commands, tasks
import os, random, asyncio, time, json
from flask import Flask
from threading import Thread
from datetime import datetime

# --- 🌐 تشغيل السيرفر (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Mira Advanced System: Online 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# --- 📁 قاعدة البيانات ---
DB_FILE = "database.json"
ID_CHANNEL_STOCKS = 123456789012345678  # ⚠️ ضع هنا آيدي القناة التي ترسل فيها الأسهم

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                keys = ['cash', 'bank', 'items', 'marry', 'stocks']
                for k in keys:
                    if k not in data: data[k] = {}
                return data
        except: return {'cash': {}, 'bank': {}, 'items': {}, 'marry': {}, 'stocks': {}}
    return {'cash': {}, 'bank': {}, 'items': {}, 'marry': {}, 'stocks': {}}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# --- ⚙️ دوال المساعدة ---
def get_val(uid, cat, default=0):
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = default
    return db[cat][uid]

def update_val(uid, cat, amt):
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = 0
    db[cat][uid] += amt
    save_db()

# --- 📈 نظام الأسهم المطور ---
STOCKS = {
    "ارامكو": {"price": 100, "trend": "➖"},
    "تيسلا": {"price": 250, "trend": "➖"},
    "سولانا": {"price": 150, "trend": "➖"},
    "الراجحي": {"price": 85, "trend": "➖"}
}

@tasks.loop(minutes=10)
async def stock_market_task():
    channel = bot.get_channel(ID_CHANNEL_STOCKS)
    if not channel: return

    update_text = "🔔 **تحديث مباشر لسوق الأسهم** 📈\n"
    update_text += f"📅 `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n"
    update_text += "━━━━━━━━━━━━━━━━━━\n"

    for s in STOCKS:
        old_price = STOCKS[s]["price"]
        change = random.randint(-20, 25)
        new_price = max(10, old_price + change)
        
        trend = "🔼" if new_price > old_price else "🔽"
        STOCKS[s]["price"] = new_price
        STOCKS[s]["trend"] = trend
        
        update_text += f"{trend} **{s}**: `{new_price:,}` ريال\n"

    update_text += "━━━━━━━━━━━━━━━━━━\n"
    update_text += "⌛ التحديث القادم بعد: `10 دقائق`"
    
    await channel.send(update_text)

# --- 💍 نظام الزواج بمهر ---
@bot.command(name='تزوجني')
async def marry(ctx, dowry: int):
    if not ctx.message.reference:
        return await ctx.reply("⚠️ | لازم ترد على رسالة الشخص اللي تبي تتزوجه!")
    
    target = (await ctx.channel.fetch_message(ctx.message.reference.message_id)).author
    if target == ctx.author: return await ctx.reply("🙅‍♂️ | ما تقدر تتزوج نفسك!")
    
    if str(ctx.author.id) in db['marry']: return await ctx.reply("❌ | أنت متزوج بالفعل!")
    if str(target.id) in db['marry']: return await ctx.reply("❌ | هذا الشخص متزوج!")
    
    if get_val(ctx.author.id, 'cash') < dowry:
        return await ctx.reply(f"💸 | كاشك ما يغطي المهر المطلوب (`{dowry:,}`)")

    await ctx.send(f"👰 **طلب زواج**\n{target.mention}، هل تقبل الزواج من {ctx.author.mention} بمهر قدره `{dowry:,}`؟\n\n*(اكتب: **أقبل** أو **أرفض** خلال 60 ثانية)*")

    def check(m): return m.author == target and m.content in ["أقبل", "أرفض"]
    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        if msg.content == "أقبل":
            update_val(ctx.author.id, 'cash', -dowry)
            update_val(target.id, 'cash', dowry)
            db['marry'][str(ctx.author.id)] = str(target.id)
            db['marry'][str(target.id)] = str(ctx.author.id)
            save_db()
            await ctx.send(f"🎊 **تم الزواج بنجاح!**\nألف مبروك لـ {ctx.author.mention} و {target.mention} ❤️")
        else:
            await ctx.send(f"💔 | {target.mention} رفض الزواج.. معوض خير.")
    except asyncio.TimeoutError:
        await ctx.send("⌛ | انتهى الوقت ولم يتم الرد.")

# --- 🥷 نظام الرد الشامل (زرف، تحويل، هبة) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # التعامل مع الردود
    if message.reference:
        ref_msg = await message.channel.fetch_message(message.reference.message_id)
        target = ref_msg.author
        content = message.content

        if content == "زرف" and target != message.author:
            if random.random() > 0.4:
                stolen = random.randint(300, 1200)
                update_val(target.id, 'cash', -stolen)
                update_val(message.author.id, 'cash', stolen)
                await message.reply(f"🥷 **عملية ناجحة!** زرفت من {target.mention} مبلغ `{stolen:,}` ريال.")
            else:
                update_val(message.author.id, 'cash', -600)
                await message.reply("🚔 **كشفتك الشرطة!** دفعت غرامة `600` ريال.")

        elif content.startswith("تحويل"):
            try:
                amt = int(''.join(filter(str.isdigit, content)))
                if get_val(message.author.id, 'cash') >= amt:
                    update_val(message.author.id, 'cash', -amt)
                    update_val(target.id, 'cash', amt)
                    await message.reply(f"✅ تم تحويل `{amt:,}` ريال إلى {target.mention}.")
            except: pass

    await bot.process_commands(message)

# --- 💳 الأوامر الأساسية ---
@bot.command(name='رصيدي')
async def balance(ctx):
    user_id = str(ctx.author.id)
    cash = get_val(user_id, 'cash')
    bank = get_val(user_id, 'bank')
    status = "عزوبي 🍃"
    if user_id in db['marry']:
        p_id = db['marry'][user_id]
        status = f"متزوج من <@{p_id}> ❤️"

    msg = f"👤 **معلوماتك الاقتصادية:**\n"
    msg += "━━━━━━━━━━━━━━\n"
    msg += f"💵 **الكاش:** `{cash:,}` ريال\n"
    msg += f"🏧 **البنك:** `{bank:,}` ريال\n"
    msg += f"💍 **الحالة:** {status}\n"
    msg += "━━━━━━━━━━━━━━"
    await ctx.reply(msg)

@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    salary = random.randint(1000, 2500)
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"👷‍♂️ | اشتغلت وجبت راتب كفو: `{salary:,}` ريال.")

@bot.command(name='الأسهم')
async def list_stocks(ctx):
    msg = "📊 **أسعار الأسهم الحالية:**\n━━━━━━━━━━━━━━\n"
    for s, v in STOCKS.items():
        msg += f"{v['trend']} **{s}**: `{v['price']:,}` ريال\n"
    msg += "━━━━━━━━━━━━━━\n💡 التحديث تلقائي كل 10 دقائق."
    await ctx.reply(msg)

@bot.event
async def on_ready():
    print(f"Mira Bot is Online ✅")
    stock_market_task.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ | اهدأ قليلاً! انتظر `{int(error.retry_after)}` ثانية.")

keep_alive()
bot.run(os.environ.get('TOKEN'))
