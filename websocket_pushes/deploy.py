from ethvigil.EVCore import EVCore
from websocket_listener import EthVigilWSSubscriber
import queue
import asyncio
import time
import signal
import json
# from .exceptions import ServiceExit


class ServiceExit(Exception):
    pass


update_q = queue.Queue()
update_map = dict()


def get_serviceexit_wrapper():
    def deco(func):
        def mod_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceExit:
                pass
            except Exception as e:
                print('Received exception running main()\n', e, e.__context__)
            finally:
                t.shutdown_flag.set()
                t.join()
        return mod_func
    return deco


handle_serviceexit = get_serviceexit_wrapper()


async def async_shutdown(signal, loop):
    # print(f'Received exit signal {signal.name}...')
    tasks = [t for t in asyncio.Task.all_tasks() if t is not
             asyncio.Task.current_task()]

    [task.cancel() for task in tasks]

    # print(f'Cancelling {len(tasks)} outstanding tasks')
    await asyncio.gather(*tasks)
    loop.stop()
    # print('Event loop Shutdown complete.')


def sync_shutdown(signum, frame):
    # print('Caught signal %d' % signum)
    raise ServiceExit


@handle_serviceexit
def main():
    r = evc.deploy(
        contract_file='microblog.sol',
        contract_name='Microblog',
        inputs={
            '_ownerName': 'Anomit',
            '_blogTitle': 'Blog'
        }
    )
    # print(r)
    contract_addr = r['contract']
    deploying_tx = r['txhash']
    print('Contract to be deployed at: ', contract_addr)
    print('Waiting for confirmation of contract deployment transaction...')
    while True:
        p = update_q.get()
        p = json.loads(p)
        # print(p)
        update_q.task_done()
        if p['txHash'] == deploying_tx:
            print('Received deployment transaction confirmation: ', deploying_tx)
            break
        time.sleep(5)
    contract_instance = evc.generate_contract_sdk(
        contract_address=contract_addr,
        app_name='microblog'
    )
    tx_response = contract_instance.addPost(
        **{
            'title': str(time.time()),
            'body': 'Body',
            'url': 'not applicable',
           'photo': 'not applicable'
        }
    )
    tx = tx_response[0]['txHash']
    print('Addpost tx response: ', tx)
    while True:
        # wait to get update
        p = update_q.get()
        p = json.loads(p)
        update_q.task_done()
        # print('Received WS update after addpost(): ', p)
        if p.get('txHash') == tx and p.get('type') == 'contractmon':
            print('Received transaction confirmation: ', tx)
            break
        time.sleep(5)


if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        main_loop.add_signal_handler(
            s, lambda s=s: asyncio.get_event_loop().create_task(async_shutdown(s, main_loop)))
    for s in signals:
        signal.signal(s, sync_shutdown)

    evc = EVCore(verbose=False)
    api_read_key = evc._api_read_key
    t = EthVigilWSSubscriber(kwargs={
        'api_read_key': api_read_key,
        'update_q': update_q,
        'ev_loop': main_loop,
        'filter': 'contractmon'  # yet to be implemented
    })
    t.start()

    try:
        main()
    except ServiceExit:
        pass
