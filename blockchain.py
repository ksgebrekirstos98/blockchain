from blockchain_util import hash_block
import json
from block import Block
from transaction import Transaction
from verification import Verification

MINING_REWARD = 10

class Blockchain:
    def __init__(self, hosting_node_id):
        gen_block = Block("", 0, [], 0, 0)
        self.node = hosting_node_id
        self.chain = [gen_block]
        self.outstanding_transactions = []
        self.participants = dict()
        self.load_data()


    def get_last_block(self):
        if len(self.chain) < 1:
            return None
        return self.chain[-1]


    def add_transaction(self, sender, recepient, amount):
        transaction = Transaction(sender, recepient, amount)

        if Verification().verify_transaction(transaction, self.get_balance):
            self.outstanding_transactions.append(transaction)
            self.participants[sender] = True
            self.participants[recepient] = True
            self.save_data()
            return True
        return False


    def get_proof_of_work(self):
        proof_of_work = 0

        while not Verification().valid_proof_of_work(
            hash_block(self.get_last_block()), self.outstanding_transactions, proof_of_work
        ):
            proof_of_work += 1
        return proof_of_work


    def mine_block(self):
        proof_of_work = self.get_proof_of_work()

        mining_reward_transaction = Transaction(None, self.node, MINING_REWARD)
        self.outstanding_transactions.append(mining_reward_transaction)

        new_block = Block(
            hash_block(self.get_last_block()),
            int(self.get_last_block().index) + 1,
            self.outstanding_transactions,
            proof_of_work,
        )
        self.chain.append(new_block)
        
        if Verification().verify_blockchain(self.chain):
            self.outstanding_transactions = []
            self.participants[self.node] = True
            self.save_data()
            return True

        self.chain.pop()
        self.outstanding_transactions.pop()
        return False


    def get_balance(self, participant):
        amount_sent = 0.0
        amount_received = 0.0

        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == participant:
                    amount_sent += transaction.amount
                elif transaction.recepient == participant:
                    amount_received += transaction.amount

        for transaction in self.outstanding_transactions:
            if transaction.sender == participant:
                amount_sent += transaction.amount
        return float(amount_received - amount_sent)


    def save_data(self):
        try:
            with open("blockchain.txt", mode="w") as file:
                reconstructed_blockchain = [
                    block.__dict__
                    for block in [
                        Block(
                            block_el.prev_hash,
                            block_el.index,
                            [tx.__dict__ for tx in block_el.transactions],
                            block_el.proof_of_work,
                            block_el.timestamp,
                        )
                        for block_el in self.chain
                    ]
                ]
                file.write(json.dumps(reconstructed_blockchain))
                file.write("\n")
                reconstructed_outstanding_transactions = [
                    txn.__dict__ for txn in self.outstanding_transactions
                ]
                file.write(json.dumps(reconstructed_outstanding_transactions))
                file.write("\n")
                file.write(json.dumps(self.participants))
        except IOError:
            ("Saving failed!")


    def load_data(self):
        try:
            with open("blockchain.txt", mode="r") as file:
                file_content = file.readlines()
                blockchain = json.loads(file_content[0][:-1])
                outstanding_transactions = json.loads(file_content[1][:-1])
                updated_blockchain = []
                updated_outstanding_transactions = []

                for block in blockchain:
                    updated_block = Block(
                        block["prev_hash"],
                        block["index"],
                        [
                            Transaction(
                                tx["sender"], tx["recepient"], tx["amount"], tx["timestamp"]
                            )
                            for tx in block["transactions"]
                        ],
                        block["proof_of_work"],
                        block["timestamp"],
                    )
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain

                for txn in outstanding_transactions:
                    updated_txn = Transaction(
                        txn["sender"], txn["recepient"], txn["amount"], txn["timestamp"]
                    )
                    updated_outstanding_transactions.append(updated_txn)
                self.outstanding_transactions = updated_outstanding_transactions
                self.participants = json.loads(file_content[2])
        except (IOError, IndexError):
            print("Initializing new blockchain with genesis block.")