# token_refresh.py
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def refresh_google_token():
    """Google Calendar APIトークンをリフレッシュ"""
    print("=== Google トークンリフレッシュ開始 ===")
    
    # credentials.jsonの存在確認
    if not os.path.exists("credentials.json"):
        print("❌ credentials.jsonが見つかりません")
        return False
    
    print("✅ credentials.json確認完了")
    
    # token.jsonの存在確認
    if not os.path.exists("token.json"):
        print("❌ token.jsonが見つかりません")
        print("💡 初回認証が必要です。ローカルでgoogle_calendar.pyを実行してください。")
        return False
    
    print("✅ token.json確認完了")
    
    try:
        # 既存のトークンを読み込み
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        print(f"トークン有効性: {creds.valid}")
        print(f"トークン期限切れ: {creds.expired}")
        print(f"リフレッシュトークン存在: {bool(creds.refresh_token)}")
        
        if creds and creds.expired and creds.refresh_token:
            print("🔄 リフレッシュトークンを使用してトークンを更新中...")
            
            # トークンをリフレッシュ
            creds.refresh(Request())
            
            # 更新されたトークンを保存
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            
            print("✅ トークンリフレッシュ成功")
            
            # 更新されたトークンの内容を表示
            with open("token.json", "r") as token:
                token_content = token.read()
                print("\n" + "="*50)
                print("新しいトークン（GitHub Secretsにコピーしてください）:")
                print("="*50)
                print(token_content)
                print("="*50)
            
            return True
        
        elif creds.valid:
            print("✅ トークンは既に有効です")
            
            # 現在のトークンの内容を表示
            with open("token.json", "r") as token:
                token_content = token.read()
                print("\n" + "="*50)
                print("現在のトークン（確認用）:")
                print("="*50)
                print(token_content)
                print("="*50)
            
            return True
        
        else:
            print("❌ トークンが無効で、リフレッシュトークンもありません")
            print("💡 再認証が必要です。ローカルでgoogle_calendar.pyを実行してください。")
            return False
            
    except Exception as e:
        print(f"❌ トークンリフレッシュエラー: {str(e)}")
        import traceback
        print(f"詳細エラー:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🏁 トークンリフレッシュスクリプト開始")
    success = refresh_google_token()
    if success:
        print("🎉 トークンリフレッシュ完了")
    else:
        print("❌ トークンリフレッシュ失敗")
    print("🏁 スクリプト終了")