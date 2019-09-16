import click
import requests
from eth_account.messages import defunct_hash_message
from eth_account.account import Account
from eth_abi import is_encodable
from eth_abi.packed import encode_abi_packed, encode_single_packed
import json
from dynaconf import settings
import eth_utils


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


def solidityKeccak(abi_types, values, validity_check=False):
    """
    Executes keccak256 exactly as Solidity does.
    Takes list of abi_types as inputs -- `[uint24, int8[], bool]`
    and list of corresponding values  -- `[20, [-1, 5, 0], True]`

    Adapted from web3.py
    """
    if len(abi_types) != len(values):
        raise ValueError(
            "Length mismatch between provided abi types and values.  Got "
            "{0} types and {1} values.".format(len(abi_types), len(values))
        )
    if validity_check:
        for t, v in zip(abi_types, values):
            if not is_encodable(t, v):
                print(f'Value {v} is not encodable for ABI type {t}')
                return False
    hex_string = eth_utils.add_0x_prefix(''.join(
        encode_single_packed(abi_type, value).hex()
        for abi_type, value
        in zip(abi_types, values)
    ))
    # hex_string = encode_abi_packed(abi_types, values).hex()
    return eth_utils.keccak(hexstr=hex_string)


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

    sig_msg = Account.signHash(message_hash, private_key)
    with open('./SignerTesting.sol', 'r') as f:
        contract_code = f.read()
    deploy_params = {
        'msg': msg,
        'sig': sig_msg.signature.hex(),
        'name': 'SignerTesting',
        'inputs': [],
        'code': contract_code
    }
    # API call to deploy
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    r = requests.post(ctx_obj['internal_api_endpoint']+'/deploy', json=deploy_params, headers=headers)
    rj = r.json()
    click.echo('Deployed contract results')
    click.echo(rj)
    if rj['success']:
        click.echo('Copy the contract address into settings.json')


@cli.command()
@click.argument('uniqueid', required=True, type=int)
@click.argument('privatekey', required=True)
@click.pass_obj
def submitConfirmation(ctx_obj, uniqueid, privatekey):
    api_key = ctx_obj['api_key']
    private_key = privatekey
    contract = ctx_obj['contract_address']
    contract = eth_utils.to_checksum_address(contract)
    signed_specific_msg = sign_confirmation(uniqueid, contract, private_key)
    method_args = {
        'uniqueID': uniqueid,
        'sig': signed_specific_msg
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{ctx_obj["rest_api_endpoint"]}/contract/{ctx_obj["contract_address"]}/submitConfirmation'
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    print(r.text)


def sign_confirmation(unique_id, contractaddr, private_key):
    print('Signing data with settlementid, contractaddr...')
    print(unique_id)
    print(contractaddr)
    hash = solidityKeccak(abi_types=['uint256', 'address'], values=[unique_id, contractaddr], validity_check=True)
    msg_hash = defunct_hash_message(hexstr=hash.hex())
    signed_msg_hash = Account.signHash(msg_hash, private_key)
    click.echo(f'Signed message hash: {signed_msg_hash.signature.hex()}')
    # return bytes.fromhex(s=signed_msg_hash.signature.hex())
    return signed_msg_hash.signature.hex()



@cli.command()
@click.pass_obj
def init(ctx_obj):
    print("Got context object")
    print(ctx_obj)


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


if __name__ == '__main__':
    cli()
