# BlockchainProject
First project which involves creating a blockchain using Python. Always wanted to learn more about Blockchain so decided to build a blockchain from
scratch with the help of a tutorial and was finally able to do something in cryptocurrency.

The project had several prequistes which were : 

  Make sure [Python 3.6+](https://www.python.org/downloads/) is installed.
  
  Flask library for HTTP requests
  ``` 
  $ pip install Flask==0.12.2
  ```
 
  requests
  ```
  $ pip install requests==2.18.4
  ```

  Run the server:
  
    $ python3.8 blockchain.py
    
    $ pipenv run python blockchain.py
 
 
  ` Blockchain.postman_collection.json ` contains a Postman collection of various HTTP requests:
 
      * Mine a Block - `http://localhost:5000/mine` GET method
      
      * Transactions - `http://localhost:5000/transactions/new` POST method
      
      * Mined 3 blocks, chain of 4 blocks 
        
        1. 'http://localhost:5000/mine' GET method - 3 times to mine 3 blocks
        
        2. 'http://localhost:5000/chain' GET method - to see the blockchain of 4 blocks
        
      * Register a new node on another port - `http://localhost:5000/nodes/register` POST method
