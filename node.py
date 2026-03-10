import hashlib
import json
import time
import os
import binascii
import ecdsa
from flask import Flask, jsonify, request, render_template_string

class BDCoin:
    def __init__(self):
        self.chain_file = 'blockchain.json'
        self.chain = []
        self.pending_txs = []
        self.difficulty = 4
        self.target_block_time = 600
        self.load_chain()

    def load_chain(self):
        if os.path.exists(self.chain_file):
            try:
                with open(self.chain_file, 'r') as f:
                    self.chain = json.load(f)
            except:
                self.create_genesis()
        else:
            self.create_genesis()

    def create_genesis(self):
        self.create_block(proof=100, previous_hash='0'*64)

    def save_chain(self):
        temp_file = self.chain_file + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(self.chain, f, indent=4)
        os.replace(temp_file, self.chain_file)

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_txs,
            'proof': proof,
            'previous_hash': previous_hash,
            'difficulty': self.difficulty
        }
        self.pending_txs = []
        self.chain.append(block)
        if len(self.chain) % 10 == 0:
            self.adjust_difficulty()
        self.save_chain()
        return block

    def adjust_difficulty(self):
        if len(self.chain) < 10: return
        last_10 = self.chain[-10:]
        actual_time = last_10[-1]['timestamp'] - last_10[0]['timestamp']
        expected_time = self.target_block_time * 10
        if actual_time < (expected_time / 2):
            self.difficulty += 1
        elif actual_time > (expected_time * 2):
            self.difficulty = max(1, self.difficulty - 1)

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == address: balance += float(tx['amount'])
                if tx['sender'] == address: balance -= float(tx['amount'])
        for tx in self.pending_txs:
            if tx['sender'] == address: balance -= float(tx['amount'])
        return balance

    def get_history(self, address):
        history = []
        for block in self.chain:
            for tx in block['transactions']:
                if tx['sender'] == address or tx['recipient'] == address:
                    t_type = "Reward" if tx['sender'] == "0" else ("Sent" if tx['sender'] == address else "Received")
                    history.append({
                        "type": t_type,
                        "amount": tx['amount'],
                        "address": tx['sender'] if t_type == "Received" else tx['recipient'],
                        "time": time.strftime('%d %b, %H:%M', time.localtime(block['timestamp'])),
                        "block": block['index']
                    })
        return history[::-1]

blockchain = BDCoin()
app = Flask(__name__)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bitcoin Node | BDCOIN Alpha</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root { --btc-orange: #F7931A; --bg-dark: #0A0A0B; --glass: rgba(255, 255, 255, 0.03); }
            body { background-color: var(--bg-dark); color: #FFFFFF; font-family: 'Inter', sans-serif; overflow-x: hidden; }
            
            /* Background Animation */
            .bg-pattern {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
                background-image: radial-gradient(circle at 2px 2px, rgba(247, 147, 26, 0.05) 1px, transparent 0);
                background-size: 40px 40px;
            }

            .glass-card {
                background: var(--glass);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
            }

            .btc-button {
                background: linear-gradient(135deg, #F7931A 0%, #FFAB40 100%);
                transition: all 0.3s ease;
            }
            .btc-button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(247, 147, 26, 0.3); }

            .node-status-pulse {
                width: 8px; height: 8px; background: #10B981; border-radius: 50%;
                display: inline-block; box-shadow: 0 0 10px #10B981;
                animation: pulse 2s infinite;
            }

            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

            input:focus { border-color: var(--btc-orange) !important; outline: none; }
        </style>
    </head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <div class="bg-pattern"></div>

        <div id="loginPage" class="max-w-md w-full animate-in fade-in duration-700">
            <div class="text-center mb-10">
                <svg class="w-16 h-16 mx-auto mb-4" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="32" fill="#F7931A"/>
                    <path d="M44.5 35.8c0.8-5.3-3.3-8.1-8.8-10l1.8-7.3-4.5-1.1-1.8 7.1c-1.2-0.3-2.4-0.6-3.6-0.8l1.8-7.2-4.5-1.1-1.8 7.3c-1 0-1.9 0-2.8 0l0.1-0.3-6.1-1.5-1.2 4.8s3.3 0.8 3.2 0.8c1.8 0.4 2.1 1.6 2.1 2.6l-2.1 8.3c0.1 0 0.3 0.1 0.5 0.1l-0.5-0.1-2.9 11.6c-0.2 0.5-0.8 1.4-2.1 1.1 0 0-3.2-0.8-3.2-0.8l-2.2 5.1 5.8 1.4c1.1 0.3 2.1 0.6 3.2 0.8l-1.8 7.4 4.5 1.1 1.8-7.3c1.2 0.3 2.4 0.6 3.6 0.8l-1.8 7.3 4.5 1.1 1.8-7.4c7.6 1.4 13.3 0.9 15.7-6 1.9-5.6-0.1-8.8-4.2-11 3-0.7 5.2-2.7 5.8-6.8zm-10.4 14.8c-1.4 5.5-10.8 2.5-13.8 1.8l2.5-9.8c3 0.7 12.7 2.2 11.3 8zm1.4-15c-1.3 5-9.1 2.5-11.6 1.8l2.2-9c2.5 0.6 10.7 1.8 9.4 7.2z" fill="white"/>
                </svg>
                <h1 class="text-2xl font-bold tracking-tight">Bitcoin Node Manager</h1>
                <p class="text-gray-400 text-sm">Sign in to your BDCOIN instance</p>
            </div>

            <div class="glass-card p-8 shadow-2xl">
                <div class="mb-6">
                    <label class="block text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Node Secret Key</label>
                    <div class="relative">
                        <input type="password" id="privKey" class="w-full bg-black/40 border border-white/10 p-4 rounded-xl text-white placeholder-gray-600 transition-all" placeholder="Enter Private Hex Key...">
                        <button onclick="toggleKey()" class="absolute right-4 top-4 text-gray-500 hover:text-white">👁</button>
                    </div>
                </div>

                <div class="flex items-center justify-between mb-8">
                    <label class="flex items-center text-xs text-gray-400 cursor-pointer">
                        <input type="checkbox" id="rememberMe" class="mr-2 rounded border-white/10 bg-black/40 text-[#F7931A]"> Remember this Node
                    </label>
                    <a href="#" class="text-xs text-[#F7931A] hover:underline">Lost Phrase?</a>
                </div>

                <button onclick="login()" id="loginBtn" class="w-full btc-button text-black font-bold py-4 rounded-xl mb-4 flex items-center justify-center">
                    <span id="btnText">Initialize Connection</span>
                </button>

                <div class="text-center">
                    <span class="text-xs text-gray-500">Don't have a node? <a href="#" class="text-white hover:underline">Generate Account</a></span>
                </div>
            </div>

            <div class="mt-8 flex justify-center space-x-6">
                <div class="text-center">
                    <p class="text-[10px] text-gray-500 uppercase">Status</p>
                    <p class="text-xs font-bold text-green-500"><span class="node-status-pulse mr-1"></span> Synchronized</p>
                </div>
                <div class="text-center">
                    <p class="text-[10px] text-gray-500 uppercase">Network</p>
                    <p class="text-xs font-bold">Mainnet (BDC)</p>
                </div>
                <div class="text-center">
                    <p class="text-[10px] text-gray-500 uppercase">Peers</p>
                    <p class="text-xs font-bold">12 Connected</p>
                </div>
            </div>
        </div>

        <div id="dashboard" class="hidden w-full max-w-5xl animate-in slide-in-from-bottom-10 duration-500">
            <nav class="flex justify-between items-center mb-8 bg-glass p-4 rounded-2xl border border-white/5">
                <div class="flex items-center space-x-4">
                    <div class="w-10 h-10 bg-[#F7931A] rounded-full flex items-center justify-center font-bold text-black">B</div>
                    <div>
                        <p class="text-sm font-bold">Node BD-01</p>
                        <p class="text-[10px] text-gray-400">Version 1.0.4-Beta</p>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="bg-white/5 hover:bg-white/10 p-2 px-4 rounded-lg text-xs font-semibold">Settings</button>
                    <button onclick="logout()" class="bg-red-500/10 hover:bg-red-500/20 text-red-500 p-2 px-4 rounded-lg text-xs font-semibold">Terminate Session</button>
                </div>
            </nav>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="glass-card p-8 md:col-span-2 relative overflow-hidden">
                    <div class="absolute top-0 right-0 p-8 opacity-10">
                        <svg class="w-32 h-32" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                    </div>
                    <p class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Available Balance</p>
                    <h2 id="balText" class="text-6xl font-black mb-6">0.00 <span class="text-2xl text-[#F7931A]">BDC</span></h2>
                    
                    <div class="flex flex-col sm:flex-row gap-6 mt-8 pt-8 border-t border-white/5">
                        <div id="qrcode" class="p-2 bg-white rounded-lg inline-block self-start"></div>
                        <div class="flex-1">
                            <p class="text-xs text-gray-400 mb-2 font-bold uppercase">Your Public Address</p>
                            <div class="bg-black/40 p-3 rounded-xl border border-white/5 flex justify-between items-center">
                                <code id="addrText" class="text-xs text-gray-300 break-all"></code>
                                <button onclick="copyAddr()" class="text-[#F7931A] text-xs ml-4">Copy</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="glass-card p-6 flex flex-col justify-between">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-4">Network Health</h3>
                    <div class="space-y-4">
                        <div class="flex justify-between border-b border-white/5 pb-2">
                            <span class="text-xs text-gray-500">Block Height</span>
                            <span id="blockHeight" class="text-xs font-bold text-[#F7931A]">0</span>
                        </div>
                        <div class="flex justify-between border-b border-white/5 pb-2">
                            <span class="text-xs text-gray-500">Mempool</span>
                            <span id="mempoolSize" class="text-xs font-bold">0 TXs</span>
                        </div>
                        <div class="flex justify-between border-b border-white/5 pb-2">
                            <span class="text-xs text-gray-500">Difficulty</span>
                            <span id="diffText" class="text-xs font-bold">4.0</span>
                        </div>
                    </div>
                    <div class="mt-6">
                        <div class="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                            <div class="bg-[#F7931A] h-full w-2/3 shadow-[0_0_15px_#F7931A]"></div>
                        </div>
                        <p class="text-[9px] text-gray-500 mt-2 text-center uppercase">Sync Progress: 100%</p>
                    </div>
                </div>

                <div class="glass-card p-6">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-6">Create Outbound Transaction</h3>
                    <input type="text" id="toAddr" class="w-full bg-black/40 border border-white/10 p-3 rounded-xl text-sm mb-4" placeholder="Recipient Public Address">
                    <div class="relative mb-6">
                        <input type="number" id="toAmt" class="w-full bg-black/40 border border-white/10 p-3 rounded-xl text-sm" placeholder="Amount to send">
                        <span class="absolute right-4 top-3 text-[#F7931A] font-bold text-xs">BDC</span>
                    </div>
                    <button onclick="send()" class="w-full btc-button text-black font-bold py-3 rounded-xl text-sm">Broadcast Transaction</button>
                </div>

                <div class="glass-card p-6 md:col-span-2">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-6">Transaction Ledger</h3>
                    <div id="historyList" class="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                        </div>
                </div>
            </div>
        </div>

        <script>
            let walletKey = ""; let walletAddr = ""; let lastBalance = 0; let qr = null;

            window.onload = function() {
                const saved = localStorage.getItem('bd_node_session');
                if(saved) {
                    document.getElementById('privKey').value = saved;
                    login();
                }
            };

            async function login() {
                const key = document.getElementById('privKey').value;
                if(!key) return;
                
                const btn = document.getElementById('loginBtn');
                btn.innerHTML = '<span class="animate-spin mr-2">◌</span> Connecting...';
                
                try {
                    const r = await fetch('/auth', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({priv: key})});
                    const d = await r.json();
                    
                    if(d.error) {
                        alert("Cryptographic Verification Failed");
                        btn.innerHTML = "Initialize Connection";
                        return;
                    }

                    walletKey = key; walletAddr = d.address;
                    if(document.getElementById('rememberMe').checked) localStorage.setItem('bd_node_session', key);

                    document.getElementById('loginPage').classList.add('hidden');
                    document.getElementById('dashboard').classList.remove('hidden');
                    document.getElementById('addrText').innerText = walletAddr;
                    if(!qr) qr = new QRCode(document.getElementById("qrcode"), { text: walletAddr, width: 100, height: 100 });
                    
                    updateUI(true);
                    setInterval(updateUI, 5000);
                } catch(e) { 
                    alert("Node Offline"); 
                    btn.innerHTML = "Initialize Connection";
                }
            }

            function toggleKey() {
                const x = document.getElementById("privKey");
                x.type = x.type === "password" ? "text" : "password";
            }

            function logout() { localStorage.removeItem('bd_node_session'); location.reload(); }

            async function updateUI(silent = false) {
                const r = await fetch('/balance/' + walletAddr);
                const d = await r.json();
                lastBalance = d.balance;
                document.getElementById('balText').innerHTML = d.balance.toFixed(2) + ' <span class="text-2xl text-[#F7931A]">BDC</span>';

                const hR = await fetch('/chain');
                const chainData = await hR.json();
                document.getElementById('blockHeight').innerText = chainData.chain.length;
                document.getElementById('diffText').innerText = chainData.difficulty;

                const historyR = await fetch('/history/' + walletAddr);
                const historyD = await historyR.json();
                document.getElementById('historyList').innerHTML = historyD.map(tx => `
                    <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
                        <div class="flex items-center space-x-4">
                            <div class="w-8 h-8 rounded-full flex items-center justify-center ${tx.type === 'Sent' ? 'bg-red-500/20 text-red-500' : 'bg-green-500/20 text-green-500'}">
                                ${tx.type === 'Sent' ? '↑' : '↓'}
                            </div>
                            <div>
                                <p class="text-xs font-bold">${tx.type}</p>
                                <p class="text-[9px] text-gray-500">${tx.time} • Block #${tx.block}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-sm font-black ${tx.type === 'Sent' ? 'text-red-400' : 'text-green-400'}">${tx.type === 'Sent' ? '-' : '+'}${tx.amount} BDC</p>
                            <p class="text-[8px] text-gray-600 truncate w-24">${tx.address}</p>
                        </div>
                    </div>
                `).join('') || '<p class="text-center text-gray-600 text-xs py-8">No transaction data found in ledger.</p>';
            }

            async function send() {
                const to = document.getElementById('toAddr').value;
                const amt = document.getElementById('toAmt').value;
                const r = await fetch('/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({priv:walletKey, to:to, amt:amt})});
                const d = await r.json();
                alert(d.message || d.error);
                updateUI(true);
            }

            function copyAddr() {
                navigator.clipboard.writeText(walletAddr);
                alert("Address copied to clipboard");
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/auth', methods=['POST'])
def auth():
    try:
        data = request.get_json()
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(data['priv']), curve=ecdsa.SECP256k1)
        return jsonify({"address": binascii.hexlify(sk.get_verifying_key().to_string()).decode()})
    except: return jsonify({"error": "Fail"}), 400

@app.route('/balance/<address>')
def bal(address):
    return jsonify({"balance": blockchain.get_balance(address)})

@app.route('/history/<address>')
def hist(address):
    return jsonify(blockchain.get_history(address))

@app.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    try:
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(data['priv']), curve=ecdsa.SECP256k1)
        sender = binascii.hexlify(sk.get_verifying_key().to_string()).decode()
        if blockchain.get_balance(sender) < float(data['amt']): return jsonify({"error":"Insufficient funds for transaction"}), 400
        blockchain.pending_txs.append({"sender":sender, "recipient":data['to'], "amount":float(data['amt'])})
        return jsonify({"message":"Transaction broadcasted to mempool"})
    except: return jsonify({"error":"Cryptographic signature error"}), 400

@app.route('/chain')
def chain():
    return jsonify({"chain": blockchain.chain, "difficulty": blockchain.difficulty})

@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    last = blockchain.chain[-1]
    blockchain.pending_txs.append({"sender":"0", "recipient":data['wallet'], "amount":50})
    p_hash = hashlib.sha256(json.dumps(last, sort_keys=True).encode()).hexdigest()
    return jsonify(blockchain.create_block(data['proof'], p_hash)), 200

if __name__ == '__main__':
    # Standard Flask port, change to 8080 or 10000 for cloud hosting if needed
    app.run(host='0.0.0.0', port=5000)
