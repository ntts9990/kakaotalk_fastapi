from fastapi import FastAPI
from typing import List
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

app = FastAPI()


async def get_news(keyword: str = ""):
    # 뉴스 크롤링 로직 구현
    url = "https://news.naver.com/main/ranking/popularMemo.naver"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"}

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")

    newslist = soup.select(".rankingnews_list")

    # 뉴스 데이터를 저장할 리스트
    newsData = []

    # 언론사마다
    for news in newslist[:12]:
        # 5개의 상위랭킹 뉴스를 가져옴
        lis = news.findAll("li")
        for li in lis:
            # 뉴스랭킹
            news_ranking_element = li.select_one(".list_ranking_num")
            if news_ranking_element is not None:
                news_ranking = news_ranking_element.text
            else:
                news_ranking = "랭킹 정보 없음"

            # 뉴스링크와 제목
            list_title = li.select_one(".list_title")
            if list_title is not None:
                news_title = list_title.text
                news_link = list_title.get("href")
            else:
                continue

            # 뉴스 썸네일
            try:
                news_img = li.select_one("img").get("src")
            except:
                news_img = None

            # 저장
            newsData.append({
                "ranking": news_ranking,
                "title": news_title,
                "link": news_link,
                "img": news_img
            })

    for news in newsData:
        news_url = news['link']
        res = requests.get(news_url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        news_time = soup.select_one(".media_end_head_info_datestamp").select_one(
            ".media_end_head_info_datestamp_time").get("data-date-time")
        news_content = soup.select_one("#newsct_article").text.replace("\n", "").replace("\t", "")
        news['time'] = news_time
        news['contents'] = news_content

    if keyword:
        filtered_newsData = [news for news in newsData if keyword.lower() in news['title'].lower()]
    else:
        filtered_newsData = newsData


    file = pd.DataFrame(filtered_newsData)
    # return file
    return file


@app.get("/news", response_model=List[dict])
async def read_news(keyword: str = ""):
    news_df = await get_news(keyword)
    return news_df.to_dict('records')


# Streamlit 애플리케이션 예제
def streamlit_app():
    st.title("뉴스 검색")
    # 사용자로부터 키워드 입력 받기
    keyword = st.text_input("검색할 키워드를 입력하세요:", "")

    # 검색 버튼 추가
    if st.button("검색"):
        # FastAPI 서버에서 뉴스 데이터 가져오기
        # 예제에서는 직접 FastAPI를 호출하는 코드는 제외하고, 함수 호출로 대체합니다.
        # 실제 구현에서는 FastAPI 엔드포인트에 요청을 보내는 코드가 필요합니다.
        news_df = get_news(keyword)  # 비동기 호출 방식 고려
        st.write(news_df)

# Streamlit 앱 실행
if __name__ == "__main__":
    streamlit_app()