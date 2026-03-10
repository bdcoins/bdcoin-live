import hashlib
import json
import time
from flask import Flask, jsonify, request, render_template_string
from ecdsa import SigningKey, SECP256k1

class BDCoin:
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.difficulty = 4 
        # Genesis Block
        self.create_block(proof=100, previous_hash='1', miner="Satoshi")

    def create_block(self, proof, previous_hash, miner):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.mempool,
            'proof': proof,
            'previous_hash': previous_hash,
            'miner': miner, # Track who found the block
        }
        self.mempool = [] # Clear mempool after mining
        self.chain.append(block)
        
        # Simple Difficulty Adjustment (Every 10 blocks)
        if len(self.chain) % 10 == 0:
            self.difficulty += 1
            
        return block

    def hash(self, block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

# --- Server Logic ---
app = Flask(__name__)
bdc = BDCoin()

@app.route('/')
def home():
    # Home Page: Wallet Generator & Transfer
    return render_template_string("""
    <html>
        <head><title>BDCoin Core</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px;">
            <h1>BDCoin Network</h1>
            <div style="background: #f4f4f4; padding: 15px; border-radius: 10px;">
                <h3>Step 1: Generate Wallet</h3>
                <button onclick="genWallet()">Create New Wallet</button>
                <p id="walletInfo"></p>
            </div>
            <br>
            <div style="background: #e8f4fd; padding: 15px; border-radius: 10px;">
                <h3>Step 2: P2P Transfer</h3>
                <input id="sender" placeholder="Your Address"><br>
                <input id="receiver" placeholder="Recipient Address"><br>
                <input id="amount" type="number" placeholder="Amount"><br><br>
                <button onclick="sendCoins()">Send BDCoin</button>
            </div>
            <p><a href="/explorer">View Block Explorer & Leaderboard →</a></p>
            
            <script>
                function genWallet() {
                    const id = Math.random().toString(36).substring(2, 15);
                    document.getElementById('walletInfo').innerHTML = "<b>Address:</b> BDC_" + id + "<br><small>Save this address to mine!</small>";
                }
                function sendCoins() {
                    alert("Transaction added to mempool! It will be confirmed in the next block.");
                }
            </script>
        </body>
    </html>
    """)

@app.route('/explorer')
def explorer():
    # 2nd Page: Stats and Block Finders
    miner_stats = {}
    for block in bdc.chain:
        miner = block['miner']
        miner_stats[miner] = miner_stats.get(miner, 0) + 1

    return render_template_string("""
    <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>Block Explorer</h1>
            <h3>Network Difficulty: {{ diff }}</h3>
            <hr>
            <h3>Top Miners (Blocks Found)</h3>
            <ul>
                {% for miner, count in stats.items() %}
                    <li><b>{{ miner }}</b>: {{ count }} Blocks</li>
                {% endfor %}
            </ul>
            <hr>
            <h3>Recent Blocks</h3>
            <table border="1" width="100%">
                <tr><th>Index</th><th>Miner</th><th>Transactions</th><th>Hash</th></tr>
                {% for b in chain[::-1] %}
                <tr>
                    <td>{{ b.index }}</td>
                    <td>{{ b.miner }}</td>
                    <td>{{ b.transactions|length }}</td>
                    <td><small>{{ b.previous_hash[:20] }}...</small></td>
                </tr>
                {% endfor %}
            </table>
            <br><a href="/">Back Home</a>
        </body>
    </html>
    """, diff=bdc.difficulty, chain=bdc.chain, stats=miner_stats)

@app.route('/mine', methods=['POST'])
def mine_block():
    data = request.get_json()
    last_block = bdc.chain[-1]
    # Proof validation would go here in a production app
    new_block = bdc.create_block(data['proof'], bdc.hash(last_block), data['wallet'])
    return jsonify(new_block), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({"chain": bdc.chain, "difficulty": bdc.difficulty})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
