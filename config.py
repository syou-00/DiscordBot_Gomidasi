import os

# 環境変数からトークンを取得（GitHub Actions用）
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFY_CHANNEL_ID = int(os.getenv('NOTIFY_CHANNEL_ID')) if os.getenv('NOTIFY_CHANNEL_ID') else None

# ローカル開発時の設定（環境変数が設定されていない場合のフォールバック）
if not DISCORD_TOKEN:
    # ローカル開発用 - このファイルはGitHubにアップロードしないでください
    try:
        from config_local import DISCORD_TOKEN, NOTIFY_CHANNEL_ID
    except ImportError:
        print("警告: DISCORD_TOKENが設定されていません")
        print("環境変数またはconfig_local.pyを設定してください")