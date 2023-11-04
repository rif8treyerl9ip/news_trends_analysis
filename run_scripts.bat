@REM @echo off

cd C:\Users\thyt\normal
poetry run python C:\Users\thyt\Learning\Learning_py\news_trends_analysis\src\scripts\daily_japan_trends_to_news_report.py

cd C:\Users\thyt\DevEnv
poetry run python C:\Users\thyt\Learning\Learning_py\news_trends_analysis\src\scripts\line_messenger.py