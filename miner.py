import hashlib
import requests
import time
import os
import threading
from flask import Flask

# --- CONFIGURATION ---
# These will be set in the Render Dashboard Environment Variables
NODE_URL = os.environ.get("NODE_URL", "https://your-node-name.onrender.com")
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS", "your_public_address_here")

app = Flask(__name__)
stats = {"blocks_mined": 0, "status": "Initializing..."}

def solve_pow(last_proof, difficulty):
    proof = 0
    prefix = "0" * difficulty
    while True:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:difficulty] == prefix:
            return proof
        proof += 1

def start_mining():
    global stats
    print(f"Mining started for: {WALLET_ADDRESS}")
    stats["status"] = "Mining"
    
    while True:
        try:
            # 1. Fetch latest block and difficulty
            response = requests.get(f"{NODE_URL}/chain", timeout=10)
            data = response.json()
            last_block = data['chain'][-1]
            difficulty = data['difficulty']
            
            # 2. Solve Proof of Work
            new_proof = solve_pow(last_block['proof'], difficulty)
            
            # 3. Submit result
            submit = requests.post(f"{NODE_URL}/mine", json={
                "proof": new_proof,
                "wallet": WALLET_ADDRESS
            }, timeout=10)
            
            if submit.status_code == 200:
                stats["blocks_mined"] += 1
                print(f"✅ Success! Total blocks mined: {stats['blocks_mined']}")
            
        except Exception as e:
            stats["status"] = f"Error: {str(e)}"
            print(f"⚠️ Connection error: {e}. Retrying in 10s...")
            time.sleep(10)

@app.route('/')
def status():
    return f"""
    <h1>BDcoin Miner Status</h1>
    <p><b>Target Node:</b> {NODE_URL}</p>
    <p><b>Mining Wallet:</b> {WALLET_ADDRESS}</p>
    <p><b>Status:</b> {stats['status']}</p>
    <p><b>Blocks Mined in this session:</b> {stats['blocks_mined']}</p>
    """

if __name__ == "__main__":
    # Start mining in a background thread so the web server can stay alive
    miner_thread = threading.Thread(target=start_mining, daemon=True)
    miner_thread.start()
    
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
