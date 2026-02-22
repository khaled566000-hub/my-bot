import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os

intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix='.', intents=intents)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ai_status = True
chat_memory = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - Railway Hosting")

@bot.group(invoke_without_command=True)
async def sees(ctx, status: str):
    global ai_status
    try: await ctx.message.delete()
    except: pass
    if status.lower() == "on": 
        ai_status = True
        await ctx.send("AI: Enabled", delete_after=3)
    elif status.lower() == "off": 
        ai_status = False
        await ctx.send("AI: Disabled", delete_after=3)

@sees.command(name="del")
async def _del(ctx, *, inp: str = "1"):
    try: await ctx.message.delete()
    except: pass
    
    only_bot = False
    if "@" in inp:
        only_bot = True
        inp = inp.replace("@", "").strip()
    
    try:
        amount = 100 if inp.lower() == "all" or not inp else int(inp)
    except:
        amount = 100

    def is_bot(m):
        return m.author.id == bot.user.id

    if only_bot:
        await ctx.channel.purge(limit=amount, check=is_bot)
    else:
        await ctx.channel.purge(limit=amount)

@bot.event
async def on_message(message):
    global ai_status, chat_memory
    if message.author == bot.user: return

    if message.content.lower().startswith(".sees"):
        await bot.process_commands(message)
        return

    user_name = message.author.display_name
    msg_content = message.content[1:] if message.content.startswith(".") else message.content
    
    chat_memory.append({"role": "user", "content": f"[{user_name}]: {msg_content}"})
    if len(chat_memory) > 100: 
        chat_memory.pop(0)

    if ai_status and message.content.startswith("."):
        calc_text = message.content[1:]
        if any(op in calc_text for op in '+-*/') and not any(c.isalpha() for c in calc_text):
            try:
                result = str(eval(calc_text))
                await message.channel.send(result)
                chat_memory.append({"role": "assistant", "content": result})
                return
            except: pass

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are AI (bot-566 APP) in discord. Rule 1: Users appear as [Name]: Content. NEVER write [ ] or : in your response. Rule 2: Use the user's name exactly as spelled but only when necessary."},
                *chat_memory
            ]
        }

        async with message.channel.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply = data['choices'][0]['message']['content']
                            
                            chat_memory.append({"role": "assistant", "content": reply})
                            
                            for i in range(0, len(reply), 2000):
                                await message.channel.send(reply[i:i+2000])
                        else:
                            print(f"API Error: {resp.status}")
            except Exception as e:
                print(f"Error occurred: {e}")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)

