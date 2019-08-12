import click
import requests

from eth_account.messages import defunct_hash_message
from eth_account.account import Account
import json
from dynaconf import settings


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    private_key = settings['privatekey']
    api_endpoint = settings['INTERNAL_API_ENDPOINT']
    rest_api_endpoint = settings['REST_API_ENDPOINT']
    api_key = ev_login(api_endpoint, private_key)
    contract_addr = settings['contractAddress']
    if contract_addr == "" or not contract_addr:
        click.echo("Contract address was not supplied in configuration")
    ctx.obj = {
        'api_key': api_key,
        'private_key': private_key,
        'contract_address': contract_addr,
        'internal_api_endpoint': api_endpoint,
        'rest_api_endpoint': rest_api_endpoint
    }


def ev_login(api_endpoint, private_key):
    msg = "Trying to login"
    message_hash = defunct_hash_message(text=msg)
    signed_msg = Account.signHash(message_hash, private_key)
    # --ethvigil API CALL---
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    r = requests.post(api_endpoint + '/login', json={'msg': msg, 'sig': signed_msg.signature.hex()}, headers=headers)
    if r.status_code == requests.codes.ok:
        r = r.json()
        return r['data']['key']
    else:
        return None


@cli.command()
@click.pass_obj
def deploy(ctx_obj):
    """
    Deploys a new instance of ERC20Mintable.sol on EthVigil.
    When prompted, enter a JSON-compatible list of constructor inputs to be passed on to the ERC20Mintable contract.

    For example, ["My Token", "SYMBOL", 18] corresponding to ERC20 standards: token name, token symbol, token decimals
    NOTE: Enter double quoted strings. Single quoted strings are not supported as JSON serialized.

    Check deploy.py for a code example
    """
    msg = "Trying to deploy"
    message_hash = defunct_hash_message(text=msg)
    private_key = ctx_obj['private_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr != '':
        if click.confirm('You already have a contract address specified in the settings file. '
                         'Do you want to proceed with deploying another contract? '):
            pass
        else:
            return
    click.echo('Enter the list of constructor inputs: ')
    constructor_inputs = input()
    if constructor_inputs.strip() == "":
        if click.confirm('Do you want to use the defaults ["My Token", "SYMBOL", 18]'):
            constructor_inputs = ["My Token", "SYMBOL", 18]
        else:
            return
    else:
        try:
            constructor_inputs = json.loads(constructor_inputs)
        except json.JSONDecodeError:
            click.echo("Enter a valid JSON list for constructor inputs")
            if click.confirm('Do you want to use the defaults ["My Token", "SYMBOL", 18]'):
                constructor_inputs = ["My Token", "SYMBOL", 18]
            else:
                return
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
    click.echo('Deploying with constructor arguments: ')
    click.echo(constructor_inputs)
    # API call to deploy
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    r = requests.post(ctx_obj['internal_api_endpoint']+'/deploy', json=deploy_params, headers=headers)
    rj = r.json()
    click.echo('Deployed contract results')
    click.echo(rj)
    if rj['success']:
        click.echo('Copy the contract address into settings.json')


@cli.command()
@click.pass_obj
def init(ctx_obj):
    print("Got context object")
    print(ctx_obj)


@cli.command()
@click.argument('to_address', required=True)
@click.argument('amount', required=True)
@click.pass_obj
def mint(ctx_obj, to_address, amount):
    """
    Mints new tokens and transfers them to to_address.

    <to_address>: address to which new tokens will be minted and transferred to.
    Note: Increases totalSupply of the ERC20 contract.

    <amount>: units of new tokens to be minted

    """
    api_key = ctx_obj['api_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    method_args = {'account': to_address, 'amount': amount}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{contract_addr}/mint'
    click.echo('Calling mint()\n........')
    click.echo(f'Contract: {contract_addr}')
    click.echo(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    click.echo(r.text)


@cli.command()
@click.argument('account', required=True)
@click.pass_obj
def balanceof(ctx_obj, account):
    """
    Fetches the tokens allotted to an address specified by <account> on this contract instance
    """
    api_key = ctx_obj['api_key']
    rest_api_endpoint = ctx_obj['rest_api_endpoint']
    contract_address = ctx_obj['contract_address']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{rest_api_endpoint}/contract/{contract_address}/balanceOf/{account}'
    r = requests.get(url=method_api_endpoint, headers=headers)
    print(r.text)


@cli.command()
@click.argument('spender_address', required=True)
@click.argument('tokens', required=True)
@click.pass_obj
def approve(ctx_obj, spender_address, tokens):
    """
    Approves <spender_address> to spend  <tokens> on behalf of msg.sender
    """
    api_key = ctx_obj['api_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    method_args = {'spender': spender_address, 'value': tokens}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{contract_addr}/approve'
    click.echo('Calling approve()\n........')
    click.echo(f'Contract: {contract_addr}')
    click.echo(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    click.echo(r.text)


@cli.command()
@click.argument('sender', required=True)
@click.argument('recipient', required=True)
@click.argument('amount', required=True)
@click.pass_obj
def transferfrom(ctx_obj, sender, recipient, amount):
    """
    Moves `amount` tokens from `sender` to `recipient` using the allowance mechanism.
    `amount` is then deducted from the caller's allowance.

    NOTE: The EthVigil API signer address for Gorli testnet, 0x3dc7d43d5f180661970387a4f89c7e715b567512, needs to be approve()-d by the <sender> first.
    """
    api_key = ctx_obj['api_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    method_args = {'sender': sender, 'recipient': recipient, 'amount': amount}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{contract_addr}/transferFrom'
    click.echo('Calling transferFrom()\n........')
    click.echo(f'Contract: {contract_addr}')
    click.echo(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    click.echo(r.text)


@cli.command()
@click.argument('spender', required=True)
@click.argument('added_value')
@click.pass_obj
def increaseallowance(ctx_obj, spender, added_value):
    """
    Atomically increases the allowance granted to <spender> by the caller.
     * This is an alternative to approve()
     *
     * Emits an Approval event indicating the updated allowance.
    """
    api_key = ctx_obj['api_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    method_args = {'spender': spender, 'addedValue': added_value}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{contract_addr}/increaseAllowance'
    click.echo('Calling increaseAllowance()\n........')
    click.echo(f'Contract: {contract_addr}')
    click.echo(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    click.echo(r.text)


@cli.command()
@click.argument('spender', required=True)
@click.argument('subtracted_value', required=True)
@click.pass_obj
def decreaseallowance(ctx_obj, spender, subtracted_value):
    """
        Atomically decreases the allowance granted to <spender> by the caller.
         * This is an alternative to approve()
         *
         * Emits an Approval event indicating the updated allowance.
    """
    api_key = ctx_obj['api_key']
    contract_addr = ctx_obj['contract_address']
    if contract_addr == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    method_args = {'spender': spender, 'subtractedValue': subtracted_value}
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{contract_addr}/decreaseAllowance'
    click.echo('Calling decreaseAllowance()\n........')
    click.echo(f'Contract: {contract_addr}')
    click.echo(f'Method arguments:\n===============\n{method_args}')
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    click.echo(r.text)


@cli.command()
@click.argument('owner', required=True)
@click.argument('spender', required=True)
@click.pass_obj
def allowance(ctx_obj, owner, spender):
    """
    Returns the remaining number of tokens that `spender` will be allowed to spend on behalf of `owner` through {transferFrom}.
    This is zero by default.
    """
    api_key = ctx_obj['api_key']
    contract_address = ctx_obj['contract_address']
    rest_api_endpoint = ctx_obj['rest_api_endpoint']
    if contract_address == "":
        click.echo('No contract address configured to send the transaction to. Check settings.json')
        return
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{rest_api_endpoint}/contract/{contract_address}/allowance/{owner}/{spender}'
    r = requests.get(url=method_api_endpoint, headers=headers)
    print(r.text)

@cli.command()
@click.argument('url', required=True)
@click.pass_obj
def registerhook(ctx_obj, url):
    contract = ctx_obj['contract_address']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    msg = 'dummystring'
    message_hash = defunct_hash_message(text=msg)
    sig_msg = Account.signHash(message_hash, ctx_obj['private_key'])
    method_args = {
        "msg": msg,
        "sig": sig_msg.signature.hex(),
        "key": ctx_obj['api_key'],
        "type": "web",
        "contract": contract,
        "web": url
    }
    r = requests.post(url=f'{ctx_obj["internal_api_endpoint"]}/hooks/add', json=method_args, headers=headers)
    click.echo(r.text)
    if r.status_code == requests.codes.ok:
        r = r.json()
        if not r['success']:
            click.echo('Failed to register webhook with Ethvigil API...')
        else:
            hook_id = r["data"]["id"]
            click.echo('Succeeded in registering webhook with Ethvigil API...')
            click.echo(f'EthVigil Hook ID: {hook_id}')
    else:
        click.echo('Failed to register webhook with Ethvigil API...')


@cli.command()
@click.argument('hookid', required=True)
@click.argument('events', required=True)
@click.pass_obj
def addhooktoevent(ctx_obj, hookid, events):
    msg = 'dummystring'
    message_hash = defunct_hash_message(text=msg)
    contract_address = ctx_obj['contract_address']
    private_key = ctx_obj['private_key']
    api_key = ctx_obj['api_key']
    api_endpoint = ctx_obj['internal_api_endpoint']
    sig_msg = Account.signHash(message_hash, private_key)
    events_to_be_registered_on = list()
    if not events:
        events_to_be_registered_on.append('*')
    else:
        for each in events.split(','):
            events_to_be_registered_on.append(each)
    method_args = {
        "msg": msg,
        "sig": sig_msg.signature.hex(),
        "key": api_key,
        "type": "web",
        "contract": contract_address,
        "id": hookid,
        "events": events_to_be_registered_on
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    click.echo(f'Registering | hook ID: {hookid} | events: {events_to_be_registered_on} | contract: {contract_address}')
    r = requests.post(url=f'{api_endpoint}/hooks/updateEvents', json=method_args,
                      headers=headers)
    click.echo(r.text)
    if r.status_code == requests.codes.ok:
        r = r.json()
        if r['success']:
            click.echo('Succeeded in adding hook')
        else:
            click.echo('Failed to add hook')
            return
    else:
        click.echo('Failed to add hook')
        return


@cli.command()
@click.pass_obj
def totalsupply(ctx_obj):
    api_key = ctx_obj['api_key']
    rest_api_endpoint = ctx_obj['rest_api_endpoint']
    contract_address = ctx_obj['contract_address']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{rest_api_endpoint}/contract/{contract_address}/totalSupply'
    r = requests.get(url=method_api_endpoint, headers=headers)
    print(r.text)


if __name__ == '__main__':
    cli()
