# skyscanner-contentful-management
[![Build Status](https://travis-ci.org/Skyscanner/skyscanner-contentful-management.svg?branch=master)](https://travis-ci.org/Skyscanner/skyscanner-contentful-management)

## Installation
This is published as a PyPi package and can be installed with pip.

`$ pip install skyscanner-contentful-management`

## Configuration
By default, requests are made directly against Contentful's API endpoints. You might desire different behaviour if you internally use an API proxy to track requests.

If it exists, `~/.config/skyscanner-contentful-management` is used to define override API endpoints. The effective default configuration is defined by the following configuration file.

```ini
[base_url]
api=https://api.contentful.com
upload=https://upload.contentful.com
```

## Authentication
This tool requires a Contentful API key (passed through the `CONTENTFUL_OAUTH_TOKEN` environment variable or the `--oauth-token` argument). This can be obtained by generating a Personal Access Token inside a space's API configuration or by authorising with an OAuth application.

Additionally, this tool can pass an API proxy key if you're not directly connecting to Contentful. This is passed to the server as the `apikey` header and is defined using the `CONTENTFUL_GATEWAY_API_KEY` environment variable or the `--gateway-api-key` argument.

## Commands
The tool takes an endpoint and any associated parameters as input.

| command | arguments | flags |
| -------- | -------- | -------- |
| list-content-types | space_id | c |
| put-content-type | space_id, content_type_id | Dv |
| get-content-type | space_id, content_type_id |  |
| put-content-type-editor | space_id, content_type_id | DV |
| get-content-type-editor | space_id, content_type_id |  |
| delete-content-type | space_id, content_type_id | V |
| publish-content-type | space_id, content_type_id | V |
| unpublish-content-type | space_id, content_type_id |  |
| list-entries | space_id | ce |
| post-entry | space_id | Dt |
| put-entry | space_id, entry_id | Dtv |
| get-entry | space_id, entry_id |  |
| delete-entry | space_id, entry_id | V |
| publish-entry | space_id, entry_id | V |
| unpublish-entry | space_id, entry_id | V |
| archive-entry | space_id, entry_id | V |
| unarchive-entry | space_id, entry_id | V |
| list-assets | space_id | ca |
| post-asset | space_id | D |
| put-asset | space_id, asset_id | Dv |
| get-asset | space_id, asset_id |  |
| delete-asset | space_id, asset_id | V |
| process-asset | space_id, asset_id, locale | V |
| publish-asset | space_id, asset_id | V |
| unpublish-asset | space_id, asset_id | V |
| archive-asset | space_id, asset_id | V |
| unarchive-asset | space_id, asset_id | V |
| get-locales | space_id |  |
| list-spaces |  |  |
| post-space |  | oD |
| put-space | space_id | oD |
| get-space | space_id |  |
| delete-space | space_id | ! |
| post-upload | space_id | B |
| get-upload | space_id, upload_id |  |
| delete-upload | space_id, upload_id |  |
| post-webhook | space_id | D |
| put-webhook | space_id, webhook_id | D |
| get-webhook | space_id, webhook_id |  |
| delete-webhook | space_id, webhook_id |  |
| list-webhooks | space_id |  |
| list-webhook-calls | space_id, webhook_id |  |
| get-webhook-call | space_id, webhook_id, call_id |  |
| get-webhook-health | space_id, webhook_id |  |

### Flags
Flags determine what type of data should be sent to Contentful accompanying the request (document, version number, content type, etc.)

| flag | name | options | arguments |
| -----| ---- | ------- | --------- |
| c | is_collection | --skip / --limit | n/a |
| D | sends_document | --document-file or --document-body | n/a |
| v | allows_version | --document-version | n/a |
| V | requires_version | --document-version | n/a |
| t | requires_content_type | --content-type |  n/a |
| e | is_entry_collection | --select / --order / --content-type | query term |
| a | is_asset_collection | --select / --order / --mimetype-group | n/a |
| o | allows_organization | --organization | n/a |
| ! | is_dangerous | --force or --no-force | n/a |
| B | sends_binary | --document-file or --document-body | n/a |


## Usage Examples
These examples aim to cover a variety of different commands to explain how arguments and flags are used together. It doesn't intend to document every supported command or argument combination.

You should consider the [Content Management API](https://www.contentful.com/developers/docs/references/content-management-api/) documentation to be the ultimate source of truth regarding what information Contentful are expecting.

Every command returns a JSON object to stdout, which encapsulates the unmodified JSON response from Contentful inside the body attribute.

```javascript
{
  "timestamp": "2017-10-23T10:58:29.428887+00:00",
  "operation": "get-locales",
  "arguments": {
    "space_id": "samplespace1"
  },
  "url": "https://api.contentful.com/spaces/samplespace1/locales",
  "status_code": 200,
  "body": {
    "total": 1,
    "limit": 100,
    "skip": 0,
    "sys": {
      "type": "Array"
    },
    "items": [
      { }
    ]
  },
  "exception": null,
  "attempt": 0,
  "retrying": false
}
```

### Listing Content Types
`$ skyscanner-contentful-management list-content-types --space-id samplespace1`

### Creating an entry
`$ skyscanner-contentful-management post-entry --space-id samplespace1 --content-type news --document-file myentry.json`

### Deleting a space
`$ skyscanner-contentful-management delete-space  --space-id samplespace1  --force`

## Command Streaming
A streaming command is provided for performing multiple operations in sequence within a single execution. This can be extremely useful for bulk tasks (uploading/deleting images, articles, etc.), even if they are on entirely different endpoints.

The `stream` command expects a [jsonl](http://jsonlines.org/) file containing each of the commands to be performed. It optionally supports specifying an output file (with `--output-file`) and whether errors should be logged (using the `--echo-log/--no-echo-log` switch). If an `--output-file` isn't defined, stdout is used instead.

`$ skyscanner-contentful-management stream archived_autumn_articles.jsonl --output-file archived_autumn_articles_log.jsonl --error-log`

Each object inside the input jsonl file should adhere to the following structure.

```json
{
  "operation": "list-content-types",
  "arguments": {
    "space_id": "samplespace1",
    "skip": null,
    "limit": null
  }
}
```

Each response follows the same format as documented in "Usage Examples". Each result is returned as its own jsonl object.

This can be useful for manually forcing retries (e.g. if a stream was run out of order) as response objects can be passed back to stream. When combined with [jq](https://stedolan.github.io/jq/), you can filter out unsuccessful replies and use these to determine which commands should be reattempted.

`$ jq "select(.status_code!=200) archived_autumn_articles_log.jsonl -c > archived_autumn_articles_retry.jsonl && skyscanner-contentful-management stream archived_autumn_articles_retry.jsonl`

### Stream Preparation
Instead of manually writing a JSON object for a command, you can pass the `--prepare-stream` argument and receive an object that would execute the supplied command.

```
$ python contentful/management.py list-entries --space-id samplespace1 --prepare-stream
{"operation": "list-entries", "arguments": {"space_id": "samplespace1", "query_term": [], "skip": null, "limit": null, "select": null, "order": null, "content_type": null}}
```
