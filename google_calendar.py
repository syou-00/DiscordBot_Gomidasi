# google_calendar.py (ハイブリッド版)
import os
import json
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# サービスアカウント用の認証
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_google_calendar_events():
    """Google Calendarから明日の予定を取得"""
    try:
        print("🔐 Google Calendar認証中...")
        
        service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if not service_account_key:
            print("⚠️ GOOGLE_SERVICE_ACCOUNT_KEY が設定されていません")
            return []
        
        service_account_info = json.loads(service_account_key)
        print(f"✅ サービスアカウント: {service_account_info.get('client_email', 'Unknown')}")
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        
        service = build("calendar", "v3", credentials=credentials)
        print("✅ Google Calendar API 認証成功")

        # 明日の日付範囲を計算
        jst = pytz.timezone('Asia/Tokyo')
        today_jst = datetime.datetime.now(jst).date()
        tomorrow_jst_date = today_jst + datetime.timedelta(days=1)
        
        print(f"Google Calendar検索対象: {tomorrow_jst_date}")
        
        tomorrow_start_jst = datetime.datetime.combine(tomorrow_jst_date, datetime.time.min).replace(tzinfo=jst)
        tomorrow_end_jst = datetime.datetime.combine(tomorrow_jst_date, datetime.time.max).replace(tzinfo=jst)
        
        tomorrow_start_utc = tomorrow_start_jst.astimezone(pytz.UTC)
        tomorrow_end_utc = tomorrow_end_jst.astimezone(pytz.UTC)
        
        # カレンダー一覧を取得
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"利用可能なカレンダー: {len(calendars)}個")
        
        all_events = []
        
        # 各カレンダーから予定を取得
        for calendar in calendars:
            calendar_id = calendar['id']
            calendar_name = calendar.get('summary', 'Unknown')
            access_role = calendar.get('accessRole', 'Unknown')
            
            if access_role not in ['reader', 'writer', 'owner']:
                continue
            
            try:
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=tomorrow_start_utc.isoformat(),
                    timeMax=tomorrow_end_utc.isoformat(),
                    singleEvents=True,
                    orderBy='startTime',
                    maxResults=50
                ).execute()
                
                events = events_result.get('items', [])
                
                for event in events:
                    start = event.get('start', {})
                    
                    if 'dateTime' in start:
                        start_datetime = datetime.datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                        event_date_jst = start_datetime.astimezone(jst).date()
                    elif 'date' in start:
                        event_date_jst = datetime.datetime.strptime(start['date'], '%Y-%m-%d').date()
                    else:
                        continue
                    
                    if event_date_jst == tomorrow_jst_date:
                        all_events.append({
                            'summary': event.get('summary', '名前なし'),
                            'start': start,
                            'calendar': calendar_name,
                            'source': 'google_calendar'
                        })
                        print(f"✅ Google予定: {event.get('summary', '名前なし')} ({calendar_name})")
                        
            except HttpError as e:
                print(f"⚠️ カレンダー '{calendar_name}' アクセスエラー: {e}")
                continue
        
        print(f"Google Calendarから取得: {len(all_events)}件")
        return all_events

    except Exception as error:
        print(f"❌ Google Calendar エラー: {error}")
        return []

def get_fixed_schedule_events():
    """固定スケジュールから明日の予定を取得"""
    try:
        print("📅 固定スケジュール確認中...")
        
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.datetime.now(jst).date() + datetime.timedelta(days=1)
        weekday = tomorrow.weekday()  # 0=月曜日, 6=日曜日
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        print(f"明日: {tomorrow_str} ({weekday_names[weekday]}曜日)")
        
        # 曜日別の基本スケジュール（地域に応じて調整）
        weekly_schedule = {
            0: ['家庭ごみ'],  # 月曜日
            1: ['プラごみ'],                              # 火曜日
            2: ['瓶、缶、ペットごみ'],                     # 水曜日
            3: ['燃えるごみ'],                              # 木曜日
            4: [],                       # 金曜日
            5: [],                              # 土曜日
            6: []                               # 日曜日
        }
        

        
        events = []
        
        # 曜日ベースの予定
        if weekday in weekly_schedule:
            for task in weekly_schedule[weekday]:
                events.append({
                    'summary': task,
                    'start': {'date': tomorrow_str},
                    'source': 'fixed_schedule',
                    'type': 'weekly'
                })
                print(f"📅 定期予定: {task}")
        
        # 特定日付の予定
        if tomorrow_str in special_dates:
            for task in special_dates[tomorrow_str]:
                events.append({
                    'summary': task,
                    'start': {'date': tomorrow_str},
                    'source': 'fixed_schedule',
                    'type': 'special'
                })
                print(f"📅 特別予定: {task}")
        
        print(f"固定スケジュールから取得: {len(events)}件")
        return events
        
    except Exception as error:
        print(f"❌ 固定スケジュール エラー: {error}")
        return []

def get_tomorrow_events():
    """
    ハイブリッドシステム: Google Calendar + 固定スケジュール
    """
    print("🔄 ハイブリッドシステムで予定取得開始...")
    
    all_events = []
    
    # 1. Google Calendarから取得を試行
    google_events = get_google_calendar_events()
    if google_events:
        all_events.extend(google_events)
    
    # 2. 固定スケジュールから取得
    fixed_events = get_fixed_schedule_events()
    
    # 3. 重複チェックして固定スケジュールを追加
    for fixed_event in fixed_events:
        fixed_summary = fixed_event['summary'].lower()
        
        # Google予定と重複しているかチェック
        is_duplicate = False
        for google_event in google_events:
            google_summary = google_event['summary'].lower()
            # 部分一致で重複判定（例: "ごみ"が含まれているかどうか）
            if any(keyword in google_summary for keyword in ['ごみ', 'ゴミ', 'プラスチック', '紙']) and \
               any(keyword in fixed_summary for keyword in ['ごみ', 'ゴミ', 'プラスチック', '紙']):
                is_duplicate = True
                print(f"🔄 重複スキップ: {fixed_event['summary']} (Google予定と重複)")
                break
        
        if not is_duplicate:
            all_events.append(fixed_event)
    
    # 4. 結果まとめ
    google_count = len(google_events)
    fixed_count = len([e for e in all_events if e.get('source') == 'fixed_schedule'])
    
    print(f"\n📊 ハイブリッド結果:")
    print(f"  Google Calendar: {google_count}件")
    print(f"  固定スケジュール: {fixed_count}件")
    print(f"  合計: {len(all_events)}件")
    
    if all_events:
        print("📋 明日の予定一覧:")
        for event in all_events:
            source = event.get('source', 'unknown')
            source_label = {'google_calendar': 'Google', 'fixed_schedule': '固定'}
            print(f"  ✅ {event['summary']} ({source_label.get(source, source)})")
    
    return all_events

# 下位互換性のための関数
def get_next_event():
    """次のイベントを取得（下位互換性）"""
    return get_tomorrow_events()

def get_event_by_type(event_type):
    """特定タイプのイベントを取得（下位互換性）"""
    events = get_tomorrow_events()
    for event in events:
        if event_type in event['summary']:
            return event
    return None

def format_event_message(event):
    """イベントをメッセージ形式にフォーマット（下位互換性）"""
    if not event:
        return None
    return f"明日は **{event['summary']}** の予定があります"

if __name__ == "__main__":
    print("=== ハイブリッド Google Calendar システム ===")
    events = get_tomorrow_events()
    
    if events:
        print(f"\n🎯 明日の予定 ({len(events)}件):")
        for i, event in enumerate(events, 1):
            source = event.get('source', 'unknown')
            source_icon = {'google_calendar': '📱', 'fixed_schedule': '📅'}
            print(f"{i}. {source_icon.get(source, '❓')} {event['summary']}")
    else:
        print("\n📭 明日の予定はありません。")