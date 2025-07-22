import datetime
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# APIに要求する権限を指定
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_tomorrow_events():
  """
  翌日の予定を取得する関数（厳密な日付フィルタリング付き）
  """
  creds = None
  # ユーザーのアクセスとリフレッシュトークンを格納するtoken.jsonファイルが存在する場合、token.jsonを使用して認証する。
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # 有効な資格情報がない場合、ユーザーにログインさせます。
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # 次回実行のために資格情報を保存する。※二回目以降の実行では認証がスキップされる。
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

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
    
    # カレンダーAPIを呼び出します（広めに検索）
    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=tomorrow_start_utc.isoformat(),
        timeMax=tomorrow_end_utc.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,  # 十分な件数を取得
      )
      .execute()
    )
    events = events_result.get("items", [])

    print(f"APIから取得されたイベント数: {len(events)}件")

    if not events:
      print("検索範囲内にイベントはありません。")
      return []

    # 明日の日付に完全一致するイベントのみを厳密にフィルタリング
    tomorrow_events = []
    
    for event in events:
      start_info = event["start"]
      summary = event.get("summary", "タイトルなし")
      
      # イベントの日付を日本時間で解析
      event_date_jst = None
      start_datetime_str = None
      
      if start_info.get("dateTime"):
        # 時刻付きイベント
        start_datetime_str = start_info["dateTime"]
        try:
          # ISO形式の日時文字列を解析
          if start_datetime_str.endswith('Z'):
            event_datetime_utc = datetime.datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
          else:
            event_datetime_utc = datetime.datetime.fromisoformat(start_datetime_str)
            if event_datetime_utc.tzinfo is None:
              event_datetime_utc = event_datetime_utc.replace(tzinfo=pytz.UTC)
          
          event_datetime_jst = event_datetime_utc.astimezone(jst)
          event_date_jst = event_datetime_jst.date()
        except Exception as e:
          print(f"日時解析エラー: {start_datetime_str} - {e}")
          continue
          
      elif start_info.get("date"):
        # 終日イベント
        start_datetime_str = start_info["date"]
        try:
          event_date_jst = datetime.datetime.fromisoformat(start_datetime_str).date()
        except Exception as e:
          print(f"日付解析エラー: {start_datetime_str} - {e}")
          continue
      
      # デバッグ情報を出力
      print(f"イベント: {summary}")
      print(f"  開始: {start_datetime_str}")
      print(f"  日付(JST): {event_date_jst}")
      print(f"  対象日: {tomorrow_jst_date}")
      
      # 明日の日付と完全一致する場合のみ追加
      if event_date_jst == tomorrow_jst_date:
        tomorrow_events.append({
          "start": start_datetime_str,
          "summary": summary
        })
        print(f"  ✅ 追加: 明日の予定")
      else:
        print(f"  ❌ 除外: 日付が一致しない（{event_date_jst} ≠ {tomorrow_jst_date}）")
      print()

    print(f"明日の予定件数: {len(tomorrow_events)}件")
    
    # 結果の表示
    if tomorrow_events:
      print("=== 明日の予定一覧 ===")
      for i, event in enumerate(tomorrow_events, 1):
        print(f"{i}. {event['summary']} ({event['start']})")
    else:
      print("明日の予定はありません。")
    
    return tomorrow_events

  except HttpError as error:
    print(f"Google Calendar APIエラー: {error}")
    return []
  except Exception as error:
    print(f"予期しないエラー: {error}")
    return []

def main():
  """
  ユーザーのカレンダーの現在時刻から10件のイベントの開始日時と名前を表示する。
  """
  creds = None
  # ユーザーのアクセスとリフレッシュトークンを格納するtoken.jsonファイルが存在する場合、token.jsonを使用して認証する。
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # 有効な資格情報がない場合、ユーザーにログインさせます。
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # 次回実行のために資格情報を保存する。※二回目以降の実行では認証がスキップされる。
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # カレンダーAPIを呼び出します。
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z'はUTC時間を示します
    print("次の10件のイベントを取得中")
    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
      )
      .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("次のイベントはありません。")
      return

    # 次の10件のイベントの開始日時と名前を表示します。
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"エラーが発生しました: {error}")


if __name__ == "__main__":
  main()