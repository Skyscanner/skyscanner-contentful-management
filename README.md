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
| list-content-types      | --space-id                         | Ec   |
| put-content-type        | --space-id --content-type-id       | EDv  |
| get-content-type        | --space-id --content-type-id       | E    |
| put-content-type-editor | --space-id --content-type-id       | EDV  |
| get-content-type-editor | --space-id --content-type-id       | E    |
| delete-content-type     | --space-id --content-type-id       | EV   |
| publish-content-type    | --space-id --content-type-id       | EV   |
| unpublish-content-type  | --space-id --content-type-id       | E    |
| list-entries            | --space-id                         | Ece  |
| post-entry              | --space-id                         | EDt  |
| put-entry               | --space-id --entry-id              | EDtv |
| get-entry               | --space-id --entry-id              | E    |
| delete-entry            | --space-id --entry-id              | EV   |
| publish-entry           | --space-id --entry-id              | EV   |
| unpublish-entry         | --space-id --entry-id              | EV   |
| archive-entry           | --space-id --entry-id              | EV   |
| unarchive-entry         | --space-id --entry-id              | EV   |
| list-assets             | --space-id                         | Eca  |
| post-asset              | --space-id                         | ED   |
| put-asset               | --space-id --asset-id              | EDv  |
| get-asset               | --space-id --asset-id              | E    |
| delete-asset            | --space-id --asset-id              | EV   |
| process-asset           | --space-id --asset-id --locale     | EV   |
| publish-asset           | --space-id --asset-id              | EV   |
| unpublish-asset         | --space-id --asset-id              | EV   |
| archive-asset           | --space-id --asset-id              | EV   |
| unarchive-asset         | --space-id --asset-id              | EV   |
| list-locales            | --space-id                         | Ec   |
| post-locale             | --space-id                         | ED   |
| put-locale              | --space-id --locale-id             | ED   |
| get-locale              | --space-id --locale-id             | E    |
| delete-locale           | --space-id --locale-id             | E    |
| list-space-memberships  | --space-id                         | Ec   |
| post-space-membership   | --space-id                         | ED   |
| put-space-membership    | --space-id --membership-id         | ED   |
| get-space-membership    | --space-id --membership-id         | E    |
| delete-space-membership | --space-id --membership-id         | E    |
| list-roles              | --space-id                         | Ec   |
| post-role               | --space-id                         | ED   |
| put-role                | --space-id --role-id               | ED   |
| get-role                | --space-id --role-id               | E    |
| delete-role             | --space-id --role-id               | E    |
| get-environment         | --space-id --environment-id        |      |
| put-environment         | --space-id --environment-id        | D    |
| delete-environment      | --space-id --environment-id        | !    |
| list-environments       | --space-id                         | c    |
| list-spaces             |                                    |      |
| post-space              |                                    | oD   |
| put-space               | --space-id                         | oD   |
| get-space               | --space-id                         |      |
| delete-space            | --space-id                         | !    |
| post-upload             | --space-id                         | B    |
| get-upload              | --space-id --upload-id             |      |
| delete-upload           | --space-id --upload-id             |      |
| post-webhook            | --space-id                         | D    |
| put-webhook             | --space-id --webhook-id            | D    |
| get-webhook             | --space-id --webhook-id            |      |
| delete-webhook          | --space-id --webhook-id            |      |
| list-webhooks           | --space-id                         |      |
| list-webhook-calls      | --space-id --webhook-id            |      |
| get-webhook-call        | --space-id --webhook-id --call-id  |      |
| get-webhook-health      | --space-id --webhook-id            |      |


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
| E | environment-aware | --environment-id | n/a |


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
