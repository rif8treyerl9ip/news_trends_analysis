from linebot import LineBotApi
from linebot.models import TextSendMessage
import json
import time
from datetime import datetime

# 現在の日付を取得
current_date = datetime.now().strftime('%Y%m%d')
print(current_date)
# JSONファイルのパス
config_file_path = r'C:\Users\thyt\confidential_files\Line\Japan Trends news\config.json'

# JSONファイルを開いてアクセス情報を読み込む
with open(config_file_path, 'r') as file:
    data = json.load(file)
    access_token = data['access_token']  # access_tokenの値を取得
    chennel_user_id = data['chennel_user_id']  # my_user_idの値を取得

# LineBotApiオブジェクトを作成
line_bot_api = LineBotApi(access_token)

# ニュースレポートファイルのパス
news_report_file_path = rf"C:\Users\thyt\Learning\Learning_py\news_trends_analysis\src\scripts\news_report\{current_date}_Yesterday's_Trending_News_Report.txt"

# ニュースレポートファイルを開いて内容を読み込む
with open(news_report_file_path, 'r', encoding='utf-8') as file:
    message = file.read()

# ニュースレポートの内容をLINEで送信
line_bot_api.push_message(chennel_user_id, TextSendMessage(text=message))


# 5秒待機
time.sleep(5)

# スクリプトを終了
print("Line botへのメッセージ送信が完了しました。このスクリプトは5秒後に自動的に終了します。")