import asyncio
import discord
import os
import datetime
import pytz

def get_week_of_month(date):
    """月の第何週目かを取得"""
    week_number = (date.day - 1) // 7 + 1
    return week_number

def get_fallback_schedule():
    """完全フォールバック: 最小限の固定スケジュール"""
    try:
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.datetime.now(jst).date() + datetime.timedelta(days=1)
        weekday = tomorrow.weekday()
        week_of_month = get_week_of_month(tomorrow)
        
        events = []
        
        # 地域のごみ出しスケジュール
        if weekday == 0:  # 月曜日
            events.append({
                'summary': '燃えるごみ',
                'start': {'date': tomorrow.strftime('%Y-%m-%d')},
                'source': 'fallback'
            })
        elif weekday == 1:  # 火曜日
            events.append({
                'summary': 'プラスチックごみ',
                'start': {'date': tomorrow.strftime('%Y-%m-%d')},
                'source': 'fallback'
            })
        elif weekday == 2:  # 水曜日
            events.append({
                'summary': '瓶・缶・ペットボトルごみ',
                'start': {'date': tomorrow.strftime('%Y-%m-%d')},
                'source': 'fallback'
            })
            # 2週目と4週目は紙ごみも
            if week_of_month in [2, 4]:
                events.append({
                    'summary': '紙ごみ',
                    'start': {'date': tomorrow.strftime('%Y-%m-%d')},
                    'source': 'fallback'
                })
        elif weekday == 3:  # 木曜日
            events.append({
                'summary': '燃えるごみ',
                'start': {'date': tomorrow.strftime('%Y-%m-%d')},
                'source': 'fallback'
            })
        
        return events
        
    except Exception:
        return []

async def send_notification():
    """ハイブリッドシステムによる予定通知"""
    
    print("🏁 メイン実行開始")
    print("=== ハイブリッド通知スクリプト開始 ===")
    
    # 環境変数の確認
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    NOTIFY_CHANNEL_ID_STR = os.getenv('NOTIFY_CHANNEL_ID')
    
    print(f"DISCORD_TOKEN存在: {DISCORD_TOKEN is not None}")
    print(f"NOTIFY_CHANNEL_ID_STR: {'***' if NOTIFY_CHANNEL_ID_STR else 'None'}")
    
    if not DISCORD_TOKEN or not NOTIFY_CHANNEL_ID_STR:
        print("❌ 必要な環境変数が設定されていません")
        return
    
    try:
        NOTIFY_CHANNEL_ID = int(NOTIFY_CHANNEL_ID_STR)
        print(f"NOTIFY_CHANNEL_ID: {'***' if NOTIFY_CHANNEL_ID else 'None'}")
    except ValueError:
        print("❌ NOTIFY_CHANNEL_ID が無効な数値です")
        return
    
    # 現在時刻表示
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.datetime.now(jst)
    print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')} JST")
    
    # ハイブリッドシステムで予定取得
    tomorrow_events = []
    calendar_status = "✅ 接続成功"
    
    try:
        print("📅 ハイブリッドシステム開始...")
        
        # google_calendar モジュールをインポート
        try:
            import google_calendar
            print("✅ google_calendar モジュールのインポート成功")
        except ImportError as e:
            print(f"❌ google_calendar モジュールのインポートエラー: {e}")
            # フォールバック: 固定スケジュールのみ
            tomorrow_events = get_fallback_schedule()
            calendar_status = "⚠️ 固定スケジュールのみ"
        else:
            # ハイブリッドシステムで予定取得
            tomorrow_events = google_calendar.get_tomorrow_events()
            calendar_status = "✅ ハイブリッドシステム"
        
        if tomorrow_events:
            print("📋 取得した予定:")
            for i, event in enumerate(tomorrow_events):
                source = event.get('source', 'unknown')
                source_icon = {'google_calendar': '📱', 'fixed_schedule': '📅', 'fallback': '🔄'}
                print(f"  {i+1}. {source_icon.get(source, '❓')} {event.get('summary', '名前なし')}")
        else:
            print("📭 明日の予定はありません")
            
    except Exception as e:
        print(f"⚠️ ハイブリッドシステム エラー: {str(e)}")
        # 完全フォールバック
        tomorrow_events = get_fallback_schedule()
        calendar_status = "⚠️ フォールバック動作"
    
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
                print("⚠️ get_channel で見つからないため fetch_channel を試行...")
                channel = await client.fetch_channel(NOTIFY_CHANNEL_ID)
            
            print(f"✅ チャンネル見つかりました: {channel.name}")
            
            # 通知メッセージを作成
            if tomorrow_events:
                # 予定ありの場合
                event_messages = []
                google_count = 0
                fixed_count = 0
                fallback_count = 0
                
                for event in tomorrow_events:
                    source = event.get('source', 'unknown')
                    if source == 'google_calendar':
                        google_count += 1
                        event_messages.append(f"📱 **{event['summary']}**")
                    elif source == 'fixed_schedule':
                        fixed_count += 1
                        event_messages.append(f"📅 **{event['summary']}**")
                    elif source == 'fallback':
                        fallback_count += 1
                        event_messages.append(f"🔄 **{event['summary']}**")
                    else:
                        event_messages.append(f"❓ **{event['summary']}**")
                
                # システム情報
                system_info = []
                if google_count > 0:
                    system_info.append(f"📱 Google Calendar: {google_count}件")
                if fixed_count > 0:
                    system_info.append(f"📅 固定スケジュール: {fixed_count}件")
                if fallback_count > 0:
                    system_info.append(f"🔄 フォールバック: {fallback_count}件")
                
                notification_text = f"""📅 **明日の予定** ({len(tomorrow_events)}件)

{chr(10).join(event_messages)}

🔄 **システム状況**: {calendar_status}
📊 **内訳**: {' / '.join(system_info)}
🕘 **通知時刻**: {current_time.strftime('%Y年%m月%d日 %H:%M')}"""
                
                await channel.send(notification_text)
                print(f"✅ 予定通知を送信しました: {len(tomorrow_events)}件")
                
            else:
                # 予定なしの場合
                notification_text = f"""📅 **明日の予定**

明日の予定はありません。

🔄 **システム状況**: {calendar_status}
🕘 **通知時刻**: {current_time.strftime('%Y年%m月%d日 %H:%M')}"""
                
                await channel.send(notification_text)
                print("✅ 予定なし通知を送信しました")
                
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
    asyncio.run(send_notification())
    print("🏁 メイン実行終了")
