import requests


def main():
    contract_address = "0xcontractAddress"
    api_key = '1122-122-23443-1133'
    rest_api_endpoint = 'https://beta-api.ethvigil.com/v0.1'
    method_args = {'spender': '0x774246187E1E2205C5920898eEde0945016080Df', 'addedValue': 1000}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{rest_api_endpoint}/contract/{contract_address}/increaseAllowance'
    print('Calling increaseAllowance()\n........')
    print(f'Contract: {contract_address}')
    print(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    print(r.text)


if __name__ == '__main__':
    main()