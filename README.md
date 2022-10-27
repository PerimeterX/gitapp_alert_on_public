# Alert on Public Repos

[![GitHub issues](https://img.shields.io/github/issues/PerimeterX/gitapp_alert_on_public)](https://github.com/PerimeterX/gitapp_alert_on_public/issues)
[![GitHub forks](https://img.shields.io/github/forks/PerimeterX/gitapp_alert_on_public)](https://github.com/PerimeterX/gitapp_alert_on_public/network)
[![GitHub stars](https://img.shields.io/github/stars/PerimeterX/gitapp_alert_on_public)](https://github.com/PerimeterX/gitapp_alert_on_public/stargazers)
[![Latest Release](https://img.shields.io/github/v/release/perimeterx/gitapp_alert_on_public)](https://github.com/PerimeterX/gitapp_alert_on_public/releases)
[![GitHub license](https://img.shields.io/github/license/PerimeterX/gitapp_alert_on_public)](https://github.com/PerimeterX/gitapp_alert_on_public/blob/main/LICENSE)
![Top Languages](https://img.shields.io/github/languages/top/perimeterx/gitapp_alert_on_public)

A github application for finding and alerting on newly created public repositories for GitHub users who are part of a GitHub organization.

## Prepare Things

1. Create and install a GitHub application to your organization.
    1. The GitHub application requires only one permission: _Organization permissions > Members (Read-Only)_.
    2. Download the private PEM file needed for JWT token creations.
2. Update the [config.json](config-sample.json) file (see sample file) with the PEM file location and installation ID.
3. For a single instance on a single organization, add to [config.json](config-sample.json) the GitHub organization and a slack webhook for notifications.
    1. Create a new slack app
    2. Goto _Incoming Webhooks_ and create a new hook
4. _Optional_ add a mongodb parameters for storing notifications.
5. run
```Shell
pip install -r requirements.txt
```

### Config File

```JSON
{
    "key_file": "./conf/private-key.pem",
    "github_app_id": "1111111",
    "installs": [
        {
            "org": "ORG_NAME",
            "slack_web_hook": "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXX/XXXXXXXXXX"
        }],
    "use_mongo": false,
    "mongodb_conn": "mongodb://.......", // relevant only if use_mongo is true, can be removed otherwise
    "mongodb_db": "DB name" // relevant only if use_mongo is true, can be removed otherwise
}
```

## Test

The following command will run a single scan and stop

```Shell
python main.py once
```

## Run

The following command will run forever, scanning repos immediatly, followed by a scan every 30 minutes.

```Shell
python main.py
```

### Docker Usage

```Shell
docker build --tag gitapp .
docker run -d gitapp
```
