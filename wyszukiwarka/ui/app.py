from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint do wyszukiwania produktu
@app.route('/search', methods=['POST'])
def search():
    product_name = request.form['product_name']
    response = requests.post('http://engine:5001/search', json={'product_name': product_name})
    return response.json()

# Endpoint do wyświetlania wyników wyszukiwania
@app.route('/results')
def results():
    product_name = request.args.get('product_name')
    response = requests.get(f'http://db_service:5002/products?name={product_name}')
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

