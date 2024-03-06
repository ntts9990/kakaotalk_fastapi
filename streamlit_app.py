# streamlit_app.py
import streamlit as st
import requests

# FastAPI 서버 URL
FASTAPI_SERVER_URL = "http://127.0.0.1:8000/news"


def get_news_from_server(keyword):
    response = requests.get(FASTAPI_SERVER_URL, params={"keyword": keyword})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("서버에서 뉴스를 가져오는 데 실패했습니다.")
        return []


def main():
    st.title("뉴스 검색 앱")

    keyword = st.text_input("검색할 키워드를 입력하세요:")

    if st.button("뉴스 가져오기"):
        news_data = get_news_from_server(keyword)
        if news_data:
            for news_item in news_data:
                with st.container():
                    st.write(f"제목: {news_item['title']}")
                    st.write(f"시간: {news_item['time']}")
                    st.write(f"내용: {news_item['contents']}")
                    st.markdown("---") # 뉴스 항목 간 구분선
        else:
            st.write("검색어와 일치하는 뉴스가 없습니다.")


if __name__ == "__main__":
    main()