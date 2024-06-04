import asyncio
import aiohttp
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

#Funkcja do pobierania danych z linka (asynchroniczna)
async def fetch(session, url):
    logging.debug(f"Fetching URL: {url}")
    async with session.get(url) as response:
        logging.debug(f"Status code: {response.status}")
        if response.status != 200:
            logging.error(f"Error fetching URL: {url}, status code: {response.status}")
            return ""
        return await response.text()

#Asynchroniczna funkcja do pobierania danych o produkcie
async def fetch_product_data(product_name):
    urls = [f'https://www.olx.pl/oferty/q-{product_name}/',
            f'https://www.ceneo.pl/szukaj-{product_name}'
    ]  # Lista URL-ów do przeszukania
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        products = []
        for response, url in zip(responses, urls):
            if response:
                logging.debug(f"Response length: {len(response)}")
                soup = BeautifulSoup(response, 'html.parser')
                # Parsowanie HTML do uzyskania danych o produkcie
                if "www.olx.pl" in url:
                    try:
                        div = soup.find('div', {'class': 'css-1sw7q4x'})
                        link = div.find('a', href=True)
                        cena = div.find('p', {'data-testid': 'ad-price'}).text
                        web_name = div.find('h6', {'class': 'css-16v5mdi er34gjf0'}).text
                        product_info = {
                            'name': product_name,
                            'price': cena.strip("qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMłŁąĄżŻźŹęĘóÓśŚ")+' zł',
                            'image': div.find('img')['src'],
                            'source': "OLX",  # Dodaj URL do informacji o produkcie
                            'link': 'https://www.olx.pl/'+link['href'],
                            'web_name': web_name
                        }
                        logging.debug(f"Parsed product info: {product_info}")
                        products.append(product_info)
                    except Exception as e:
                        logging.error(f"Error parsing HTML: {e}")
                        continue
                elif "www.ceneo.pl" in url:
                    try:
                        div_all = soup.find_all('div', {'class': 'cat-prod-row__body'})
                        div = div_all[1]
                        cena = div.find('span', {'class': 'price'}).text
                        link = div.find('a', href=True)
                        web_name = div.find('strong', {'class': 'cat-prod-row__name'}).text
                        product_info = {
                            'name': product_name,
                            'price': cena.strip("qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMłŁąĄżŻźŹęĘóÓśŚ")+' zł',
                            'image': div.find('img')['src'],
                            'source': "Ceneo",  # Dodaj URL do informacji o produkcie
                            'link': 'https://www.ceneo.pl/'+link['href'],
                            'web_name': web_name
                        }
                        logging.debug(f"Parsed product info: {product_info}")
                        products.append(product_info)
                    except Exception as e:
                        logging.error(f"Error parsing HTML: {e}")
                        continue
        return products

#Funkcja do zapisywania danych produktów do bazy danych
def save_to_db(products):
    db_url = 'http://db_service:5002/products'
    for product in products:
        logging.debug(f"Saving to DB: {product}")
        response = requests.post(db_url, json=product)
        logging.debug(f"DB response: {response.status_code}")

# Funkcja przetwarzająca produkty (pobieranie i zapisywanie)
def process_product(product_name):
    products = asyncio.run(fetch_product_data(product_name))
    save_to_db(products)

# Endpoint do wyszukiwania produktu
@app.route('/search', methods=['POST'])
def search_product():
    data = request.get_json()
    product_name = data['product_name']
    logging.debug(f"Starting search for product: {product_name}")
    
    with ThreadPoolExecutor() as executor:
        executor.submit(process_product, product_name)
        
    return jsonify({'status': 'Search started'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

