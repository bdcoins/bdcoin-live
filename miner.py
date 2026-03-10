import hashlib
import requests
import time
import argparse

def proof_of_work(last_proof, difficulty):
    proof = 0
    while True:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:difficulty] == "0" * difficulty:
            return proof
        proof += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', help='Server IP/URL', required=True)
    parser.add_argument('--wallet', help='BDCoin Wallet Address', required=True)
    args = parser.parse_args()

    print(f"Mining BDCoin... Target Server: {args.server}")
    
    while True:
        try:
            # 1. Get last block to find current proof
            response = requests.get(f"{args.server}/chain").json()
            last_block = response['chain'][-1]
            last_proof = last_block['proof']
            
            # 2. Start Hashing
            start_time = time.time()
            new_proof = proof_of_work(last_proof, 4)
            duration = time.time() - start_time
            
            # 3. Submit Proof
            submit = requests.post(f"{args.server}/mine", 
                                   json={"proof": new_proof, "wallet": args.wallet})
            
            if submit.status_code == 200:
                print(f"Block Mined! Proof: {new_proof} | Time: {duration:.2f}s")
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)
