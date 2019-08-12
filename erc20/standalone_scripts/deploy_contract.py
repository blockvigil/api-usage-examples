from eth_account.messages import defunct_hash_message
from eth_account.account import Account
import requests
import json


def main():
    msg = "Trying to deploy"
    message_hash = defunct_hash_message(text=msg)
    private_key = "0xprivatekeyhexstring"
    constructor_inputs = ['My Token', 'SYMBOL', 18]
    sig_msg = Account.signHash(message_hash, private_key)
    with open('./ERC20Mintable.sol', 'r') as f:
        contract_code = f.read()
    deploy_params = {
        'msg': msg,
        'sig': sig_msg.signature.hex(),
        'name': 'ERC20Mintable',
        'inputs': constructor_inputs,
        'code': contract_code
    }
    print('Deploying with constructor arguments: ')
    print(constructor_inputs)
    # API call to deploy
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    api_endpoint = "https://beta.ethvigil.com/api"
    r = requests.post(api_endpoint + '/deploy', json=deploy_params, headers=headers)
    rj = r.json()
    print('Deployed contract results')
    print(rj)


if __name__ == '__main__':
    main()