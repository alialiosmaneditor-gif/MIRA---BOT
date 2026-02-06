import discord
from discord.ext import commands, tasks
import os, random, asyncio, time, json
from flask import Flask
from threading import Thread

# --- نظام البقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "ميرا المتطورة جاهزة ومحفوظة.. 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

# --- 📁 نظام قاعدة البيانات الدائمة (JSON) ---
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {'cash': {}, 'bank': {}, 'points': {}, 'items': {}, 'boost': {}}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# --- دوال المساعدة (مع حفظ تلقائي) ---
def get_val(uid, cat):
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = 0
    return db[cat][uid]

def update_val(uid, cat, amt): 
    uid = str(uid)
    if uid not in db[cat]: db[cat][uid] = 0
    db[cat][uid] += amt
    save_db() # حفظ فوري عند أي تغيير

@bot.event
async def on_ready():
    print(f"تم تشغيل ميرا بنجاح ✅ - البيانات محفوظة في {DB_FILE}")

# --- 📜 الأوامر المنسقة (شرح واضح) ---
@bot.command(name='الأوامر')
async def help_menu(ctx):
    guide = (
        "🎮 **دليل ميرا الاقتصادي - البيانات محفوظة للأبد!** 🇸🇦\n\n"
        "💰 **1. الاقتصاد والزرف:**\n"
        "• `عمل` 💼: راتب كل 5 دقايق.\n"
        "• `زرف` 🥷: رد على رسالة واكتب 'زرف'.\n"
        "• `تحويل (المبلغ)` 💸: رد على رسالة لتحويل المبلغ.\n\n"
        "🏧 **2. البنك والحماية:**\n"
        "• `إيداع (المبلغ)` 🏦: حط فلوسك بالخزنة.\n"
        "• `سحب (المبلغ)` 🏧: اسحب من الخزنة.\n"
        "• `رصيدي` 💳: شف ثروتك كاملة.\n\n"
        "🎲 **3. المسابقات (40 ثانية):**\n"
        "• `يانصيب` 🎰 | `رياضيات` 🧮 | `عكس` 🔄 | `أعلام` 🌍\n\n"
        "🏆 **4. التنافس:**\n"
        "• `توب 10` 💎: من هو هامور السيرفر؟"
    )
    await ctx.reply(guide)

# --- 💳 الرصيد المصلح (لا يظهر فاضي) ---
@bot.command(name='رصيدي')
async def balance(ctx):
    u = ctx.author.id
    cash, bank, pts = get_val(u, 'cash'), get_val(u, 'bank'), get_val(u, 'points')
    msg = (
        f"🏦 **محفظتك يا بطل:**\n"
        f"💵 **الكاش:** {cash:,} ريال\n"
        f"🏧 **البنك:** {bank:,} ريال\n"
        f"🐾 **النقاط:** {pts}\n"
    )
    await ctx.reply(msg)

# --- 🏧 أوامر البنك ---
@bot.command(name='إيداع')
async def deposit(ctx, amt: int):
    if amt <= 0 or get_val(ctx.author.id, 'cash') < amt: return await ctx.reply("❌ كاشك ما يكفي!")
    update_val(ctx.author.id, 'cash', -amt)
    update_val(ctx.author.id, 'bank', amt)
    await ctx.reply(f"🏦 تم إيداع **{amt:,} ريال** بنجاح. ✅")

@bot.command(name='سحب')
async def withdraw(ctx, amt: int):
    if amt <= 0 or get_val(ctx.author.id, 'bank') < amt: return await ctx.reply("❌ رصيدك بالبنك ما يكفي!")
    update_val(ctx.author.id, 'bank', -amt)
    update_val(ctx.author.id, 'cash', amt)
    await ctx.reply(f"🏧 تم سحب **{amt:,} ريال** لمحفظتك. ✅")

# --- 🥷 نظام الرد (التحويل والزرف) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # التحويل بالرد
    if "تحويل" in message.content and message.reference:
        try:
            amt = int(''.join(filter(str.isdigit, message.content)))
            target = (await message.channel.fetch_message(message.reference.message_id)).author
            if get_val(message.author.id, 'cash') < amt: return await message.reply("❌ كاشك ما يكفي!")
            update_val(message.author.id, 'cash', -amt); update_val(target.id, 'cash', amt)
            await message.reply(f"✅ تم تحويل **{amt:,} ريال** لـ {target.mention}! 🤝")
        except: pass

    # الزرف بالرد
    if message.content == "زرف" and message.reference:
        target = (await message.channel.fetch_message(message.reference.message_id)).author
        if target == message.author: return
        if random.randint(1, 100) > 50:
            stolen = random.randint(100, 600)
            update_val(target.id, 'cash', -stolen); update_val(message.author.id, 'cash', stolen)
            await message.reply(f"🥷 زرفت من {target.mention} مبلغ **{stolen} ريال**! 😎💰")
        else:
            update_val(message.author.id, 'cash', -400); await message.reply("🚔 انقفطت ودفعت غرامة 400 ريال! 🚨")
            
    await bot.process_commands(message)

# --- أوامر الاقتصاد ---
@bot.command(name='عمل')
@commands.cooldown(1, 300, commands.BucketType.user)
async def work(ctx):
    salary = random.randint(800, 1500)
    update_val(ctx.author.id, 'cash', salary)
    await ctx.reply(f"💼 جبت راتب **{salary:,} ريال**.. كفو! 💸")

@bot.command(name='توب')
async def top_rich(ctx, arg=""):
    if arg == "10":
        sorted_data = sorted(db['cash'].items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير بالسيرفر:**\n\n"
        for i, (uid, bal) in enumerate(sorted_data):
            msg += f"{i+1}. <@{uid}> — **{bal:,} ريال** 💰\n"
        await ctx.reply(msg)

keep_alive()
bot.run(os.environ.get('TOKEN'))
