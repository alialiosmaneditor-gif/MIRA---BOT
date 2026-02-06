import discord
from discord.ext import commands, tasks
import os, random, asyncio, time, json
from flask import Flask
from threading import Thread

# --- 🌐 نظام البقاء متصلاً (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "ميرا المتطورة جاهزة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# --- 📁 نظام قاعدة البيانات الدائمة (JSON) ---
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # التأكد من وجود الأقسام الأساسية
                for key in ['cash', 'bank', 'items']:
                    if key not in data: data[key] = {}
                return data
        except: return {'cash': {}, 'bank': {}, 'items': {}}
    return {'cash': {}, 'bank': {}, 'items': {}}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# --- 🛒 قائمة عناصر المتجر ---
# يمكنك إضافة أو تعديل العناصر هنا بسهولة
STORE_ITEMS = {
    "رول": {"price": 50000, "desc": "رتبة مميزة في السيرفر", "emoji": "🎭"},
    "حماية": {"price": 10000, "desc": "تمنع الزرف لمدة معينة", "emoji": "🛡️"},
    "تذكرة": {"price": 5000, "desc": "تذكرة سحب على جوائز", "emoji": "🎫"},
    "سيارة": {"price": 150000, "desc": "للاستعراض في البروفايل", "emoji": "🏎️"}
}

# --- ⚙️ دوال المساعدة لضمان الدقة ---
def get_val(uid, cat):
    uid = str(uid)
    if uid not in db[cat]: 
        if cat == 'items': db[cat][uid] = []
        else: db[cat][uid] = 0
    return db[cat][uid]

def update_val(uid, cat, amt): 
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = 0
    db[cat][uid] += amt
    save_db()

def get_balance_msg(uid):
    cash = get_val(uid, 'cash')
    bank = get_val(uid, 'bank')
    return f"\n\n💰 **تحديث المحفظة:**\n💵 كاش: `{cash:,}` ريال\n🏧 بنك: `{bank:,}` ريال"

@bot.event
async def on_ready():
    print(f"✅ تم تشغيل {bot.user.name} - البيانات محفوظة بنجاح")

# --- 📜 الأوامر العامة ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    guide = (
        "🎮 **دليل ميرا الاقتصادي الشامل** 🇸🇦\n\n"
        "💰 **الاقتصاد والزرف:**\n"
        "• `عمل` 💼: الحصول على راتب.\n"
        "• `زرف` 🥷: رد على رسالة الشخص لزرفه.\n"
        "• `تحويل (المبلغ)` 💸: رد على رسالة لتحويل كاش.\n\n"
        "🛒 **المتجر والامتلاك:**\n"
        "• `المتجر` 🛍️: عرض الأغراض المتاحة.\n"
        "• `شراء (اسم الغرض)` 💳: شراء منتج من المتجر.\n"
        "• `اغراضي` 📦: عرض ما تملكه في حقيبتك.\n\n"
        "🏧 **البنك والحماية:**\n"
        "• `إيداع (المبلغ)` 🏦 | `سحب (المبلغ)` 🏧\n"
        "• `رصيدي` 💳 | `توب 10` 💎"
    )
    await ctx.reply(guide)

# --- 🛒 نظام المتجر (The Shop System) ---
@bot.command(name='المتجر')
async def shop(ctx):
    embed_msg = "🛒 **متجر ميرا الاقتصادي**\n"
    embed_msg += "————————————————\n"
    for item, info in STORE_ITEMS.items():
        embed_msg += f"{info['emoji']} **{item}** — `{info['price']:,}` ريال\n╰ {info['desc']}\n\n"
    embed_msg += "💡 للشراء اكتب: `شراء اسم الغرض`"
    await ctx.reply(embed_msg)

@bot.command(name='شراء')
async def buy(ctx, *, item_name: str):
    if item_name not in STORE_ITEMS:
        return await ctx.reply("❌ هذا الغرض غير موجود في المتجر! تأكد من الاسم.")
    
    cost = STORE_ITEMS[item_name]['price']
    user_cash = get_val(ctx.author.id, 'cash')
    
    if user_cash < cost:
        return await ctx.reply(f"❌ ما عندك كاش كافي! سعره `{cost:,}` ريال.")
    
    # خصم المبلغ
    update_val(ctx.author.id, 'cash', -cost)
    
    # إضافة الغرض للحقيبة
    uid = str(ctx.author.id)
    if uid not in db['items']: db['items'][uid] = []
    db['items'][uid].append(item_name)
    save_db()
    
    await ctx.reply(f"✅ مبروك! شريت **{item_name}** {STORE_ITEMS[item_name]['emoji']} بنجاح.{get_balance_msg(ctx.author.id)}")

@bot.command(name='اغراضي')
async def my_items(ctx):
    items = get_val(ctx.author.id, 'items')
    if not items:
        return await ctx.reply("📦 حقيبتك فاضية.. روح اشتغل واشترِ من المتجر!")
    
    msg = "📦 **حقيبة أغراضك:**\n"
    for item in set(items):
        count = items.count(item)
        msg += f"• {STORE_ITEMS[item]['emoji']} {item} (العدد: {count})\n"
    await ctx.reply(msg)

# --- 💳 البنك والاقتصاد ---
@bot.command(name='رصيدي')
async def balance(ctx):
    await ctx.reply(get_balance_msg(ctx.author.id))

@bot.command(name='إيداع')
async def deposit(ctx, amt: int):
    if amt <= 0: return await ctx.reply("❌ المبلغ لازم يكون أكبر من صفر!")
    if get_val(ctx.author.id, 'cash') < amt: return await ctx.reply("❌ ما عندك كاش يكفي!")
    
    update_val(ctx.author.id, 'cash', -amt)
    update_val(ctx.author.id, 'bank', amt)
    await ctx.reply(f"✅ تم إيداع **{amt:,}** ريال في البنك! 🏦{get_balance_msg(ctx.author.id)}")

@bot.command(name='سحب')
async def withdraw(ctx, amt: int):
    if amt <= 0: return await ctx.reply("❌ المبلغ لازم يكون أكبر من صفر!")
    if get_val(ctx.author.id, 'bank') < amt: return await ctx.reply("❌ بنكك ما فيه هذا المبلغ!")
    
    update_val(ctx.author.id, 'bank', -amt)
    update_val(ctx.author.id, 'cash', amt)
    await ctx.reply(f"🏧 تم سحب **{amt:,}** ريال لمحفظتك!{get_balance_msg(ctx.author.id)}")

@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    salary = random.randint(800, 1500)
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 اشتغلت وجبت راتب **{salary:,}** ريال! كفو.{get_balance_msg(ctx.author.id)}")

@bot.command(name='توب')
async def top_rich(ctx, limit: int = 10):
    sorted_data = sorted(db['cash'].items(), key=lambda x: x[1], reverse=True)[:limit]
    msg = f"🏆 **أغنى {limit} هوامير بالسيرفر:**\n\n"
    for i, (uid, bal) in enumerate(sorted_data):
        msg += f"{i+1}. <@{uid}> — **{bal:,} ريال** 💰\n"
    await ctx.reply(msg)

# --- 🥷 نظام الردود (الزرف والتحويل) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # تحويل بالرد
    if message.content.startswith("تحويل") and message.reference:
        try:
            amt = int(''.join(filter(str.isdigit, message.content)))
            target = (await message.channel.fetch_message(message.reference.message_id)).author
            if target == message.author: return
            if get_val(message.author.id, 'cash') < amt: return await message.reply("❌ كاشك ما يكفي!")
            
            update_val(message.author.id, 'cash', -amt)
            update_val(target.id, 'cash', amt)
            await message.reply(f"✅ تم تحويل **{amt:,}** لـ {target.mention}!{get_balance_msg(message.author.id)}")
        except: pass

    # زرف بالرد
    elif message.content == "زرف" and message.reference:
        target = (await message.channel.fetch_message(message.reference.message_id)).author
        if target == message.author: return
        
        if random.randint(1, 100) > 50:
            stolen = random.randint(100, 600)
            update_val(target.id, 'cash', -stolen)
            update_val(message.author.id, 'cash', stolen)
            res = f"🥷 زرفت من {target.mention} مبلغ **{stolen} ريال**! 😎"
        else:
            update_val(message.author.id, 'cash', -400)
            res = "🚔 انقفطت يا خايب! دفعت غرامة 400 ريال! 🚨"
        await message.reply(f"{res}{get_balance_msg(message.author.id)}")
            
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ اصبر يا وحش باقي لك **{int(error.retry_after)} ثانية**.")

keep_alive()
bot.run(os.environ.get('TOKEN'))
