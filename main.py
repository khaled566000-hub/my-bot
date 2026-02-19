@bot.command()
async def ai(ctx, *, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    
    # --- هنا نضع سطر الـ History لجمع آخر 10 رسائل في الشات ---
    history_messages = []
    async for msg in ctx.channel.history(limit=10):
        # تحديد من المتحدث (البوت أم المستخدم)
        role = "assistant" if msg.author.id == bot.user.id else "user"
        content = msg.content
        history_messages.append({"role": role, "content": content})
    
    # عكس الترتيب ليكون من الأقدم للأحدث
    history_messages.reverse()
    # -------------------------------------------------------

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant like Gemini. Respond in the user's language."},
            *history_messages # نرسل التاريخ بالكامل للذكاء الاصطناعي هنا
        ]
    }
    
    async with ctx.typing():
        try:
            r = requests.post(url, headers=headers, json=payload).json()
            answer = r['choices'][0]['message']['content']
            await ctx.send(answer[:2000])
        except:
            await ctx.send("❌ Error")
