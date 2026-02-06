import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "البوت متصل 🟢"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.start()

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

@bot.event
async def on_ready(): print(f'ميرا جاهزة: {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "ميرا" in message.content: await message.reply("هلا، أسمعك!")
    await bot.process_commands(message)

keep_alive()
bot.run(os.environ['TOKEN'])
