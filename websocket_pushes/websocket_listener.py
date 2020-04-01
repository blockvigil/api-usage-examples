import json
import websockets
import asyncio
import async_timeout
import queue
import threading
import time


async def consumer_contract(read_api_key, update_q: queue.Queue):
    async with websockets.connect('wss://beta.ethvigil.com/ws') as ws:
        await ws.send(json.dumps({'command': 'register', 'key': read_api_key}))
        ack = await ws.recv()
        ack = json.loads(ack)
        try:
            ack_cmd = ack['command']
        except KeyError:
            print('Bad response')
            await ws.close()
            return
        else:
            if ack_cmd != 'register:ack':
                print('Registration not acknowledged')
                await ws.close()
                return
        sessionID = ack['sessionID']
        # async for msg in ws:
        #    print(msg)
        while True:
            try:
                async with async_timeout.timeout(10):
                    msg = await ws.recv()
                    # observed: heartbeat messages being delivered out of sequence, gotta ignore
                    if json.loads(msg).get('command') != 'heartbeat':
                        update_q.put(msg)
            except asyncio.TimeoutError:
                await ws.send(json.dumps({'command': 'heartbeat', 'sessionID': sessionID}))
                ack = await ws.recv()
                # print(ack)
            except asyncio.CancelledError:
                # print('Received cancel on WS listener coro')
                try:
                    await ws.send(json.dumps({'command': 'unregister', 'key': read_api_key}))
                    ack = await ws.recv()
                    await ws.close()
                except:  # ignore any residual shutdown errors
                    pass
                finally:
                    break


class EthVigilWSSubscriber(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        super().__init__(group=group, target=target, name=name, daemon=True)
        self._args = args
        self._kwargs = kwargs
        self._api_read_key = self._kwargs['api_read_key']
        self._update_q = self._kwargs['update_q']
        self._ev_loop = self._kwargs['ev_loop']

        self.shutdown_flag = threading.Event()

    def run(self) -> None:
        asyncio.set_event_loop(self._ev_loop)
        try:
            asyncio.get_event_loop().run_until_complete(consumer_contract(self._api_read_key, self._update_q))
            while not self.shutdown_flag.is_set():
                time.sleep(1)
        except ServiceExit:
            pass
        except Exception as e:
            print('Received exception in child thread\n', e, e.__context__)
        # print('Stopping thread ', self.ident)
