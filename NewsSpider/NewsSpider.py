import requests
from bs4 import BeautifulSoup


def save_to_file(file_path, file_name, data):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    path = os.path.join(file_path, file_name + '.txt')
    with open(path, "w", encoding='utf-8') as file:
        for item in data:
            file.write(item + '\n')


def get_page_info(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    title = soup.find('h2', class_='titleBar').get_text(strip=True)
    more_link = soup.find('div', class_='more').find('a')['href']
    return title, more_link


def spider(url):
    response = requests.get(url)
    response.encoding = 'gbk'
    page_content = response.text
    title, more_link = get_page_info(page_content)
    print(f"Title: {title}")
    print(f"More Link: {more_link}")
    # Save the title and more link to a file
    save_to_file('news', 'news_info', [title, more_link])


if __name__ == '__main__':
    start_url = "http://example.com/start-page"
    print("Start")
    spider(start_url)
    print("End")
