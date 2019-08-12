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
    events_to_be_registered_on = ['Approval', 'Transfer']
    hook_id = 12  # hook ID as registered on EthVigil
    msg = 'dummystring'
    message_hash = defunct_hash_message(text=msg)
    sig_msg = Account.signHash(message_hash, private_key)
    method_args = {
        "msg": msg,
        "sig": sig_msg.signature.hex(),
        "key": api_key,
        "type": "web",
        "contract": contract,
        "id": hook_id,
        "events": events_to_be_registered_on
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    print(f'Registering | hook ID: {hook_id} | events: {events_to_be_registered_on} | contract: {contract}')
    r = requests.post(url=f'{api_endpoint}/hooks/updateEvents', json=method_args,
                      headers=headers)
    print(r.text)
    if r.status_code == requests.codes.ok:
        r = r.json()
        if r['success']:
            print('Succeeded in adding hook')
        else:
            print('Failed to add hook')
            return
    else:
        print('Failed to add hook')
        return


if __name__ == '__main__':
    main()