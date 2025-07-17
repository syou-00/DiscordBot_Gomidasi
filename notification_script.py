import asyncio
import discord
import os
from datetime import datetime
from google_calendar import get_tomorrow_events

async def send_notification():
    """GitHub Actions用の通知スクリプト"""
    # 環境変数から設定を取得
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    NOTIFY_CHANNEL_ID = int(os.getenv('NOTIFY_CHANNEL_ID'))
    
    if not DISCORD_TOKEN or not NOTIFY_CHANNEL_ID:
        print("環境変数が設定されていません")
        return
    
    # 現在の日本時間を取得
    import pytz
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst)
    current_hour = current_time.hour
    
    # 時間帯に応じてメッセージを変更
    if current_hour < 12:
        time_message = ""
        day_message = "今日"
    else:
        time_message = ""
        day_message = "明日"
    
    # Discord クライアントを設定
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"ログインしました: {client.user}")
        try:
            # 翌日の予定を取得
            tomorrow_events = get_tomorrow_events()
            
            if tomorrow_events:
                channel = client.get_channel(NOTIFY_CHANNEL_ID)
                if channel:
                    # メッセージを作成
                    messages = []
                    for event in tomorrow_events:
                        messages.append(f"{day_message}は{event['summary']}の予定があります")
                    
                    # 通知を送信
                    notification_text = f"{time_message}\n**{day_message}の予定**\n" + "\n".join(messages)
                    await channel.send(notification_text)
                    print(f"通知を送信しました: {len(tomorrow_events)}件の予定")
                else:
                    print("チャンネルが見つかりません")
            else:
                print("翌日の予定はありません")
                # 朝の場合は「今日の予定はありません」も送信
                if current_hour < 12:
                    channel = client.get_channel(NOTIFY_CHANNEL_ID)
                    if channel:
                        await channel.send(f"{time_message}\n今日の予定はありません。")
                
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
        finally:
            await client.close()
    
    # Discord ボットを起動
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(send_notification())
