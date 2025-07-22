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
  翌日の予定を取得する関数
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

    # 日本時間基準で翌日の開始と終了時刻を設定
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.datetime.now(jst)
    tomorrow_jst = now_jst + datetime.timedelta(days=1)
    
    # 翌日の0時から23時59分まで（日本時間）
    tomorrow_start_jst = tomorrow_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end_jst = tomorrow_jst.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # UTCに変換
    tomorrow_start_utc = tomorrow_start_jst.astimezone(pytz.UTC)
    tomorrow_end_utc = tomorrow_end_jst.astimezone(pytz.UTC)
    
    print(f"翌日の予定を取得中... ({tomorrow_start_jst.strftime('%Y-%m-%d')} JST)")
    print(f"検索範囲: {tomorrow_start_utc.isoformat()} から {tomorrow_end_utc.isoformat()}")
    
    # カレンダーAPIを呼び出します。
    events_result = (
      service.events()
      .list(
        calendarId="primary",
        timeMin=tomorrow_start_utc.isoformat(),
        timeMax=tomorrow_end_utc.isoformat(),
        singleEvents=True,
        orderBy="startTime",
      )
      .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("翌日の予定はありません。")
      return []

    # 翌日の予定のみを厳密にフィルタリング
    tomorrow_events = []
    tomorrow_date_jst = tomorrow_start_jst.date()
    
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      summary = event.get("summary", "タイトルなし")
      
      # イベントの日付を解析（日本時間基準）
      event_date_jst = None
      if event["start"].get("dateTime"):
        # 時刻付きイベント
        event_datetime_utc = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        event_datetime_jst = event_datetime_utc.astimezone(jst)
        event_date_jst = event_datetime_jst.date()
      elif event["start"].get("date"):
        # 終日イベント
        event_date_jst = datetime.datetime.fromisoformat(start).date()
      
      # 翌日の日付（日本時間）と一致する場合のみ追加
      if event_date_jst == tomorrow_date_jst:
        tomorrow_events.append({
          "start": start,
          "summary": summary
        })
        print(f"翌日の予定: {start} - {summary}")
      else:
        print(f"除外: {start} - {summary} (日付: {event_date_jst}, 対象日: {tomorrow_date_jst})")

    print(f"翌日の予定件数: {len(tomorrow_events)}件")
    return tomorrow_events

  except HttpError as error:
    print(f"エラーが発生しました: {error}")
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