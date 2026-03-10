import hashlib
import json
import time
import os
import binascii
import ecdsa
import requests
from flask import Flask, jsonify, request, render_template_string

class BDCoin:
    def __init__(self):
        self.chain = []
        self.pending_txs = []
        self.nodes = set() # P2P Node Registry
        self.difficulty = 4
        self.create_genesis()

    def create_genesis(self):
        if not self.chain:
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

    def register_node(self, address):
        self.nodes.add(address)

    def resolve_conflicts(self):
        """Bitcoin's Longest Chain Rule"""
        new_chain = None
        max_length = len(self.chain)
        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    if length > max_length: # longest chain wins
                        max_length = length
                        new_chain = chain
            except: continue
        if new_chain:
            self.chain = new_chain
            return True
        return False

blockchain = BDCoin()
app = Flask(__name__)

# --- HTML FRONTEND WITH GENERATE BUTTON ---
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BDcoin Node</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body { background: #0f172a; color: white; font-family: sans-serif; }</style>
    </head>
    <body class="p-10 flex flex-col items-center">
        <div class="max-w-xl w-full bg-slate-800 p-8 rounded-3xl shadow-2xl border border-slate-700">
            <h1 class="text-3xl font-bold text-orange-500 mb-6">BDcoin Ecosystem</h1>
            
            <div class="mb-8 p-4 bg-slate-900 rounded-xl border border-orange-500/30">
                <h2 class="text-sm uppercase tracking-widest text-gray-400 mb-4">Account Management</h2>
                <button onclick="generateWallet()" class="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 rounded-lg transition">Generate New Node Account</button>
                <div id="walletResult" class="mt-4 hidden space-y-2">
                    <p class="text-xs text-red-400">Save your Private Key! You cannot recover it.</p>
                    <div class="bg-black p-3 rounded border border-white/10 overflow-hidden">
                        <p class="text-[10px] text-gray-500">PRIVATE KEY (HEX)</p>
                        <code id="privDisplay" class="text-[10px] text-orange-300 break-all"></code>
                    </div>
                    <div class="bg-black p-3 rounded border border-white/10">
                        <p class="text-[10px] text-gray-500">PUBLIC ADDRESS</p>
                        <code id="pubDisplay" class="text-[10px] text-green-400 break-all"></code>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 text-center">
                <div class="p-4 bg-slate-900 rounded-xl">
                    <p class="text-xs text-gray-500 uppercase">Blocks</p>
                    <p id="height" class="text-2xl font-bold">0</p>
                </div>
                <div class="p-4 bg-slate-900 rounded-xl">
                    <p class="text-xs text-gray-500 uppercase">Difficulty</p>
                    <p id="diff" class="text-2xl font-bold">4</p>
                </div>
            </div>
        </div>

        <script>
            async function generateWallet() {
                const r = await fetch('/generate_wallet');
                const d = await r.json();
                document.getElementById('walletResult').classList.remove('hidden');
                document.getElementById('privDisplay').innerText = d.private_key;
                document.getElementById('pubDisplay').innerText = d.public_key;
            }
            setInterval(async () => {
                const r = await fetch('/chain');
                const d = await r.json();
                document.getElementById('height').innerText = d.length;
                document.getElementById('diff').innerText = d.difficulty;
            }, 3000);
        </script>
    </body>
    </html>
    """)

# --- API ENDPOINTS ---

@app.route('/generate_wallet')
def gen():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    priv = binascii.hexlify(sk.to_string()).decode()
    pub = binascii.hexlify(sk.get_verifying_key().to_string()).decode()
    return jsonify({"private_key": priv, "public_key": pub})

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain), 'difficulty': blockchain.difficulty})

@app.route('/mine', methods=['POST'])
def mine():
    values = request.get_json()
    last_block = blockchain.chain[-1]
    # Reward for miner
    blockchain.pending_txs.append({"sender": "0", "recipient": values['wallet'], "amount": 50})
    block = blockchain.create_block(values['proof'], hashlib.sha256(json.dumps(last_block, sort_keys=True).encode()).hexdigest())
    return jsonify(block), 200

# P2P Registration
@app.route('/nodes/register', methods=['POST'])
def register():
    nodes = request.get_json().get('nodes')
    for node in nodes: blockchain.register_node(node)
    return "Nodes added", 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
