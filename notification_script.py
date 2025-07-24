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
    
    # 夜の時間帯のみ処理（朝は何もしない）
    if current_hour < 12:
        return
    
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
            
            # 予定がある場合に通知
            if tomorrow_events:
                channel = client.get_channel(NOTIFY_CHANNEL_ID)
                if channel:
                    # メッセージを作成
                    messages = []
                    for event in tomorrow_events:
                        messages.append(f"明日は{event['summary']}の予定があります")
                    
                    # 通知を送信
                    notification_text = "**明日の予定**\n" + "\n".join(messages)
                    await channel.send(notification_text)
                    print(f"予定通知を送信しました: {len(tomorrow_events)}件の予定")
                else:
                    print("チャンネルが見つかりません")
            else:
                print("翌日の予定はないため通知をスキップします")
                
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
        finally:
            await client.close()
    
    # Discord ボットを起動
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(send_notification())
