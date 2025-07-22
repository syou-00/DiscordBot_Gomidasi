import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class CalendarBot:
    """Discord Bot用のGoogle Calendar統合クラス"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Google Calendar APIの認証を行う"""
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_next_event(self, event_type=None):
        """次のイベントを取得する"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            
            query = {}
            if event_type:
                query['q'] = event_type
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=1,
                singleEvents=True,
                orderBy='startTime',
                showDeleted=False,
                **query
            ).execute()
            
            events = events_result.get('items', [])
            if events:
                return events[0]
            return None
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def format_event_message(self, event):
        """イベント情報をメッセージ形式にフォーマットする"""
        if not event:
            return None  # 予定がない場合はNoneを返す
        
        summary = event.get('summary', 'タイトルなし')
        start = event['start']
        
        if 'dateTime' in start:
            dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            date_str = dt.strftime('%m月%d日 %H時%M分')
        elif 'date' in start:
            dt = datetime.fromisoformat(start['date'])
            date_str = dt.strftime('%m月%d日')
        else:
            date_str = '日付不明'
        
        return f"次の{summary}は{date_str}です"
    
    def check_tomorrow_events(self):
        """明日のイベントをチェックする"""
        try:
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=tomorrow_start.isoformat() + 'Z',
                timeMax=tomorrow_end.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                showDeleted=False
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def format_tomorrow_notification(self):
        """翌日の予定通知をフォーマットする"""
        tomorrow_events = self.check_tomorrow_events()
        
        if not tomorrow_events:
            return None  # 予定がない場合はNoneを返す
        
        messages = []
        for event in tomorrow_events:
            summary = event.get('summary', 'タイトルなし')
            messages.append(f"明日は{summary}の日です")
        
        return "\n".join(messages)
    
    def get_event_by_type(self, event_type):
        """特定のタイプのイベントを取得する"""
        event_types = {
            "家庭": "家庭ごみ",
            "プラスチック": "プラスチックごみ", 
            "紙": "紙ごみ"
        }
        
        query = event_types.get(event_type, event_type)
        return self.get_next_event(query)

# グローバルインスタンス
calendar_bot = None

def get_calendar_bot():
    """CalendarBotのシングルトンインスタンスを取得"""
    global calendar_bot
    if calendar_bot is None:
        calendar_bot = CalendarBot()
    return calendar_bot
