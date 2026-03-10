import hashlib
import json
import time
import os
import binascii
import ecdsa
from flask import Flask, jsonify, request

app = Flask(__name__)

class BDCoin:
    def __init__(self):
        self.chain = []
        self.pending_txs = []
        self.difficulty = 4
        self.create_genesis()

    def create_genesis(self):
        self.create_block(proof=100, previous_hash='0'*64)

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_txs,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        self.pending_txs = []
        self.chain.append(block)
        return block

blockchain = BDCoin()

@app.route('/')
def home():
    return "<h1>BDcoin Node is Live on Render!</h1><p>Use /chain to see the blocks.</p>"

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({"chain": blockchain.chain, "difficulty": blockchain.difficulty})

@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    if not data or 'wallet' not in data or 'proof' not in data:
        return jsonify({"error": "Missing data"}), 400
    
    # Reward the miner
    blockchain.pending_txs.append({"sender": "0", "recipient": data['wallet'], "amount": 50})
    new_block = blockchain.create_block(data['proof'], blockchain.chain[-1]['previous_hash'])
    return jsonify(new_block), 200

if __name__ == '__main__':
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
