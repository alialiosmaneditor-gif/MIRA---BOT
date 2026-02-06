import discord
from discord.ext import commands
import json, os, random, asyncio

# --- 📁 إعدادات القاعدة والذاكرة الدائمة ---
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {'cash': {}, 'bank': {}, 'marry': {}, 'job': {}, 'exp': {}}

db = load_db()

def save_db():
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def update_val(uid, cat, amt):
    uid = str(uid)
    if cat not in db: db[cat] = {}
    db[cat][uid] = db[cat].get(uid, 0) + amt
    save_db()

def get_val(uid, cat, default=0):
    return db.get(cat, {}).get(str(uid), default)

# --- ⚙️ إعدادات البوت ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- 💸 أمر التحويل ---
@bot.command(name='تحويل')
async def transfer(ctx, amount: int):
    if not ctx.message.reference:
        return await ctx.reply("يجب الرد على رسالة الشخص الذي تريد التحويل له ⚠️")
    
    ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    target = ref_msg.author
    
    if target == ctx.author:
        return await ctx.reply("لا يمكنك تحويل الأموال لنفسك يا ذكي 😂")
    
    if amount <= 0:
        return await ctx.reply("يجب أن يكون المبلغ أكبر من صفر 💰")
    
    user_cash = get_val(ctx.author.id, 'cash')
    if user_cash < amount:
        return await ctx.reply("رصيدك لا يكفي لإتمام هذه العملية ❌")

    options = "الخيارات المتاحة: اكتب [متأكد] للتأكيد أو [الغاء] للتراجع ✅"
    await ctx.reply(f"هل أنت متأكد من تحويل `{amount:,}` ريال إلى {target.mention}؟ 💸\n{options}")

    def check(m): return m.author == ctx.author and m.content in ["متأكد", "الغاء"]
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "متأكد":
            update_val(ctx.author.id, 'cash', -amount)
            update_val(target.id, 'cash', amount)
            await ctx.send(f"تم تحويل `{amount:,}` ريال بنجاح إلى {target.mention} ✅")
        else:
            await ctx.send("تم إلغاء عملية التحويل بنجاح 🚫")
    except asyncio.TimeoutError:
        await ctx.send("انتهى وقت الاستجابة، تم إلغاء العملية ⌛")

# --- 💔 نظام الخلع ---
@bot.command(name='خلع')
async def divorce(ctx):
    user_id = str(ctx.author.id)
    if user_id not in db['marry']:
        return await ctx.reply("أنت لست متزوجاً أصلاً لتطلب الخلع 😶")
    
    partner_id = db['marry'][user_id]
    options = "الخيارات المتاحة: اكتب [متأكد] لإنهاء العلاقة أو [الغاء] للتراجع ✅"
    
    await ctx.reply(f"هل أنت متأكد من طلب الخلع من <@{partner_id}>؟ 💔\n{options}")

    def check(m): return m.author == ctx.author and m.content in ["متأكد", "الغاء"]
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "متأكد":
            # إزالة الطرفين من قاعدة بيانات الزواج
            db['marry'].pop(user_id, None)
            db['marry'].pop(str(partner_id), None)
            save_db()
            await ctx.send(f"تم الانفصال رسمياً.. كل شخص راح في حاله 🥀")
        else:
            await ctx.send("تم التراجع عن قرار الخلع، الله يصلح الحال 🤍")
    except asyncio.TimeoutError:
        await ctx.send("انتهى الوقت، يبدو أنك تراجعت عن قرارك ⌛")

# --- 📊 أمر الرصيد المنسق ---
@bot.command(name='رصيدي')
async def balance(ctx):
    user_id = ctx.author.id
    cash = get_val(user_id, 'cash')
    job = db.get('job', {}).get(str(user_id), "عاطل")
    marry_status = f"<@{db['marry'][str(user_id)]}> ❤️" if str(user_id) in db['marry'] else "عزوبي 🍃"

    msg = f"✨ **بطاقة الأحوال الشخصية** ✨\n"
    msg += f"━━━━━━━━━━━━━━\n"
    msg += f"💵 **الكاش:** `{cash:,}` ريال\n"
    msg += f"💼 **المهنة:** {job} 🛠️\n"
    msg += f"💍 **الحالة:** {marry_status}\n"
    msg += f"━━━━━━━━━━━━━━"
    await ctx.reply(msg)

# --- 🎰 الياناصيب المنسق ---
@bot.command(name='ياناصيب')
async def lottery(ctx):
    user_id = ctx.author.id
    price = 100000
    if get_val(user_id, 'cash') < price:
        return await ctx.reply(f"رصيدك لا يكفي لشراء التذكرة ❌")

    options = "الخيارات المتاحة: اكتب [متأكد] للشراء أو [الغاء] للتراجع ✅"
    await ctx.reply(f"سعر التذكرة `{price:,}` ريال، هل تود المغامرة؟ 🎰\n{options}")

    def check(m): return m.author == ctx.author and m.content in ["متأكد", "الغاء"]
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "متأكد":
            update_val(user_id, 'cash', -price)
            if random.random() <= 0.20:
                update_val(user_id, 'cash', 400000)
                await ctx.send(f"مبروووك! انفجرت الجائزة بوجهك وفزت بـ `400,000` ريال 🎊")
            else:
                await ctx.send(f"للأسف خسرنا التذكرة، حاول مرة أخرى 💸")
        else:
            await ctx.send("تم إلغاء شراء التذكرة 🚫")
    except: pass

@bot.event
async def on_ready():
    print(f"Mira System is active as {bot.user} ✅")

bot.run("YOUR_TOKEN_HERE")
