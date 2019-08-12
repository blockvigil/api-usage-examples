## Populate `settings.json`
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

Leave the `contractAddress` field as it is. 
Fill it up once you deploy the `ERC20Mintable.sol` contract through the python script.

## Setting up webhook listener server

`python webhook_listener.py`

## Interacting with the smart contract

### Work directly with the CLI script
Install the package requirements
`pip install -r requirements.txt`

`python cli.py deploy`

### Install as an executable

`pip install -e .`

If everything goes well,

`erc20-cli deploy`


## Getting help

`python cli.py --help`

`python cli.py increaseallowance --help`

OR

`erc20-cli --help`