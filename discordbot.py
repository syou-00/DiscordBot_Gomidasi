import discord
import config
import random
from calendar_integration import get_calendar_bot
from google_calendar import get_tomorrow_events

# 必要最低限のインテントのみを設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容を読み取るために必要
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("Ready!")
    
    # 翌日の予定をチェックして通知
    try:
        tomorrow_events = get_tomorrow_events()
        
        if tomorrow_events and hasattr(config, 'NOTIFY_CHANNEL_ID') and config.NOTIFY_CHANNEL_ID:
            channel = client.get_channel(config.NOTIFY_CHANNEL_ID)
            if channel:
                # 翌日の予定をまとめて送信
                messages = []
                for event in tomorrow_events:
                    messages.append(f"明日は{event['summary']}の予定があります")
                
                if messages:
                    await channel.send("**明日の予定**\n" + "\n".join(messages))
                    
    except Exception as e:
        print(f"翌日の予定チェック中にエラーが発生しました: {str(e)}")
    
    # Botが起動したことを通知するメッセージを送信
    if hasattr(config, 'NOTIFY_CHANNEL_ID') and config.NOTIFY_CHANNEL_ID:
        channel = client.get_channel(config.NOTIFY_CHANNEL_ID)
        if channel:
            await channel.send("Botが起動しました！")

@client.event
async def on_message(message):
    # 自身が送信したメッセージには反応しない
    if message.author == client.user:
        return

    # カレンダー関連のコマンドを処理
    if message.content.startswith('!カレンダー'):
        try:
            calendar_bot = get_calendar_bot()
            parts = message.content.split()
            
            if len(parts) == 1:
                # 直近のイベントを取得
                event = calendar_bot.get_next_event()
                response = calendar_bot.format_event_message(event)
            elif len(parts) == 2:
                # 特定のタイプのイベントを取得
                event_type = parts[1]
                event = calendar_bot.get_event_by_type(event_type)
                response = calendar_bot.format_event_message(event)
            else:
                response = "使用方法: !カレンダー [家庭/プラスチック/紙]"
            
            # 予定がある場合のみメッセージを送信
            if response:
                await message.channel.send(response)
            
        except Exception as e:
            await message.channel.send(f"エラーが発生しました: {str(e)}")
    
    # 明日の予定をチェック
    elif message.content.startswith('!明日'):
        try:
            tomorrow_events = get_tomorrow_events()
            
            if tomorrow_events:
                responses = []
                for event in tomorrow_events:
                    responses.append(f"明日は{event['summary']}の予定があります")
                response = "**明日の予定**\n" + "\n".join(responses)
            else:
                response = "明日の予定はありません。"
                
            await message.channel.send(response)
            
        except Exception as e:
            await message.channel.send(f"エラーが発生しました: {str(e)}")

    # ユーザーからのメンションを受け取った場合、あらかじめ用意された配列からランダムに返信を返す
    elif client.user in message.mentions:
        answer_list = ["さすがですね！","知らなかったです！","すごいですね！","センスが違いますね！","そうなんですか？"]
        answer = random.choice(answer_list)
        print(answer)
        await message.channel.send(answer)




client.run(config.DISCORD_TOKEN)