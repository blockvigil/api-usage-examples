from eth_account.messages import defunct_hash_message
from eth_account.account import Account
import requests


def main():
    contract = "0xcontractAddress"
    api_key = '1122-122-23443-1133'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json',
               'X-API-KEY': api_key}
    private_key = "0xprivatekeyhexstring"
    api_endpoint = "https://beta.ethvigil.com/api"
    msg = 'dummystring'
    message_hash = defunct_hash_message(text=msg)
    sig_msg = Account.signHash(message_hash, private_key)
    method_args = {
        "msg": msg,
        "sig": sig_msg.signature.hex(),
        "key": api_key,
        "type": "web",
        "contract": contract,
        "web": "https://randomstring.ngrok.io"
    }
    r = requests.post(url=f'{api_endpoint}/hooks/add', json=method_args, headers=headers)
    print(r.text)
    if r.status_code == requests.codes.ok:
        r = r.json()
        if not r['success']:
            print('Failed to register webhook with Ethvigil API...')
        else:
            hook_id = r["data"]["id"]
            print('Succeeded in registering webhook with Ethvigil API...')
            print(f'EthVigil Hook ID: {hook_id}')
    else:
        print('Failed to register webhook with Ethvigil API...')


if __name__ == '__main__':
    main()