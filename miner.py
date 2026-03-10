import hashlib
import requests
import time
import argparse

def mine(last_proof, difficulty):
    proof = 0
    while True:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:difficulty] == "0" * difficulty:
            return proof
        proof += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', required=True)
    parser.add_argument('--wallet', required=True)
    args = parser.parse_args()

    print(f"BDCoin Miner Started for {args.wallet}")
    
    while True:
        try:
            status = requests.get(f"{args.server}/chain").json()
            last_block = status['chain'][-1]
            diff = status['difficulty']
            
            print(f"Mining block {last_block['index']+1} at Difficulty {diff}...")
            new_proof = mine(last_block['proof'], diff)
            
            requests.post(f"{args.server}/mine", json={
                "proof": new_proof, 
                "wallet": args.wallet
            })
            print("Block Found! Sent to server.")
        except Exception as e:
            print(f"Waiting for node... {e}")
            time.sleep(10)
