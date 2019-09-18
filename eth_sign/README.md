## Signing and Verifying messages in Ethereum

The guide will introduce you to sending an offline signed message to a smart contract via the EthVigil API endpoints.
The signing method used to demonstrate this example is the legacy [`eth_sign`](https://github.com/ethereum/wiki/wiki/JSON-RPC#eth_sign)

The verification happens on contract and we monitor corresponding events for that in a webhook integration.

These steps are also packaged into a CLI tool designed in Python for you to play around with a pre-supplied contract.



## Please refer to [this doc](https://ethvigil.com/docs/eth_sign_example_code/) for a walkthrough.

### Populate `settings.json`
Rename `settings.example.json` to `settings.json`

These are the initial contents of the file:

```json
{
  "development": {
    "privatekey": "",
    "contractAddress": "",
    "REST_API_ENDPOINT": "https://beta-api.ethvigil.com/v0.1",
    "INTERNAL_API_ENDPOINT": "https://beta.ethvigil.com/api",
    "ETHVIGIL_USER_ADDRESS": "0xaddr",
    "ETHVIGIL_API_KEY": "1212-1212-12-12"
  }
}
```
Enter the appropriate values for the following keys
* `privatekey`
* `ETHVIGIL_USER_ADDRESS` -- associated with the above private key
* `ETHVIGIL_API_KEY` -- a token passed in HTTP request headers to authenticate POST calls. Works with GET calls too.

>Hint: If you have `ev-cli` installed, you can use [dumpsettings](https://ethvigil.com/docs/cli_onboarding#backup-settings-and-recover-later) to recover your EthVigil credentials

Leave the `contractAddress` field as it is.
Fill it up once you deploy the `ERC20Mintable.sol` contract through the python script.

## Setting up webhook listener server

`python webhook_listener.py`

## Interacting with the smart contract

### Work directly with the CLI script
Install the package requirements

`pip install -r requirements.txt`

`python eth_sign_cli.py deploy`

**----OR----**

### Install as an executable

```
~/workspace/api-usage-examples/eth_sign$ pip install -e .
```

If everything goes well,

`ethsign-cli deploy`

## Setting up the contract

### Deploy the contract

```
$ python eth_sign_cli.py deploy 
OR 
$ ethsign-cli deploy

Contract address was not supplied in configuration
Deployed contract results
{
    'success': True, 
    'data': {
        'contract': '0xbfd6eabcb94eb1dea59d8a8a5019699c18681cb0', 
        'gas': '145790', 
        'txhash': '0x198c9fcf9a0dcd12502e8db78f87ebc53b0e9198ef7f628271ef6081e0d35847', 
        'hash': '0x198c9fcf9a0dcd12502e8db78f87ebc53b0e9198ef7f628271ef6081e0d35847'
    }
}

Copy the contract address into settings.json
```

### Register the webhook listening endpoint with the EthVigil platform
1. `python webhook_listener.py`

2. `./ngrok http 5554`

```
$ python eth_sign_cli.py registerhook https://4c1d746f.ngrok.io

{"success":true,"data":{"id":24}}
Succeeded in registering webhook with Ethvigil API...
EthVigil Hook ID: 24
```

>Refer back to the [CLI tool guide](https://ethvigil.com/docs/cli_onboarding.html#webhooks) or [web UI guide](https://ethvigil.com/docs/web_onboarding/#webhooks) to learn how to add webhook integrations on EthVigil beta

### Subscribe to all events emitted from this contract

``` 
$ python eth_sign_cli.py addhooktoevent 24 '*'

Registering | hook ID: 24 | events: ['*'] | contract: 0xee07ee1a2e1dfbf307de512ce57bd9db7d824755
{"success":true,"subscribedEvents":["*"]}
Succeeded in adding hook
```

## Send a signed message to the contract
The command format is `submitconfirmation <unique sequence ID/nonce> <private key used to sign the message>`
``` 
$ python eth_sign_cli.py submitconfirmation 1 0x080a12470a639f95139e5e2d9fc7ca597869a42de9bfab4969a3a57a89b0c84a

Signing data with settlementid, contractaddr...
1
0xBFd6eabcB94eB1dEA59d8A8a5019699C18681CB0
Signed message hash: 0xd093bf19f8e5d7526953f63b7721628b95820e94cf42298f97cd4502b61ff392024b4030ee7db3f74690e721289b287583d72ccd8ad297e69c822eb4f1f87c2a1b
{"success": true, "data": [{"txHash": "0x34d95ba2cdfdc4abbcc9b2627a8956c16753023903e14a4a8f0d2cef42a614fe"}]}
```

The public Ethereum address corresponding to the private key `0x080a12470a639f95139e5e2d9fc7ca597869a42de9bfab4969a3a57a89b0c84a` is `0x774246187E1E2205C5920898eEde0945016080Df`

## Verify if the recovered signer address on the contract is the same as expected

The webhook listening endpoint receives the following update

``` 
========New event received========

ConfirmationSigRecieved

---JSON Payload delivered-----

{
    'txHash': '0x34d95ba2cdfdc4abbcc9b2627a8956c16753023903e14a4a8f0d2cef42a614fe', 
    'logIndex': 1, 
    'blockNumber': 1303866, 
    'transactionIndex': 0, 
    'contract': '0xbfd6eabcb94eb1dea59d8a8a5019699c18681cb0', 
    'event_name': 'ConfirmationSigRecieved', 
    'event_data': 
        {'signer': '0x774246187e1e2205c5920898eede0945016080df', 'uniqueID': 1}, 
    'ethvigil_event_id': 104, 
    'ctime': 1568576475
}
```

As expected, the retrieved signer in the event data is the same: `0x774246187e1e2205c5920898eede0945016080df`
