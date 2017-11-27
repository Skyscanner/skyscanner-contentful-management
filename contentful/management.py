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

import configparser
import json
import click
import requests
import string
import os.path
import datetime
import sys
from pathlib import Path
import time

from collections import namedtuple, OrderedDict


def convert_response_to_json(response):
    '''
    Convert a Response object to a JSON string for easier parsing by
    other scripts and programs.
    '''
    body_text = response.text
    try:
        body = json.loads(body_text, object_pairs_hook=OrderedDict)
    except ValueError:
        body = body_text
    obj = OrderedDict([
        ('url', response.url),
        ('status_code', response.status_code),
        ('body', body)
    ])
    return obj


def echo_output(obj, echo_to_stdout, log_file):
    s = json.dumps(obj)
    print(s, file=log_file, flush=True)
    if echo_to_stdout:
        print(s, flush=True)


Endpoint = namedtuple('Endpoint', 'name method subdomain template flags')

# Flags:
#  c: collection
#  D: document sent
#  v: optional version header
#  V: mandatory version header???
#  t: contentful document type header required
#  e: entry collection - allows --select and other advanced search options
#  a: asset collection - allows --mimetype-group and other advanced search options
#  o: optional organization ID
#  B: binary document
#  !: dangerous - such operations cannot be performed in streaming mode and require interactive confirmation

CONTENTFUL_ENDPOINTS = [
    Endpoint('list-content-types',      'get',    'api',    '/spaces/{space_id}/content_types/',                                   'c'),
    Endpoint('put-content-type',        'put',    'api',    '/spaces/{space_id}/content_types/{content_type_id}',                  'Dv'),
    Endpoint('get-content-type',        'get',    'api',    '/spaces/{space_id}/content_types/{content_type_id}',                  ''),
    Endpoint('put-content-type-editor', 'put',    'api',    '/spaces/{space_id}/content_types/{content_type_id}/editor_interface', 'DV'),
    Endpoint('get-content-type-editor', 'get',    'api',    '/spaces/{space_id}/content_types/{content_type_id}/editor_interface', ''),
    Endpoint('delete-content-type',     'delete', 'api',    '/spaces/{space_id}/content_types/{content_type_id}',                  'V'),
    Endpoint('publish-content-type',    'put',    'api',    '/spaces/{space_id}/content_types/{content_type_id}/published',        'V'),
    Endpoint('unpublish-content-type',  'delete', 'api',    '/spaces/{space_id}/content_types/{content_type_id}/published',        ''),
    Endpoint('list-entries',            'get',    'api',    '/spaces/{space_id}/entries/',                                         'ce'),
    Endpoint('post-entry',              'post',   'api',    '/spaces/{space_id}/entries/',                                         'Dt'),
    Endpoint('put-entry',               'put',    'api',    '/spaces/{space_id}/entries/{entry_id}',                               'Dtv'),
    Endpoint('get-entry',               'get',    'api',    '/spaces/{space_id}/entries/{entry_id}',                               ''),
    Endpoint('delete-entry',            'delete', 'api',    '/spaces/{space_id}/entries/{entry_id}',                               'V'),
    Endpoint('publish-entry',           'put',    'api',    '/spaces/{space_id}/entries/{entry_id}/published',                     'V'),
    Endpoint('unpublish-entry',         'delete', 'api',    '/spaces/{space_id}/entries/{entry_id}/published',                     'V'),
    Endpoint('archive-entry',           'put',    'api',    '/spaces/{space_id}/entries/{entry_id}/archived',                      'V'),
    Endpoint('unarchive-entry',         'delete', 'api',    '/spaces/{space_id}/entries/{entry_id}/archived',                      'V'),
    Endpoint('list-assets',             'get',    'api',    '/spaces/{space_id}/assets/',                                          'ca'),
    Endpoint('post-asset',              'post',   'api',    '/spaces/{space_id}/assets/',                                          'D'),
    Endpoint('put-asset',               'put',    'api',    '/spaces/{space_id}/assets/{asset_id}',                                'Dv'),
    Endpoint('get-asset',               'get',    'api',    '/spaces/{space_id}/assets/{asset_id}',                                ''),
    Endpoint('delete-asset',            'delete', 'api',    '/spaces/{space_id}/assets/{asset_id}',                                'V'),
    Endpoint('process-asset',           'put',    'api',    '/spaces/{space_id}/assets/{asset_id}/files/{locale}/process',         'V'),
    Endpoint('publish-asset',           'put',    'api',    '/spaces/{space_id}/assets/{asset_id}/published',                      'V'),
    Endpoint('unpublish-asset',         'delete', 'api',    '/spaces/{space_id}/assets/{asset_id}/published',                      'V'),
    Endpoint('archive-asset',           'put',    'api',    '/spaces/{space_id}/assets/{asset_id}/archived',                       'V'),
    Endpoint('unarchive-asset',         'delete', 'api',    '/spaces/{space_id}/assets/{asset_id}/archived',                       'V'),
    Endpoint('get-locales',             'get',    'api',    '/spaces/{space_id}/locales',                                          ''),
    Endpoint('list-spaces',             'get',    'api',    '/spaces/',                                                            ''),
    Endpoint('post-space',              'post',   'api',    '/spaces/',                                                            'oD'),
    Endpoint('put-space',               'put',    'api',    '/spaces/{space_id}',                                                  'oD'),
    Endpoint('get-space',               'get',    'api',    '/spaces/{space_id}',                                                  ''),
    Endpoint('delete-space',            'delete', 'api',    '/spaces/{space_id}',                                                  '!'),
    Endpoint('post-upload',             'post',   'upload', '/spaces/{space_id}/uploads',                                          'B'),
    Endpoint('get-upload',              'get',    'upload', '/spaces/{space_id}/uploads/{upload_id}',                              ''),
    Endpoint('delete-upload',           'delete', 'upload', '/spaces/{space_id}/uploads/{upload_id}',                              ''),
    Endpoint('post-webhook',            'post',   'api',    '/spaces/{space_id}/webhook_definitions',                              'D'),
    Endpoint('put-webhook',             'put',    'api',    '/spaces/{space_id}/webhook_definitions/{webhook_id}',                 'D'),
    Endpoint('get-webhook',             'get',    'api',    '/spaces/{space_id}/webhook_definitions/{webhook_id}',                 ''),
    Endpoint('delete-webhook',          'delete', 'api',    '/spaces/{space_id}/webhook_definitions/{webhook_id}',                 ''),
    Endpoint('list-webhooks',           'get',    'api',    '/spaces/{space_id}/webhook_definitions',                              ''),
    Endpoint('list-webhook-calls',      'get',    'api',    '/spaces/{space_id}/webhooks/{webhook_id}/calls',                      ''),
    Endpoint('get-webhook-call',        'get',    'api',    '/spaces/{space_id}/webhooks/{webhook_id}/calls/{call_id}',            ''),
    Endpoint('get-webhook-health',      'get',    'api',    '/spaces/{space_id}/webhooks/{webhook_id}/health',                     '')
]


def optionify(s):
    return '--' + s.replace('_', '-')


def extract_template_field_names(template):
    return [
        field_name
        for (fragment, field_name, format_spec, conversion)
        in string.Formatter().parse(template)
        if field_name is not None
    ]


def construct_endpoint(endpoint_spec):
    return ContentfulEndpoint(
        name=endpoint_spec.name,
        method=endpoint_spec.method,
        subdomain=endpoint_spec.subdomain,
        template=endpoint_spec.template,
        is_collection='c' in endpoint_spec.flags,
        sends_document='D' in endpoint_spec.flags,
        allows_version='v' in endpoint_spec.flags,
        requires_version='V' in endpoint_spec.flags,
        requires_content_type='t' in endpoint_spec.flags,
        is_entry_collection='e' in endpoint_spec.flags,
        is_asset_collection='a' in endpoint_spec.flags,
        allows_organization='o' in endpoint_spec.flags,
        is_dangerous='!' in endpoint_spec.flags,
        sends_binary='B' in endpoint_spec.flags
    )


# Singleton value to denote that the user specified --default-organization
# on the command-line and that we should not pass X-Contentful-Organization.
# This is preferred over making it optional, since we don't think it's a good
# default - the user should actively choose this if they really mean it.
DEFAULT_ORGANIZATION = object()

class FakeResponse:
    text = ''
    url = ''
    status_code = 0

class ContentfulEndpoint:
    def __init__(self,
                 name,
                 method,
                 subdomain,
                 template,
                 is_collection,
                 sends_document,
                 allows_version,
                 requires_version,
                 requires_content_type,
                 is_entry_collection,
                 is_asset_collection,
                 allows_organization,
                 is_dangerous,
                 sends_binary):
        self.name = name
        self.method = method
        self.subdomain = subdomain
        self.template = template
        self.is_collection = is_collection
        self.sends_document = sends_document
        self.allows_version = allows_version
        self.requires_version = requires_version
        self.requires_content_type = requires_content_type
        self.is_entry_collection = is_entry_collection
        self.is_asset_collection = is_asset_collection
        self.allows_organization = allows_organization
        self.is_dangerous = is_dangerous
        self.sends_binary = sends_binary

    def build_command(self):
        parameters = []
        for field_name in extract_template_field_names(self.template):
            option_name = optionify(field_name)
            parameters.append(click.Option([option_name], required=True))
        if self.allows_version:
            parameters.append(click.Option(['--document-version'], type=int))
        if self.requires_version:
            parameters.append(click.Option(['--document-version'], type=int, required=True))
        if self.sends_document:
            parameters.append(click.Option(['--document-file'], type=click.Path(exists=True)))
            parameters.append(click.Option(['--document-body']))
        if self.sends_binary:
            parameters.append(click.Option(['--document-file'], type=click.Path(exists=True)))
            parameters.append(click.Option(['--document-body']))
        if self.requires_content_type:
            parameters.append(click.Option(['--content-type']))
        if self.is_collection:
            parameters.append(click.Option(['--skip']))
            parameters.append(click.Option(['--limit']))
        if self.is_entry_collection:
            parameters.append(click.Option(['--select']))
            parameters.append(click.Option(['--order']))
            parameters.append(click.Option(['--content-type']))
            parameters.append(click.Argument(['query-term'], nargs=-1))
        if self.is_asset_collection:
            parameters.append(click.Option(['--select']))
            parameters.append(click.Option(['--order']))
            parameters.append(click.Option(['--mimetype-group']))
        if self.allows_organization:
            parameters.append(click.Option(['--default-organization', 'organization'], flag_value=DEFAULT_ORGANIZATION))
            parameters.append(click.Option(['--organization', 'organization'], required=True))
        if self.is_dangerous:
            parameters.append(click.Option(['--force/--no-force']))

        parameters.append(click.Option(['--prepare-stream/--no-prepare-stream']))
        parameters.append(click.Option(['--oauth-token'], envvar='CONTENTFUL_OAUTH_TOKEN', required=True))
        parameters.append(click.Option(['--gateway-api-key'], envvar='CONTENTFUL_GATEWAY_API_KEY', default=None))
        parameters.append(click.Option(['--output-file'], type=click.File('wt'), default=sys.stdout))
        parameters.append(click.Option(['--echo-log/--no-echo-log'], default=False))
        command = click.Command(self.name, params=parameters, callback=click.pass_context(self.invoke_as_click_command))
        return command

    def prepare_arguments_for_output(self, **arguments):
        arguments_copy = dict(arguments)
        arguments_copy.pop('prepare_stream', None)
        arguments_copy.pop('oauth_token', None)
        arguments_copy.pop('echo_log', None)
        arguments_copy.pop('output_file', None)
        if arguments_copy.get('document_file') is not None:
            arguments_copy['document_file'] = os.path.abspath(arguments_copy['document_file'])
        return arguments_copy

    def log_operation_result(
            self, response=None, exception=None, arguments={}, echo_to_stdout=False, log_file=sys.stdout, attempt=0, retrying=False):
        log_entry = OrderedDict()
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        log_entry['timestamp'] = timestamp
        log_entry['operation'] = self.name
        log_entry['arguments'] = self.prepare_arguments_for_output(**arguments)
        if response is not None:
            json_response = convert_response_to_json(response)
            log_entry['url'] = json_response['url']
            log_entry['status_code'] = json_response['status_code']
            log_entry['body'] = json_response['body']
        else:
            log_entry['url'] = None
            log_entry['status_code'] = None
            log_entry['body'] = None
        if exception is not None:
            log_entry['exception'] = repr(exception)
        else:
            log_entry['exception'] = None

        log_entry['attempt'] = attempt
        log_entry['retrying'] = retrying
        echo_output(log_entry, echo_to_stdout, log_file)

    def invoke_as_click_command(self, ctx, **arguments):
        arguments = dict(arguments)

        if self.sends_document or self.sends_binary:
            if arguments['document_body'] is not None and arguments['document_file'] is not None:
                raise click.UsageError('Specify --document-body or --document-file')
            if arguments['document_body'] is None and arguments['document_file'] is None:
                raise click.UsageError('Specify --document-body or --document-file')

        if self.is_dangerous and not arguments['force']:
            click.confirm('{}: Are you sure?'.format(self.name), err=True, abort=True)

        if arguments['prepare_stream']:
            echo_output(
                {'operation': self.name, 'arguments': self.prepare_arguments_for_output(**arguments)},
                echo_to_stdout=arguments['echo_log'],
                log_file=arguments['output_file'])
            return

        response = self.invoke(arguments, requests.Session(), arguments['oauth_token'], arguments['gateway_api_key'])
        self.log_operation_result(
            response=response,
            arguments=arguments,
            echo_to_stdout=arguments['echo_log'],
            log_file=arguments['output_file'],
            attempt=0,
            retrying=False)
        if not (200 <= response.status_code < 300):
            ctx.exit(2)

    def invoke_streaming(self, ctx, arguments, session, oauth_token, gateway_api_key, echo_to_stdout, log_file, run=True):
        max_attempts = 4

        try:
            if self.is_dangerous:
                raise Exception('Operation not supported in streaming mode')

            for attempt in range(max_attempts):
                response = self.invoke(arguments, session, oauth_token, gateway_api_key, run)

                retrying_allowed_for_status_code = response.status_code in [429, 500]
                last_attempt = attempt == max_attempts - 1
                should_retry = (
                    retrying_allowed_for_status_code and
                    not last_attempt)

                self.log_operation_result(
                    response=response,
                    arguments=arguments,
                    echo_to_stdout=echo_to_stdout,
                    log_file=log_file,
                    attempt=attempt,
                    retrying=should_retry)

                if not should_retry:
                    break

                time.sleep(5 * 2 ** attempt) # 5s, 10s, 20s, ...
        except Exception as e:
            self.log_operation_result(
                exception=e, arguments=arguments, echo_to_stdout=echo_to_stdout, log_file=log_file, attempt=attempt, retrying=False)

    def load_document_as_binary(self, arguments):
        if arguments.get('document_file') is not None:
            with open(arguments.get('document_file'), 'rb') as f:
                return f.read()

        if arguments.get('document_body') is not None:
            if isinstance(arguments['document_body'], dict):
                return json.dumps(arguments['document_body']).encode('utf-8')
            return arguments.get('document_body').encode('utf-8')

        raise KeyError('Could not find document_file or document_body in arguments')

    @staticmethod
    def construct_config():
        config_path = str(Path.home()) + '/.config/skyscanner-contentful-management'

        # Default configuation definitions
        config = configparser.ConfigParser()
        config['base_url'] = {}
        config['base_url']['api'] = 'https://api.contentful.com'
        config['base_url']['upload'] = 'https://upload.contentful.com'

        # Override config using external file
        if os.path.isfile(config_path):
            with open(config_path) as f:
                config.read_file(f)

        return config

    def construct_base_url(self):
        config = self.construct_config()

        if self.subdomain in config['base_url']:
            return config['base_url'][self.subdomain]
        raise Exception('No suitable contentful-api-gateway endpoint for Contentful subdomain {}'.format(self.subdomain))

    def invoke(self, arguments, session, oauth_token, gateway_api_key, run=True):
        expanded_path = self.template.format(**arguments)
        url = '{base_url}{expanded_path}'.format(
            base_url=self.construct_base_url(),
            expanded_path=expanded_path)
        headers = {
            'Authorization': 'Bearer {}'.format(oauth_token),  # Contentful
        }

        if gateway_api_key is not None:
            headers['apikey'] = gateway_api_key  # API Gateway

        params = OrderedDict()
        if self.sends_document:
            data = self.load_document_as_binary(arguments)
            headers['Content-Type'] = 'application/vnd.contentful.management.v1+json'
        elif self.sends_binary:
            data = self.load_document_as_binary(arguments)
            headers['Content-Type'] = 'application/octet-stream'
        else:
            data = None
        if self.is_collection:
            if 'skip' in arguments:
                params['skip'] = arguments['skip']
            if 'select' in arguments:
                params['select'] = arguments['select']
            if 'limit' in arguments:
                params['limit'] = arguments['limit']
        if self.is_entry_collection:
            for argname in ['select', 'order', 'content_type']:
                if argname in arguments:
                    params[argname] = arguments[argname]
            for query_term in arguments['query_term']:
                fragments = query_term.split('=', 1)
                key = fragments[0]
                if len(fragments) == 1:
                    value = ''
                else:
                    value = fragments[1]
                params[key] = value
        if (self.allows_version or self.requires_version) and ('document_version' in arguments):
            headers['X-Contentful-Version'] = str(arguments['document_version'])
        if self.requires_content_type:
            headers['X-Contentful-Content-Type'] = arguments['content_type']
        if self.allows_organization and arguments['organization'] is not DEFAULT_ORGANIZATION:
            headers['X-Contentful-Organization'] = arguments['organization']

        if run:
            response = session.request(self.method, url, data=data, headers=headers, params=params)
        else:
            # Halt and package what would have been sent over the wire as a fake response
            response = FakeResponse()
            response.url = url
            response.status_code = 000
            response.text = json.dumps({
                'method': self.method,
                'data': data,
                'headers': headers,
                'params': params
            })

        return response


@click.group()
@click.pass_context
def cli(ctx):
    pass


for endpoint_spec in CONTENTFUL_ENDPOINTS:
    cli.add_command(construct_endpoint(endpoint_spec).build_command())


@cli.command('stream')
@click.option('--oauth-token', envvar='CONTENTFUL_OAUTH_TOKEN')
@click.option('--gateway-api-key', envvar='CONTENTFUL_GATEWAY_API_KEY', default=None)
@click.option('--output-file', type=click.File('wt'), default=sys.stdout)
@click.option('--echo-log/--no-echo-log', default=False)
@click.option('--run/--dry-run', default=False)
@click.argument('stream-file', type=click.File('r'))
@click.pass_context
def stream(ctx, stream_file, oauth_token, gateway_api_key, output_file, echo_log, run):
    session = requests.Session()

    for line in stream_file:
        try:
            command_obj = json.loads(line)
            command_name = command_obj.get('operation')
            for endpoint_spec in CONTENTFUL_ENDPOINTS:
                if endpoint_spec.name == command_name:
                    construct_endpoint(endpoint_spec).invoke_streaming(
                        ctx, command_obj.get('arguments', {}), session, oauth_token, gateway_api_key, echo_log, output_file, run)
                    break
            else:
                echo_output({'error': 'Operation not recognized', 'operation': command_name}, echo_log, output_file)
        except Exception as e:
            echo_output({'exception': repr(e)}, echo_log, output_file)


if __name__ == '__main__':
    cli(obj={})
