#!/usr/bin/env python
# coding: utf-8

# ## 業務フロー: ニュース収集とトレンド分析
# 
# ### ステップ 1: コンフィグファイルの読み込み
# - `load_config` 関数を使って、指定されたパスから JSON コンフィグを読み込む。
# - 各種のコンフィグファイル（OpenAI, Google Cloud, NewsAPI）のパスを指定し、読み込む。
# 
# ### ステップ 2: APIキーの設定
# - OpenAI、NewsAPI の API キーを設定する。
# 
# ### ステップ 3: Google BigQuery クライアントの初期化
# - Google BigQuery クライアントを初期化し、プロジェクト ID を設定する。
# 
# ### ステップ 4: BigQuery からトレンドデータの取得
# - BigQuery を使用して、日本の最新のトレンドデータを取得する。
# 
# ### ステップ 5: トレンド用語の取得と表示
# - 取得したトレンドデータから上位 10 位までの用語を取得し、表示する。
# 
# ### ステップ 6: トレンドキーワードに関連するニュースの収集
# - 各トレンドキーワードに関連するニュースを NewsAPI を使用して収集する。
# - 収集する際には、日本の主要な新聞・テレビ・オンラインメディアのドメインを対象とする。
# 
# ### ステップ 7: ニュースの要約と報告
# - 収集したニュースデータを要約し、報告する。
# - このプロセスは、上位のトレンドキーワードに対して繰り返される。
# 
# ### ステップ 8: LINEメッセージ送信
# - LINE Bot API を利用して、設定されたユーザーに対してニュース更新通知を送信する。
# - ファイルパスからコンフィグファイルを読み込み、LINEのアクセストークンとユーザーIDを取得する。
# - 取得したアクセストークンを使い、LINE Bot APIを初期化する。
# - 指定されたユーザーIDに対して「Hello, this is an update from Japan Trends News!」というメッセージを送信する。
# 
# ---
# 
# この追加により、業務フローにLINEを介した通知機能が組み込まれました。これによって、ニュースの要約と報告が完了した後、関連する情報がLINEメッセージとして指定されたユーザーに自動的に送信されます。

# In[2]:


import json
import urllib.parse
import re
import requests
from datetime import datetime, timedelta
from tqdm import tqdm

import pandas as pd
import openai
from google.cloud import bigquery

# Getting the current date and time
current_date = datetime.now().strftime("%Y%m%d")

def load_config(file_path):
    """ 指定されたファイルパスからJSONコンフィグを読み込む """
    with open(file_path, 'r') as file:
        return json.load(file)

# 各種コンフィグファイルのパス
openai_config_path = 'C:\\Users\\thyt\\confidential_files\\Openai\\config.json'
google_config_path = 'C:\\Users\\thyt\\confidential_files\\Google_cloud\\config.json'
newsapi_config_path = 'C:\\Users\\thyt\\confidential_files\\Newsapi\\config.json'

# コンフィグの読み込み
openai_config = load_config(openai_config_path)
google_config = load_config(google_config_path)
newsapi_config = load_config(newsapi_config_path)

# APIキーの設定
openai.api_key = openai_config.get('API_KEY')
news_api_key = newsapi_config['API_KEY']


# In[3]:


# Google BigQueryクライアントの初期化
google_project_id = google_config['project_id_1']
client = bigquery.Client(project=google_project_id)

# BigQueryからトレンドデータを取得
# データセット：https://console.cloud.google.com/marketplace/product/bigquery-public-datasets/google-trends-intl?hl=ja&project=gcpyoutube
get_latest_japan_trends = """
WITH RecentJapanTrends AS (
    SELECT *
    FROM `bigquery-public-data.google_trends.international_top_terms`
    WHERE
        refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        AND country_name = 'Japan'
)
SELECT 
    MAX(term) AS term,
    rank
FROM RecentJapanTrends
WHERE
    week = (SELECT MAX(week) FROM RecentJapanTrends)
GROUP BY    
    rank
ORDER BY 
    rank ASC;
"""

# クエリの実行とDataFrameへの変換
df = client.query(get_latest_japan_trends).to_dataframe()

# 上位10位までの用語の取得
top_10_terms = df.head(10)['term'].tolist()

# 結果の表示
print("上位10位のトレンド用語についてニュースを生成します。:")
for i, term in enumerate(top_10_terms, 1):
    print(f"{i}. {term}")


# In[4]:

# トレンドキーワードに関連する最新ニュースの要約と報告
header_text = 'こんにちは！昨日話題になったトレンドのニュースをお届けします。興味のある話題が見つかるかもしれませんね。\n\n'

index = 1  # インデックスの初期値を7に設定

for term in tqdm(top_10_terms):
    
    # ドキュメントURL: https://newsapi.org/docs
    # News APIのエンドポイントURL
    # base_url = 'https://newsapi.org/v2/top-headlines'
    base_url = "https://newsapi.org/v2/everything"
    news_api_key = newsapi_config['API_KEY']

    # News APIリクエストのパラメータ設定
    params = {
        'q': f'"{term}"',  # 二重引用符で囲むと完全一致の記事
        # 'sortBy': 'publishedAt',
        'sortBy': 'relevancy',
        'domains': ','.join([# 新聞・報道メディア:
                    'asahi.com',  # : 朝日新聞 (Asahi Shimbun)
                    'yomiuri.co.jp',  # : 読売新聞 (Yomiuri Shimbun)
                    'mainichi.jp',  # : 毎日新聞 (Mainichi Shimbun)
                    'nikkei.com',  # : 日本経済新聞 (Nikkei)
                    'sankei.com',  # : 産業経済新聞 (Sankei Shimbun)
                    'tokyo-np.co.jp',  # : 東京新聞 (Tokyo Shimbun)
                    'nikkansports.com',  # : 日刊スポーツ (Nikkan Sports)
                    'hochi.news',  # : スポーツ報知 (Sports Hochi)
                # テレビ・放送メディア:
                    'news.tbs.co.jp',  # : TBS News
                    'fujitv.co.jp',  # : フジテレビ (Fuji Television)
                    'ntv.co.jp',  # : 日本テレビ (Nippon Television)
                    'tv-asahi.co.jp',  # : テレビ朝日 (TV Asahi)
                    'tv-tokyo.co.jp',  # : テレビ東京 (TV Tokyo)
                    'nhk.or.jp',  # : NHK (日本放送協会)
                # オンラインメディア:
                    'reallive.jp',  # : リアルライブ (Real Live)
                    'j-cast.com',  # : J-CASTニュース (J-CAST News)
                    'itmedia.co.jp',  # : ITmedia (IT Media)
                    'japanese.engadget.com',  # : Engadget 日本版 (Engadget Japanese Edition)
                    'buzzfeed.com',  # /jp: BuzzFeed Japan
                    'prtimes.jp',  # : PR TIMES
                # ビジネス・経済メディア:
                    'toyokeizai.net',  # : 東洋経済オンライン (Toyo Keizai Online)
                    'business-journal.jp',  # : ビジネスジャーナル (Business Journal)
                    'diamond.jp',  # : ダイヤモンド・オンライン (Diamond Online)
                    'forbesjapan.com',  # : Forbes Japan
                    'japan.cnet.com',  # : CNET Japan
                    'meti.go.jp',  # : 経済産業省 (Ministry of Economy, Trade and Industry)
                    'keidanren.or.jp',  # : 日本経済団体連合会 (Keidanren)
                # ウェブポータル・総合情報サイト:
                    'news.yahoo.co.jp',  # : Yahoo! Japan ニュース
                    'finance.yahoo.co.jp',  # : Yahoo! Japan ファイナンス
                    'news.livedoor.com',  # : ライブドアニュース (Livedoor News)
                    'livedoor.com',
                    'news.mynavi.jp',  # : マイナビニュース (Mynavi News)
                    'infoseek.co.jp',  # : Infoseek ニュース
                    'news.nifty.com',  # : @nifty ニュース
                    'news.goo.ne.jp',  # : goo ニュース
                    'goo.ne.jp',
                    'news.biglobe.ne.jp',  # : BIGLOBEニュース
                    'bloomberg.co.jp',  # : Bloomberg Japan
                    'sankei.news.msn.com',  # : MSN産経ニュース (MSN Sankei News)
                    'oricon.co.jp',  # : オリコン (Oricon)
                ]),
        'pageSize': 1,
        'apiKey': news_api_key
    }

    url_with_params = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = requests.get(url_with_params)
    data = response.json()

    # 記事が見つかった場合の処理
    if response.ok and len(data['articles']) > 0:
        article = data['articles'][0]

        # 記事の要約をリクエストするためのプロンプト作成
        prompt = f"以下のテキストを、100文字程度で要約してください：\n{article['description']}\n要約（箇条書き）："

        # パラメータの設定
        parameters = {
            'engine': 'gpt-3.5-turbo',
            'max_tokens': 300,
            'temperature': 0.7,
            'stop': None,  # ここで適切なストップトークンまたはシーケンスを指定できます
        }

        # APIを呼び出す
        response = openai.ChatCompletion.create(
            model=parameters['engine'],
            messages=[
                {"role": "system", "content": "あなたは助けになるアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=parameters['max_tokens'],
            temperature=parameters['temperature'],
            stop=parameters['stop'],
        )

        filename = f"C:/Users/thyt/Learning/Learning_py/news_trends_analysis/src/scripts/news_report/{current_date}_Yesterday's_Trending_News_Report.txt"

        summary = response['choices'][0]['message']['content']
        # print(f" {response['choices'][0]['message']['content']}")

        # 先頭行の置換
        head = summary.split('\n')[0]  # 先頭行とそれ以外に分割
        head = re.sub(r'^\s*-\s*', '\n  ・  ', head)

        # それ以外の行の置換
        tails = summary.split('\n')[1:]
        tails = [re.sub(r'^\s*-\s*', '\n  ・  ', tail) for tail in tails]
        tails = ''.join(tails)

        # # 結果の結合
        modefied_summary = head + tails

        output = f"""{index}. トレンド：{term}\n・タイトル：{article['title']}\n・URL：{article['url']}\n・概要：{modefied_summary}\n\n"""

        header_text += output
        index += 1
    else:
        print(f'{term}: ニュースが見つかりませんでした。')

# ファイル名の生成（例：'2023-04-10_Yesterday's Trending News Report Created Today.TXT'）
filename = f"C:/Users/thyt/Learning/Learning_py/news_trends_analysis/src/scripts/news_report/{current_date}_Yesterday's_Trending_News_Report.txt"

# テキストファイルに書き込み
with open(filename, 'w', encoding='utf-8') as file:
    file.write(header_text)

# 完成したニュースレポートの表示
# print(header_text)