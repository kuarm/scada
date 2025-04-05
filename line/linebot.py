import openai

# ตั้งค่า API ของ Together AI
openai.api_base = "https://api.together.xyz/v1"
openai.api_key = "tgp_v1_2-liFIC81sUgJq1NEUQo7NqEMINMID3WIAsV7X-OYJk"

# ใช้ Llama-2-7B Chat
response = openai.ChatCompletion.create(
    model="meta-llama/Llama-2-7b-chat-hf",
    messages=[{"role": "user", "content": "อธิบายระบบ SCADA"}]
)

print(response["choices"][0]["message"]["content"])

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    response = openai.ChatCompletion.create(
        model="meta-llama/Llama-2-7b-chat-hf",
        messages=[{"role": "user", "content": user_text}]
    )

    reply_text = response["choices"][0]["message"]["content"]
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
