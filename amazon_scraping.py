from bs4 import BeautifulSoup
import requests
import time
        
retries = 5
url = "https://www.amazon.com/s?k=mouse&crid=38UDRU7QNUXZ4&sprefix=mo%2Caps%2C430&ref=nb_sb_noss_2"
headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19042", "Accept-Language" : "en-US, en;q=0.5"}

for _ in range(retries):
    try: 
        webpage = requests.get(url, headers=headers)

        if webpage.status_code == 200:
            soup = BeautifulSoup(webpage.content, "html.parser")
            links = soup.find_all("span", attrs={"class": "a-size-medium a-color-base a-text-normal"})
            for link in links:  
                print(link.get_text())
            time.sleep(6)
            break
        else:   
            print(webpage)

    except requests.RequestException as e:
        print(f"An error occurred: {e}")

    print(f"Retrying... Attempt {retries - _} left.")

print("repository")