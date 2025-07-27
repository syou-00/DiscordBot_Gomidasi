import asyncio
import discord
import os
from datetime import datetime
from google_calendar import get_tomorrow_events

async def send_notification():
    """GitHub Actions用の通知スクリプト"""
    print("=== 通知スクリプト開始 ===")
    
    # 環境変数から設定を取得
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    NOTIFY_CHANNEL_ID_STR = os.getenv('NOTIFY_CHANNEL_ID')
    
    print(f"DISCORD_TOKEN存在: {bool(DISCORD_TOKEN)}")
    print(f"NOTIFY_CHANNEL_ID_STR: {NOTIFY_CHANNEL_ID_STR}")
    
    if not DISCORD_TOKEN or not NOTIFY_CHANNEL_ID_STR:
        print("❌ 環境変数が設定されていません")
        return
    
    try:
        NOTIFY_CHANNEL_ID = int(NOTIFY_CHANNEL_ID_STR)
        print(f"NOTIFY_CHANNEL_ID: {NOTIFY_CHANNEL_ID}")
    except ValueError:
        print("❌ NOTIFY_CHANNEL_IDが無効な数値です")
        return
    
    # 現在の日本時間を取得
    import pytz
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst)
    current_hour = current_time.hour
    
    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} JST")
    print(f"現在の時間: {current_hour}時")
    
    # 時間制限を削除（常に実行）
    print("時間制限なし - 常に実行します")
    
    # Discord クライアントを設定
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Discordにログインしました: {client.user}")
        try:
            print("📅 翌日の予定を取得中...")
            # 翌日の予定を取得
            tomorrow_events = get_tomorrow_events()
            print(f"取得した予定数: {len(tomorrow_events) if tomorrow_events else 0}件")
            
            if tomorrow_events:
                print("📋 予定の詳細:")
                for i, event in enumerate(tomorrow_events):
                    print(f"  {i+1}. {event.get('summary', '名前なし')}")
            
            # チャンネルを取得
            print(f"🔍 チャンネル取得中 (ID: {NOTIFY_CHANNEL_ID})...")
            channel = client.get_channel(NOTIFY_CHANNEL_ID)
            
            if not channel:
                print(f"❌ チャンネルが見つかりません (ID: {NOTIFY_CHANNEL_ID})")
                print("利用可能なチャンネル:")
                for guild in client.guilds:
                    for ch in guild.channels:
                        if hasattr(ch, 'send'):
                            print(f"  - {ch.name} (ID: {ch.id})")
                return
            
            print(f"✅ チャンネル見つかりました: {channel.name} (ID: {channel.id})")
            
            # 予定がある場合に通知
            if tomorrow_events:
                print("📨 通知メッセージ作成中...")
                # メッセージを作成
                messages = []
                for event in tomorrow_events:
                    messages.append(f"明日は{event['summary']}の予定があります")
                
                # 通知を送信
                notification_text = "**明日の予定**\n" + "\n".join(messages)
                print(f"送信メッセージ:\n{notification_text}")
                
                await channel.send(notification_text)
                print(f"✅ 予定通知を送信しました: {len(tomorrow_events)}件の予定")
            else:
                print("📭 翌日の予定はないため通知をスキップします")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            import traceback
            print(f"詳細エラー:\n{traceback.format_exc()}")
        finally:
            print("🔚 Discord接続を終了します")
            await client.close()
    
    # Discord ボットを起動
    print("🚀 Discord ボット起動中...")
    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Discord起動エラー: {str(e)}")

if __name__ == "__main__":
    asyncio.run(send_notification())
