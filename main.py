import discord
from discord.ext import commands
import requests
import asyncio
import os
from flask import Flask
from threading import Thread

# 1. تشغيل سيرفر وهمي للحفاظ على اتصال المنصة (Railway/Render)
app = Flask('')
@app.route('/')
def home(): return "I am alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعدادات البوت والـ Intents
intents = discord.Intents.default()
try:
    intents.message_content = True
except:
    intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)
GROQ_API_KEY = "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"
ai_status = True

@bot.event
async def on_ready():
    print(f"| {bot.user.name} IS READY |")

# 3. أمر التحكم في تشغيل/إيقاف الذكاء الاصطناعي (.sees on / .sees off)
@bot.group(invoke_without_command=True)
async def sees(ctx, status: str):
    global ai_status
    try: await ctx.message.delete()
    except: pass
    if status.lower() == "on": ai_status = True
    elif status.lower() == "off": ai_status = False

# 4. أمر المسح المتطور (.sees del 5)
@sees.command(name="del")
async def _del(ctx, *, inp: str = "1"):
    try: await ctx.message.delete()
    except: pass
    only_bot = "@" in inp
    inp = inp.replace("@", "").strip()
    if not inp or inp.lower() == "all": amount = 100
    else:
        try: amount = int(inp)
        except: amount = 100
    if isinstance(ctx.channel, discord.DMChannel):
        async for msg in ctx.channel.history(limit=amount):
            if msg.author == bot.user:
                try: await msg.delete()
                except: pass
    else:
        check_func = (lambda m: m.author.id == bot.user.id) if only_bot else None
        await ctx.channel.purge(limit=amount, check=check_func)

# 5. معالجة الرسائل والذكاء الاصطناعي
@bot.event
async def on_message(message):
    global ai_status
    if message.author == bot.user: return
    if message.content.lower().startswith(".sees"):
        await bot.process_commands(message)
        return
    
    # الرد التلقائي والحسابات
    if ai_status and message.content.startswith("."):
        calc_text = message.content[1:]
        if any(op in calc_text for op in '+-*/') and not any(c.isalpha() for c in calc_text):
            try:
                await message.channel.send(str(eval(calc_text)))
                return
            except: pass
            
        # جلب تاريخ الرسائل للرد الذكي
        history_messages = []
        async for msg in message.channel.history(limit=10):
            role = "assistant" if msg.author.id == bot.user.id else "user"
            content = msg.content[1:] if msg.content.startswith(".") else msg.content
            user_name = msg.author.display_name.split('#')[0]
            full_content = f"[{user_name}]: {content}" if role == "user" else content
            history_messages.append({"role": role, "content": full_content})
        history_messages.reverse()
        
        # الاتصال بـ Groq AI
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a smart assistant. Use names naturally. ONLY Arabic/English."},
                *history_messages
            ]
        }
        async with message.channel.typing():
            try:
                r = requests.post(url, headers=headers, json=payload).json()
                if 'choices' in r: await message.channel.send(r['choices'][0]['message']['content'][:2000])
            except: pass
    await bot.process_commands(message)

# 6. تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    # هنا بنحط التوكن مباشرة بين الأقواس عشان يشتغل فوراً
    bot.run("MTQ3Mzc2MDQ5ODAwMzc0Mjg5Mw.G6ogCs.r486T_7c2hC9-n08Z0dFargJ0UZ8kAhHDMrVa0")
