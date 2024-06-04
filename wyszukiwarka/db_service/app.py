from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Łączenie się z bazą danych
client = MongoClient('mongodb://db:27017/')
db = client.product_db
collection = db.products

#Funkcja do serializacji produktów
def serialize_product(product):
    if isinstance(product, dict):
        for key, value in product.items():
            if isinstance(value, ObjectId):
                product[key] = str(value)
    return product

@app.route('/products', methods=['POST'])

#Dodawanie nowych produktów do bazy danych
def add_product():
    product_data = request.get_json()
    logging.debug(f"Adding product to DB: {product_data}")
    collection.insert_one(product_data)
    return jsonify({'status': 'Product added'}), 201

#Pobieranie produktów z bazy danych
@app.route('/products', methods=['GET'])
def get_products():
    product_name = request.args.get('name')
    logging.debug(f"Fetching products from DB for name: {product_name}")
    products = collection.find({'name': {'$regex': product_name, '$options': 'i'}})
    serialized_products = [serialize_product(product) for product in products]
    return jsonify(serialized_products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

