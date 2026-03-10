import hashlib
import json
import time
from flask import Flask, jsonify, request, render_template_string

class BDCoin:
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.difficulty = 4  # Number of leading zeros
        self.nodes = set()
        self.create_block(proof=100, previous_hash='0', data="Genesis Block")

    def create_block(self, proof, previous_hash, data=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.mempool if data is None else data,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.mempool = []
        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_last_block(self):
        return self.chain[-1]

# --- Flask Server ---
app = Flask(__name__)
blockchain = BDCoin()

@app.route('/')
def explorer():
    # Simple HTML Template for Block Explorer
    template = """
    <html>
        <head><title>BDCoin Explorer</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>BDCoin Block Explorer</h1>
            <hr>
            <h3>Blockchain Info</h3>
            <p>Difficulty: {{ diff }} | Total Blocks: {{ chain|length }}</p>
            <table border="1" cellpadding="10">
                <tr><th>Index</th><th>Timestamp</th><th>Proof</th><th>Prev Hash</th></tr>
                {% for block in chain[::-1] %}
                <tr>
                    <td>{{ block.index }}</td>
                    <td>{{ block.timestamp }}</td>
                    <td>{{ block.proof }}</td>
                    <td style="font-size: 0.8em;">{{ block.previous_hash }}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
    </html>
    """
    return render_template_string(template, chain=blockchain.chain, diff=blockchain.difficulty)

@app.route('/mine', methods=['POST'])
def mine():
    values = request.get_json()
    proof = values.get('proof')
    wallet = values.get('wallet')
    
    # Simple Reward Transaction
    blockchain.mempool.append({"sender": "network", "recipient": wallet, "amount": 50})
    
    last_block = blockchain.get_last_block()
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)
    
    return jsonify({"message": "Block Mined!", "index": block['index']}), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({"chain": blockchain.chain, "length": len(blockchain.chain)}), 200

if __name__ == '__main__':
    # Use 0.0.0.0 to allow remote connections
    app.run(host='0.0.0.0', port=5000)
