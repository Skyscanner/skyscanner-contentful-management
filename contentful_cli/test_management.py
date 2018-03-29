#
# Copyright 2017 Skyscanner Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
import pytest
import json
import configparser
from collections import OrderedDict
import click
import requests
import subprocess

from pprint import pprint

from contentful_cli import management

# Fixture for configuration
config = configparser.ConfigParser()
config['base_url'] = {}
config['base_url']['api'] = 'https://fakeapi'
config['base_url']['upload'] = 'https://fakeupload'


class FakeResponse:
    def __init__(self, text='', url='', status_code=0, headers=None):
        self.text = text
        self.url = url
        self.status_code = status_code
        self.headers = {} if headers is None else headers


def test_contruct_api_url(mocker):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', '')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Patch configuration overriding
    mocker.patch.object(endpoint, 'construct_config', return_value=config)

    assert endpoint.construct_base_url() == config['base_url']['api']


def test_contruct_bad_url(mocker):
    # Define a sample endpoint using an invalid
    endpoint_spec = management.Endpoint('sample', 'get', 'invalid', '/sample', '')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Patch configuration overriding
    mocker.patch.object(endpoint, 'construct_config', return_value=config)

    with pytest.raises(Exception):
        endpoint.construct_base_url()


def test_prepare_stream(mocker, capsys):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', '')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Build a sample command within an artificial context
    endpoint_cmd = endpoint.build_command()
    endpoint_ctx = endpoint_cmd.make_context('management.py', ['--prepare-stream', '--oauth-token', 'sample-token'])

    endpoint_cmd.invoke(endpoint_ctx)

    # Capture the command's stdout and stderr
    out, err = capsys.readouterr()

    out_json = json.loads(out)
    out_fixture = {'arguments': {'gateway_api_key': None}, 'operation': 'sample'}

    assert out_json == out_fixture


def test_convert_response_to_json_ordereddict():
    response = FakeResponse()
    response.text = '{"body":"OK"}'
    response.status_code = 200
    response.url = 'http://example.com'

    response_converted = management.convert_response_to_json(response)

    assert response_converted['body'] == OrderedDict([('body', 'OK')])
    assert response_converted['status_code'] == response.status_code
    assert response_converted['url'] == response.url


def test_convert_response_to_json_plaintext():
    response = FakeResponse()
    response.text = 'OK'
    response.status_code = 200
    response.url = 'http://example.com'

    response_converted = management.convert_response_to_json(response)

    assert response_converted['body'] == 'OK'
    assert response_converted['status_code'] == response.status_code
    assert response_converted['url'] == response.url


def test_arg_validation_has_no_document(capsys):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', 'D')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Build a sample command within an artificial context
    endpoint_cmd = endpoint.build_command()
    endpoint_ctx = endpoint_cmd.make_context('management.py', ['--oauth-token', 'sample-token'])

    with pytest.raises(click.exceptions.UsageError):
        endpoint_cmd.invoke(endpoint_ctx)


def test_arg_validation_has_one_document(capsys):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', 'D')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Build a sample command within an artificial context
    endpoint_cmd = endpoint.build_command()
    endpoint_ctx = endpoint_cmd.make_context('management.py', ['--document-body', 'foo', '--document-file', 'README.md', '--oauth-token', 'sample-token'])

    with pytest.raises(click.exceptions.UsageError):
        endpoint_cmd.invoke(endpoint_ctx)


def test_full_invoke(mocker):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', '')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Patch configuration overriding
    mocker.patch.object(endpoint, 'construct_config', return_value=config)

    # Create a mocked out Requests session
    session = requests.Session()
    session.request = mocker.MagicMock()

    # Make a full request
    endpoint.invoke({}, session, "test-key", "")

    # Ensure the request made it to the wire once
    assert len(session.request.call_args_list) == 1

    # Validate request attributes
    args, kwargs = session.request.call_args_list[0]

    assert args[0] == 'get'
    assert args[1] == 'https://fakeapi/sample'
    assert kwargs['params'] == {}


def run_stream_command(stream_file):
    return subprocess.run([
            sys.executable,
            './contentful_cli/management.py',
            'stream',
            '-',
            '--dry-run'
        ],
        input=stream_file,
        universal_newlines=True,
        stdout=subprocess.PIPE
    )


# Streaming is heavily tied into Click and is impractical to test internally
# Instead, a dry run is conducted that simulates a stream file
def test_stream(mocker):
    stream_file = '{"operation":"list-content-types","arguments":{"space_id":"test-space","skip":null,"limit":null}}'

    proc = run_stream_command(stream_file)

    out = json.loads(proc.stdout)

    assert out['url'] == 'https://api.contentful.com/spaces/test-space/content_types/'
    assert out['body']['params'] == {'limit': None, 'skip': None}
    assert out['operation'] == 'list-content-types'

def test_stream_with_data_argument(mocker):
    stream_file = '{"operation":"post-entry","arguments":{"space_id":"test-space","content_type":"typename","document_body": {}}}'

    proc = run_stream_command(stream_file)

    out = json.loads(proc.stdout)

    assert out['url'] == 'https://api.contentful.com/spaces/test-space/entries/'
    assert out['body']['params'] == {}
    assert out['operation'] == 'post-entry'
    assert out['body']['data'] == '{}'

def test_stream_bad_command(mocker):
    stream_file = '{"operation":"obviously-fake-command","arguments":{}}'

    proc = run_stream_command(stream_file)

    out = json.loads(proc.stdout)

    assert out['error'] == 'Operation not recognized'
    assert out['operation'] == 'obviously-fake-command'

def test_stream_bad_json(mocker):
    stream_file = 'obviously-invalid-json'

    proc = run_stream_command(stream_file)

    out = json.loads(proc.stdout)

    assert 'JSONDecodeError' in out['exception']


@pytest.mark.parametrize(
    'status_codes,expected_codes,expected_retries,expected_sleeps',
    [
        # Succeed first time:
        ([200], [200], [False], []),
        # One retry:
        ([429,200], [429,200], [True,False], [1]),
        # Maximum retries:
        ([429,429,429,429,429,200], [429,429,429,429,429,200], [True,True,True,True,True,False], [1,4,16,64,256]),
        # Too many retries:
        ([429,429,429,429,429,429,200], [429] * 6, [True,True,True,True,True,False], [1,4,16,64,256]),
        # Too many retries:
        ([429]*20 + [200], [429] * 6, [True,True,True,True,True,False], [1,4,16,64,256]),
    ]
)
def test_when_streaming_429s_are_retried(
        mocker, status_codes, expected_codes, expected_retries, expected_sleeps):
    # Define a sample endpoint using the API subdomain
    endpoint_spec = management.Endpoint('sample', 'get', 'api', '/sample', '')
    endpoint = management.construct_endpoint(endpoint_spec)

    # Patch configuration overriding
    mocker.patch.object(endpoint, 'construct_config', return_value=config)

    # Create a mocked out Requests session
    session = mocker.Mock()

    session.request.side_effect = [
        FakeResponse(status_code=code)
        for code in status_codes
    ]

    # Make a full request
    echo_output = mocker.patch('contentful_cli.management.echo_output')
    sleep = mocker.patch('time.sleep')

    endpoint.invoke_streaming(
        ctx=None,
        arguments={},
        session=session,
        oauth_token="test-key",
        gateway_api_key="",
        echo_to_stdout=False,
        log_file=None,
        retry=True,
        run=True)
    logged_objects = [l[0][0] for l in echo_output.call_args_list]
    sleep_times = [l[0][0] for l in sleep.call_args_list]

    assert (
        [obj['retrying'] for obj in logged_objects] == 
        expected_retries
    )
    assert (
        [obj['status_code'] for obj in logged_objects] == 
        expected_codes
    )
    assert sleep_times == expected_sleeps
