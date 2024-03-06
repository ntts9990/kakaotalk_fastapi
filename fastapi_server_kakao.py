from fastapi import FastAPI, HTTPException
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

app = FastAPI()

class NewsData(BaseModel):
    ranking: str
    title: str
    link: str
    img: Optional[str] = None
    time: Optional[str] = None
    contents: Optional[str] = None

class ComplexRequestModel(BaseModel):
    action: dict = Field(..., example={"userRequest": {"utterance": "sample"}})

    def get_keyword(self) -> str:
        return self.action.get("userRequest", {}).get("utterance", "의사")

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

@app.post("/filtered-news")
async def read_filtered_news(request_body: ComplexRequestModel):
    keyword = request_body.get_keyword().lower()
    try:
        news_data = await fetch_news_data("https://news.naver.com/main/ranking/popularMemo.naver", keyword)
        response_body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": str(news_data) # This is a simplification, consider formatting this properly
                        }
                    }
                ]
            }
        }
        return response_body
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the news.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
