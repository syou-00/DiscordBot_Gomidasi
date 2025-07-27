import asyncio
import discord
import os
from datetime import datetime

async def send_notification():
    """GitHub Actions用の通知スクリプト（エラーハンドリング強化版）"""
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
    except ValueError as e:
        print(f"❌ NOTIFY_CHANNEL_IDが無効な数値です: {e}")
        return
    
    # 現在の日本時間を取得
    try:
        import pytz
        jst = pytz.timezone('Asia/Tokyo')
        current_time = datetime.now(jst)
    except ImportError:
        # pytzがない場合はUTC+9として計算
        from datetime import timedelta
        current_time = datetime.utcnow() + timedelta(hours=9)
    
    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} JST")
    
    # Google Calendar の予定を取得（エラー時は空リスト）
    tomorrow_events = []
    calendar_status = "❌ 利用不可"
    
    print("📅 Google Calendar 接続テスト開始...")
    try:
        from google_calendar import get_tomorrow_events
        print("✅ google_calendar モジュールのインポート成功")
        
        tomorrow_events = get_tomorrow_events()
        print(f"✅ 予定取得成功: {len(tomorrow_events) if tomorrow_events else 0}件")
        calendar_status = "✅ 正常"
        
        if tomorrow_events:
            print("📋 取得した予定:")
            for i, event in enumerate(tomorrow_events):
                print(f"  {i+1}. {event.get('summary', '名前なし')}")
        else:
            print("📭 明日の予定はありません")
            
    except Exception as e:
        print(f"⚠️ Google Calendar エラー: {str(e)}")
        if "invalid_grant" in str(e) or "expired" in str(e):
            calendar_status = "🔄 トークン更新が必要"
        else:
            calendar_status = "❌ 接続エラー"
        # エラーでもDiscord通知は続行
    
    # Discord クライアントを設定
    print("🔧 Discord クライアント設定中...")
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Discordにログインしました: {client.user}")
        
        try:
            # チャンネルを取得
            print(f"🔍 チャンネル取得中 (ID: {NOTIFY_CHANNEL_ID})...")
            channel = client.get_channel(NOTIFY_CHANNEL_ID)
            
            if not channel:
                channel = await client.fetch_channel(NOTIFY_CHANNEL_ID)
            
            print(f"✅ チャンネル見つかりました: {channel.name}")
            
            # 通知メッセージを作成
            if tomorrow_events:
                # 予定がある場合
                messages = []
                for event in tomorrow_events:
                    messages.append(f"明日は **{event['summary']}** の予定があります")
                
                notification_text = f"""📅 **明日の予定**

{chr(10).join(messages)}

🕘 **通知時刻**: {current_time.strftime('%Y年%m月%d日 %H:%M')}"""
                
                await channel.send(notification_text)
                print(f"✅ 予定通知を送信しました: {len(tomorrow_events)}件の予定")
                
            else:
                # 予定がない場合（Google Calendarが正常な場合のみ通知）
                if calendar_status == "✅ 正常":
                    notification_text = f"""📅 **明日の予定**

明日の予定はありません。

🕘 **通知時刻**: {current_time.strftime('%Y年%m月%d日 %H:%M')}"""
                    
                    await channel.send(notification_text)
                    print("✅ 予定なし通知を送信しました")
                else:
                    # Google Calendarエラー時のステータス通知
                    status_message = f"""🤖 **システム状況**

📅 Google Calendar: {calendar_status}
💬 Discord通知: ✅ 正常稼働

🕘 **確認時刻**: {current_time.strftime('%Y年%m月%d日 %H:%M')}

💡 Google Calendarのトークン更新が必要な場合があります。"""
                    
                    await channel.send(status_message)
                    print("✅ システム状況通知を送信しました")
                
        except Exception as e:
            print(f"❌ Discord処理エラー: {str(e)}")
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
    print("🏁 メイン実行開始")
    asyncio.run(send_notification())
    print("🏁 メイン実行終了")
