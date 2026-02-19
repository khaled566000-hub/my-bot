import discord
from discord.ext import commands
import requests
import asyncio
import os
from flask import Flask
from threading import Thread

# 1. السيرفر الوهمي
app = Flask('')
@app.route('/')
def home(): return "I am alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
try: intents.message_content = True
except: intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)
GROQ_API_KEY = "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"
ai_status = True

@bot.event
async def on_ready():
    print(f"| {bot.user.name} IS READY |")

# 2. أمر التحكم فقط (بدون وظيفة المسح)
@bot.group(invoke_without_command=True)
async def sees(ctx, status: str):
    global ai_status
    try: await ctx.message.delete()
    except: pass
    if status.lower() == "on": ai_status = True
    elif status.lower() == "off": ai_status = False

# 3. معالجة الرسائل والذكاء الاصطناعي
@bot.event
async def on_message(message):
    global ai_status
    if message.author == bot.user: return
    if message.content.lower().startswith(".sees"):
        await bot.process_commands(message)
        return
    
    if ai_status and message.content.startswith("."):
        calc_text = message.content[1:]
        if any(op in calc_text for op in '+-*/') and not any(c.isalpha() for c in calc_text):
            try:
                await message.channel.send(str(eval(calc_text)))
                return
            except: pass
            
        history_messages = []
        async for msg in message.channel.history(limit=20):
            role = "assistant" if msg.author.id == bot.user.id else "user"
            content = msg.content[1:] if msg.content.startswith(".") else msg.content
            user_name = msg.author.display_name.split('#')[0]
            history_messages.append({"role": role, "content": f"[{user_name}]: {content}" if role == "user" else content})
        history_messages.reverse()
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Helpful AI. Detect user language and reply ONLY in that language. No translations."},
                *history_messages
            ]
        }
        async with message.channel.typing():
            try:
                r = requests.post(url, headers=headers, json=payload).json()
                if 'choices' in r: await message.channel.send(r['choices'][0]['message']['content'][:2000])
            except: pass
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))
