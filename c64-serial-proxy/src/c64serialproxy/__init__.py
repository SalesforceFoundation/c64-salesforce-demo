from gevent import monkey
monkey.patch_all()

import gevent
import gevent.queue
import click
from serial import serial_for_url
import re
import sys
import fcntl
import os
import socket
from getpass import getpass
from salesforce_requests_oauthlib import SalesforceOAuth2Session
from urllib import urlencode
from salesforce_streaming_client import SalesforceStreamingClient


username = os.environ.get('SALESFORCE_USERNAME')
password = os.environ.get('SALESFORCE_PASSWORD') or getpass(
    'Enter password for {0}: '.format(username)
)

# Yep, a global.
session = None


def search_handler(processor_output_queue, processor_id,
                   previous_command_state, command_args):
    response = session.get(
        '/services/data/vXX.X/parameterizedSearch/',
        params={
            'q': command_args[0],
            'overallLimit': '10',
            'sobject': 'Contact',
            'Contact.fields': 'Name,Phone'
        }
    ).json()

    if 'searchRecords' in response:
        return _query_search_response_builder(
            processor_output_queue,
            processor_id,
            'search',
            len(response['searchRecords']),
            response['searchRecords']
        )
    else:
        # Sorry for not duck typing
        payload = {
            'event': 'search error',
            'processor_id': processor_id
        }
        if isinstance(response, list):
            payload['error'] = response[0][u'message']
        else:
            print response
        processor_output_queue.put(payload)


def update_handler(processor_output_queue, processor_id,
                   previous_command_state, command_args):
    record_handle, field_handle, value = command_args[0].split(None, 2)
    field_handle = int(field_handle)
    response = session.patch(
        '/services/data/vXX.X/sobjects/{0}/{1}'.format(
            previous_command_state['sobject_name'],
            previous_command_state['Ids'][record_handle]
        ),
        json={
            previous_command_state['fields'][field_handle]: value
        }
    )
    if response.status_code == 204:
        processor_output_queue.put({
            'event': 'update done',
            'processor_id': processor_id
        })
    else:
        processor_output_queue.put({
            'event': 'update error',
            'processor_id': processor_id
        })


def query_handler(processor_output_queue, processor_id, previous_command_state,
                  command_args):
    response = session.get('/services/data/vXX.X/query/?{0}'.format(
        urlencode({'q': command_args[0]})
    )).json()
    # Ignoring done for now
    if 'records' in response:
        return _query_search_response_builder(
            processor_output_queue,
            processor_id,
            'query',
            response['totalSize'],
            response['records']
        )
    else:
        # Sorry for not duck typing
        payload = {
            'event': 'query error',
            'processor_id': processor_id
        }
        if isinstance(response, list):
            payload['error'] = response[0][u'message']
        else:
            print response
        processor_output_queue.put(payload)


def _query_search_response_builder(processor_output_queue, processor_id,
                                   query_or_search, size, records):
        processor_output_queue.put({
            'event': '{0} count'.format(query_or_search),
            'processor_id': processor_id,
            'count': size
        })

        to_return = {
            'Ids': {},
            'fields': {}
        }
        for i in xrange(len(records)):
            record = records[i]
            sobject_type = record[u'attributes'][u'type']
            to_return['Ids'][chr(97 + i)] = \
                record[u'attributes'][u'url'].rsplit('/', 1)[1]
            del record[u'attributes']

            if i == 0:
                to_return['sobject_name'] = sobject_type

                sorted_keys = sorted(record.keys())
                to_return['fields'] = dict(enumerate(sorted_keys, 1))

                # Gather field names so we can send them along
                processor_output_queue.put({
                    'event': '{0} fields'.format(query_or_search),
                    'processor_id': processor_id,
                    'fields': [name.encode('ascii', errors='replace')
                               for name
                               in sorted_keys],
                    'type': sobject_type
                })

            processor_output_queue.put({
                'event': '{0} record'.format(query_or_search),
                'processor_id': processor_id,
                'record': record
            })
        processor_output_queue.put({
            'event': '{0} done'.format(query_or_search),
            'processor_id': processor_id
        })

        return to_return


# Handlers should put responses suitable for the c64 to handle into
# processor_output_queue
command_map = {
    'query': query_handler,
    'search': search_handler,
    'update': update_handler
}

re_allowed_chars = re.compile(
    r'[^A-Za-z\xc1-\xda\x11-\x14 0-9.,?\'"!@#$%^&*()-_=+;:<>/\\|}{[\]`~\r]*'
)


def to_petscii(inp):
    inp = inp.replace(r'\r', '')
    inp = inp.replace(r'\n', '\r')
    inp = re_allowed_chars.sub('', inp)
    inp = inp.replace(r'_', '-')
    inp = inp.replace(r'`', '\x27')  # '`' in petscii

    petscii_inp = []
    for char in inp:
        char_ord = ord(char)
        if 65 <= char_ord <= 90:
            petscii_inp.append(chr(char_ord + 32))
        elif 97 <= char_ord <= 122:
            petscii_inp.append(chr(char_ord - 32))
        elif 193 <= char_ord <= 218:
            petscii_inp.append(chr(char_ord - 128))
        else:
            petscii_inp.append(char)

    return ''.join(petscii_inp)


def from_petscii(inp):
    return to_petscii(inp.replace(r'\r', '\n')).replace(r'\r', '\n')


def write(control, serial_conn, write_queue):
    while not control['die']:
        to_write = None
        with gevent.Timeout(2, False) as timeout:
            to_write = write_queue.get()
        if to_write is not None:
            to_write = to_petscii(to_write)
            print 'writing', to_write
            for char in to_write:
                serial_conn.write(char)
                gevent.sleep(0.1)
            gevent.sleep(0.5)
            serial_conn.flush()


def read(control, serial_conn, command_queue):
    command = []
    while not control['die']:
        char = None
        with gevent.Timeout(2, False) as timeout:
            char = serial_conn.read()
        if char is None:
            continue
        if char == '\x00':
            command_queue.put(''.join(command))
            command = []
        else:
            command.append(from_petscii(char))


def gather_processor_output(control, processor_output_queue, write_queue):
    while not processor_output_queue.empty() or not control['die']:
        processor_output = None
        with gevent.Timeout(2, False) as timeout:
            processor_output = processor_output_queue.get()
        if processor_output is not None:
            print 'Processor {0}: {1}'.format(
                processor_output['event'],
                processor_output['processor_id']
            )

            # For sobjects returned by a rest api call
            event_tokens = processor_output['event'].split()
            if event_tokens[0] == 'query' or event_tokens[0] == 'search':
                if event_tokens[1] == 'count':
                    write_queue.put('{0} count {1}\\n'.format(
                        event_tokens[0],
                        str(processor_output['count'])
                    ))
                elif event_tokens[1] == 'fields':
                    write_queue.put('{0} fields {1} {2}\\n'.format(
                        event_tokens[0],
                        processor_output['type'],
                        ' '.join(processor_output['fields'])
                    ))
                elif event_tokens[1] == 'record':
                    write_queue.put('{0} record '.format(
                        event_tokens[0]
                    ))
                    record = processor_output['record']

                    value_lengths = []
                    values = []
                    for field_name in sorted(record.keys()):
                        value = record[field_name]
                        if value is None:
                            value = ''
                        value = value.encode('ascii', errors='replace')

                        value_lengths.append(str(len(value)))
                        values.append(value)
                    write_queue.put(','.join(value_lengths))
                    write_queue.put(' ')
                    write_queue.put(''.join(values))
                    write_queue.put('\\n')
                elif event_tokens[1] == 'error':
                    write_queue.put('{0} error {1}\\n'.format(
                        event_tokens[0],
                        processor_output['error']
                    ))
                else:
                    write_queue.put('{0}\\n'.format(processor_output['event']))
            else:
                write_queue.put('{0}\\n'.format(processor_output['event']))


# Runs in the main greenlet
# We expect these command handlers to spend most of their time
# doing network stuff, so we don't need a child process.
def command_dispatch(control, command_queue, write_queue):
    processor_output_queue = gevent.queue.Queue()
    processor_output_greenlet = gevent.spawn(
        gather_processor_output,
        control,
        processor_output_queue,
        write_queue
    )
    processor_id = 0
    previous_command_state = None
    while not control['die']:
        command = ''
        with gevent.Timeout(5, False) as timeout:
            command = command_queue.get()
        command_segments = command.split(':', 1)
        if command_segments[0] in command_map:
            processor = gevent.spawn(
                command_map[command_segments[0]],
                processor_output_queue,
                processor_id,
                previous_command_state,
                command_segments[1:]
            )
            processor_id += 1

            # Don't loop again until this processor is done.  We could store
            # these and join the list later, but for now we'd rather simplify
            # the storage of state.
            processor.join()
            previous_command_state = processor.value

    # Don't miss any processor output
    processor_output_greenlet.join()


def get_stdin(control, write_queue):
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
    while True:
        try:
            gevent.socket.wait_read(sys.stdin.fileno(), 2)
        except socket.timeout:
            continue
        else:
            line = sys.stdin.readline().strip()
            if line.lower() == 'control-quit':
                control['die'] = True
                break
            write_queue.put('{0}\\n'.format(line))


class C64StreamingClient(SalesforceStreamingClient):
    def __init__(self, client_id, client_secret, username,
                 control, write_queue, sandbox=False,
                 replay_client_id=None):

        self.control = control
        self.write_queue = write_queue

        super(C64StreamingClient, self).__init__(
            client_id,
            client_secret,
            username,
            sandbox=sandbox,
            replay_client_id=replay_client_id
        )

    def send_serial(self, connect_response_element):
        self.write_queue.put('l\\n')


@click.command()
@click.argument('device_name')
@click.option('-s', '--streaming', is_flag=True)
def main(device_name, streaming):
    oauth_client_id = os.environ.get('SALESFORCE_CLIENT_ID')
    oauth_client_secret = os.environ.get('SALESFORCE_CLIENT_SECRET')

    write_queue = gevent.queue.Queue()
    command_queue = gevent.queue.Queue()

    control = {
        'die': False
    }

    serial_conn = serial_for_url(device_name, baudrate=1200)
    serial_conn.write('\x00\\n')

    reader_greenlet = gevent.spawn(read, control, serial_conn, command_queue)
    writer_greenlet = gevent.spawn(write, control, serial_conn, write_queue)
    stdin_greenlet = gevent.spawn(get_stdin, control, write_queue)

    all_greenlets = [reader_greenlet, writer_greenlet, stdin_greenlet]
    try:
        if streaming:
            with C64StreamingClient(
                oauth_client_id, oauth_client_secret, username, control,
                write_queue
            ) as streaming_client:
                streaming_client.subscribe(
                    '/event/SoldSomething__e',
                    'send_serial'
                )
                streaming_client.start()
                streaming_client.block()
        else:
            global session
            session = SalesforceOAuth2Session(
                oauth_client_id,
                oauth_client_secret,
                username,
                sandbox=False,
                password=password
            )
            command_dispatch(control, command_queue, write_queue)
    except KeyboardInterrupt:
        pass
    try:
        print 'Stopping...'
        gevent.joinall(all_greenlets)
    except KeyboardInterrupt:
        print [bool(glet) for glet in all_greenlets]
