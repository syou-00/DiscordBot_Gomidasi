import asyncio
import discord
import os
from datetime import datetime

async def send_notification():
    """GitHub Actions用の通知スクリプト（デバッグ強化版）"""
    print("=== 通知スクリプト開始 ===")
    
    # 環境変数から設定を取得
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    NOTIFY_CHANNEL_ID_STR = os.getenv('NOTIFY_CHANNEL_ID')
    
    print(f"DISCORD_TOKEN存在: {bool(DISCORD_TOKEN)}")
    print(f"DISCORD_TOKEN長さ: {len(DISCORD_TOKEN) if DISCORD_TOKEN else 0}")
    print(f"NOTIFY_CHANNEL_ID_STR: {NOTIFY_CHANNEL_ID_STR}")
    
    if not DISCORD_TOKEN or not NOTIFY_CHANNEL_ID_STR:
        print("❌ 環境変数が設定されていません")
        return
    
    try:
        NOTIFY_CHANNEL_ID = int(NOTIFY_CHANNEL_ID_STR)
        print(f"NOTIFY_CHANNEL_ID: {NOTIFY_CHANNEL_ID}")
    except ValueError as e:
        print(f"❌ NOTIFY_CHANNEL_IDが無効な数値です: {e}")
        return
    
    # 現在の日本時間を取得
    import pytz
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst)
    current_hour = current_time.hour
    
    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} JST")
    print(f"現在の時間: {current_hour}時")
    
    # Google Calendar の予定を先に取得してテスト
    print("📅 Google Calendar 接続テスト開始...")
    try:
        from google_calendar import get_tomorrow_events
        print("✅ google_calendar モジュールのインポート成功")
        
        tomorrow_events = get_tomorrow_events()
        print(f"✅ 予定取得成功: {len(tomorrow_events) if tomorrow_events else 0}件")
        
        if tomorrow_events:
            print("📋 取得した予定:")
            for i, event in enumerate(tomorrow_events):
                print(f"  {i+1}. {event.get('summary', '名前なし')}")
        else:
            print("📭 明日の予定はありません")
            
    except Exception as e:
        print(f"❌ Google Calendar エラー: {str(e)}")
        import traceback
        print(f"詳細エラー:\n{traceback.format_exc()}")
        # Google Calendar エラーでも Discord テストは続行
        tomorrow_events = []
    
    # Discord クライアントを設定
    print("🔧 Discord クライアント設定中...")
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Discordにログインしました: {client.user}")
        print(f"✅ サーバー数: {len(client.guilds)}")
        
        # 利用可能なサーバーとチャンネルを表示
        for guild in client.guilds:
            print(f"📄 サーバー: {guild.name} (ID: {guild.id})")
            for channel in guild.channels:
                if hasattr(channel, 'send'):  # テキストチャンネルのみ
                    print(f"  - {channel.name} (ID: {channel.id})")
        
        try:
            # チャンネルを取得
            print(f"🔍 チャンネル取得中 (ID: {NOTIFY_CHANNEL_ID})...")
            channel = client.get_channel(NOTIFY_CHANNEL_ID)
            
            if not channel:
                print(f"❌ チャンネルが見つかりません (ID: {NOTIFY_CHANNEL_ID})")
                # fetch_channel でもう一度試す
                try:
                    channel = await client.fetch_channel(NOTIFY_CHANNEL_ID)
                    print(f"✅ fetch_channel で取得成功: {channel.name}")
                except Exception as fetch_error:
                    print(f"❌ fetch_channel でも失敗: {fetch_error}")
                    return
            else:
                print(f"✅ チャンネル見つかりました: {channel.name} (ID: {channel.id})")
            
            # テスト用の簡単なメッセージを送信
            print("📨 テストメッセージ送信中...")
            test_message = f"🧪 テスト通知 - {current_time.strftime('%Y-%m-%d %H:%M:%S')} JST"
            await channel.send(test_message)
            print("✅ テストメッセージ送信成功")
            
            # 実際の予定通知
            if tomorrow_events:
                print("📨 予定通知メッセージ作成中...")
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
            print(f"❌ Discord処理エラー: {str(e)}")
            import traceback
            print(f"詳細エラー:\n{traceback.format_exc()}")
        finally:
            print("🔚 Discord接続を終了します")
            await client.close()
    
    @client.event
    async def on_error(event, *args, **kwargs):
        print(f"❌ Discord イベントエラー: {event}")
        import traceback
        traceback.print_exc()
    
    # Discord ボットを起動
    print("🚀 Discord ボット起動中...")
    try:
        await client.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ Discord ログイン失敗: トークンが無効です")
    except Exception as e:
        print(f"❌ Discord起動エラー: {str(e)}")
        import traceback
        print(f"詳細エラー:\n{traceback.format_exc()}")

if __name__ == "__main__":
    print("🏁 メイン実行開始")
    asyncio.run(send_notification())
    print("🏁 メイン実行終了")
