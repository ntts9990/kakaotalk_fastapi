from fastapi import FastAPI, HTTPException
from typing import List
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

class NewsData(BaseModel):
    ranking: str
    title: str
    link: str
    img: str = None
    time: str = None
    contents: str = None

class KeywordModel(BaseModel):
    keyword: str = ""

app = FastAPI()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
}

async def fetch_detailed_news_data(link: str) -> (str, str):
    async with httpx.AsyncClient() as client:
        res = await client.get(link, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        news_time = soup.select_one(".media_end_head_info_datestamp_time").get("data-date-time")
        news_content = soup.select_one("#newsct_article").text.strip().replace("\n", "").replace("\t", "")
        return news_time, news_content

async def fetch_news_data(url: str, keyword: str) -> List[NewsData]:
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to fetch news")
    soup = BeautifulSoup(res.text, "lxml")
    news_data = []
    newslist = soup.select(".rankingnews_list")[:12]

    for news in newslist:
        for li in news.findAll("li"):
            list_title = li.select_one(".list_title")
            if list_title and keyword in list_title.text.lower():
                time, contents = await fetch_detailed_news_data(list_title.get("href"))
                news_data.append(
                    NewsData(
                        ranking=li.select_one(".list_ranking_num").text if li.select_one(".list_ranking_num") else "랭킹 정보 없음",
                        title=list_title.text,
                        link=list_title.get("href"),
                        img=li.select_one("img").get("src") if li.select_one("img") else None,
                        time=time,
                        contents=contents
                    )
                )
    return news_data

@app.post("/news", response_model=List[NewsData])
async def read_news(request_body: KeywordModel):
    keyword = request_body.keyword.lower()
    try:
        news_data = await fetch_news_data("https://news.naver.com/main/ranking/popularMemo.naver", keyword)
        return news_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the news.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
