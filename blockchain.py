from crypt import methods
import hashlib
from itertools import chain
import json
from textwrap import dedent
from time import time
from uuid import uuid4
import requests
from urllib.parse import urlparse
from flask import Flask, jsonify, request
# Creating a Blockchain class whose constructor creates an initial empty list and another to store transactions

class Blockchain(object):
    def __init__(self):
        self.chain = [] # list to store blockchain
        self.current_transactions = [] # list to store transactions
        self.newBlock(previous_hash=1, proof=100) # create the genesis block
        self.nodes = set()


    # function to create new block and add it to chain
    def newBlock(self, proof, previous_hash=None):
        block = {
            'index':len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = [] # resets the current list of transactions
        self.chain.append(block)
        return block

    # function to add a new transaction to the list of transcations
    def newTransaction(self, sender, recipent, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipent,
            'amount': amount,
        })

        return self.lastBlock['index'] + 1 # returns the index of the block that is next to be mined

    # function to register nodes
    def register_node(self, address):
        """"
        Add a new node to the list of nodes
        :param address: <str> Address of node
        :return: Node
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    @staticmethod
    # function to hash a block
    def hash(block):
        """Creates a SHA-256 of a block
            :param block: <dict> Block
            :return: <str>
        """
        blockString = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(blockString).hexdigest()

    @property
    # function to return the last block in the chain
    def lastBlock(self):
        return self.chain[-1]

    # function to implement our PoW algorithm
    def proofOfWork(self, last_proof):
        """
        Simple PoW Algorithm:
         -  Find a number p' such that hash(pp') contains leading 4 zeroes, 
            where p is the previous p'
            p is thre previous proof, and p' is the new proof
            :param last_proof: <int>
            :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof
    
    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: Does hash(pp') contain 4
        leading zeroes
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        
        return guess_hash[:4] == "0000"
    
    # function to determine if a blockchain is valid
    def valid_chain(self, chain):
        """
        :param chain: <list> A blockchain
        :return: <bool> True if valid, Flase if not
        """

        last_block = chain[0]
        curr_index = 1
        while curr_index < len(chain):
            block = chain[curr_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # check if the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # check if the Pow is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            
            last_block = block
            curr_index += 1
        
        return True

    # function to resolve conflict by replacing our chain with the longest one in the network
    def resolve_conflicts(self):
        """
        Consensus Algorithm, resolves conflicts 
        :return: <bool> True if the chain is replaced, 
        False if not
        """
        neighbours = self.nodes
        new_chain = None

        # only looking for chains longer than the current one
        max_length = len(self.chain)
        # grab and verify the chains from all the nodes in our network

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
            
            # check if the length is longer and the chain is valid

            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False


app = Flask(__name__) # Instantiate our Node

node_identifier = str(uuid4()).replace('-','') # generate a globally unique address for this node

blockchain = Blockchain() # instantiate the Blockchain

@app.route('/mine', methods=['GET'])
def mine():
    """The Mining Endpoint is where the 
    magic happens and there are things to do here
        1. Calculate PoW
        2. Reward the miner with 1 coin 
        3. Forge the new Block adding it to the
           chain
    """
    last_block = blockchain.lastBlock
    last_proof = last_block['proof']
    proof = blockchain.proofOfWork(last_proof)

    # reward for finding this proof

    blockchain.newTransaction(
            sender="0",
            recipent=node_identifier,
            amount=1,
    )

    # forge the new block by adding it to the chain
    previousHash = blockchain.hash(last_block)
    block = blockchain.newBlock(proof, previousHash)
    
    response = {
        'message' : "New Block Forged",
        'index' : block['index'],
        'transactions' : block['transactions'],
        'proof' : block['proof'],
        'previous_hash' : block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def newTransaction():
    values = request.get_json()
    required = ['sender', 'recipent', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.newTransaction(values['sender'],values['recipent'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length' : len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please subbly a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message' : 'New Nodes have been added',
        'total_nodes' : list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message' : 'The chain has been replaced',
            'new_chain' : blockchain.chain
        }
    else:
        response = {
            'message' : 'The chain is authorative',
            'chain' : blockchain.chain
        }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)