# google_calendar.py (サービスアカウント版)
import os
import json
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# サービスアカウント用の認証
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_tomorrow_events():
    """
    サービスアカウントを使用して翌日の予定を取得する関数
    """
    try:
        print("🔐 サービスアカウントで認証中...")
        
        # GitHub Secretsからサービスアカウントキーを取得
        service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if not service_account_key:
            print("❌ GOOGLE_SERVICE_ACCOUNT_KEY が設定されていません")
            return []
        
        # JSON文字列をパース
        service_account_info = json.loads(service_account_key)
        print(f"✅ サービスアカウント: {service_account_info.get('client_email', 'Unknown')}")
        
        # サービスアカウントで認証
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        
        service = build("calendar", "v3", credentials=credentials)
        print("✅ Google Calendar API 認証成功")

        # 日本時間で明日の日付を正確に計算
        jst = pytz.timezone('Asia/Tokyo')
        today_jst = datetime.datetime.now(jst).date()
        tomorrow_jst_date = today_jst + datetime.timedelta(days=1)
        
        print(f"今日の日付: {today_jst} (JST)")
        print(f"対象日（明日）: {tomorrow_jst_date} (JST)")
        
        # 明日の0:00から翌々日の0:00まで（日本時間）を検索範囲に設定
        tomorrow_start_jst = datetime.datetime.combine(tomorrow_jst_date, datetime.time.min).replace(tzinfo=jst)
        day_after_tomorrow_jst = tomorrow_jst_date + datetime.timedelta(days=1)
        tomorrow_end_jst = datetime.datetime.combine(day_after_tomorrow_jst, datetime.time.min).replace(tzinfo=jst)
        
        # UTCに変換してAPI検索
        tomorrow_start_utc = tomorrow_start_jst.astimezone(pytz.UTC)
        tomorrow_end_utc = tomorrow_end_jst.astimezone(pytz.UTC)
        
        print(f"検索範囲: {tomorrow_start_utc.isoformat()} から {tomorrow_end_utc.isoformat()} (UTC)")
        
        # カレンダーAPIを呼び出します
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=tomorrow_start_utc.isoformat(),
                timeMax=tomorrow_end_utc.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )
        
        events = events_result.get("items", [])
        print(f"APIから取得されたイベント数: {len(events)}件")
        
        # 明日の日付のイベントのみをフィルタリング
        tomorrow_events = []
        for event in events:
            try:
                # イベントの開始時刻を取得
                start = event.get('start', {})
                if 'dateTime' in start:
                    # 時刻指定のイベント
                    start_datetime = datetime.datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    event_date_jst = start_datetime.astimezone(jst).date()
                elif 'date' in start:
                    # 終日イベント
                    event_date_jst = datetime.datetime.strptime(start['date'], '%Y-%m-%d').date()
                else:
                    print(f"⚠️  開始時刻が不明なイベント: {event.get('summary', '名前なし')}")
                    continue
                
                print(f"イベント: {event.get('summary', '名前なし')}")
                print(f"  日付(JST): {event_date_jst}")
                print(f"  対象日: {tomorrow_jst_date}")
                
                # 明日の日付のイベントのみを追加
                if event_date_jst == tomorrow_jst_date:
                    tomorrow_events.append({
                        'summary': event.get('summary', '名前なし'),
                        'start': start
                    })
                    print(f"  ✅ 追加: 明日の予定")
                else:
                    print(f"  ❌ 除外: 日付が一致しない")
                    
            except Exception as e:
                print(f"⚠️  イベント処理エラー: {event.get('summary', '名前なし')} - {str(e)}")
                continue
        
        print(f"翌日の予定件数: {len(tomorrow_events)}件")
        return tomorrow_events

    except json.JSONDecodeError as e:
        print(f"❌ GOOGLE_SERVICE_ACCOUNT_KEY のJSON形式が無効です: {e}")
        return []
    except HttpError as error:
        print(f"❌ Google Calendar API エラー: {error}")
        error_details = error.error_details if hasattr(error, 'error_details') else []
        for detail in error_details:
            print(f"  - {detail}")
        return []
    except Exception as error:
        print(f"❌ 予期しないエラー: {error}")
        import traceback
        print(f"詳細エラー:\n{traceback.format_exc()}")
        return []

# Google Calendar から特定タイプの次のイベントを取得
def get_next_event():
    """次のイベントを取得"""
    return get_tomorrow_events()

def get_event_by_type(event_type):
    """特定タイプのイベントを取得"""
    events = get_tomorrow_events()
    for event in events:
        if event_type in event['summary']:
            return event
    return None

def format_event_message(event):
    """イベントをメッセージ形式にフォーマット"""
    if not event:
        return None
    return f"明日は **{event['summary']}** の予定があります"

if __name__ == "__main__":
    print("=== Google Calendar サービスアカウント認証テスト ===")
    events = get_tomorrow_events()
    if events:
        print("\n明日の予定:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['summary']}")
    else:
        print("\n明日の予定はありません。")