# gitapp_alert_on_public

A service for finding newly created public repositories for GitHub users who are part of an organization.

## Prepare Things

1. Create (or install) a GitHub application. Download the private PEM file needed for JWT token creations.
2. Update the [config.json](config-sample.json) file (see sample file) with the PEM file location and installation ID.
3. For a single instance on a single organization, add to the config file the GitHub organization and a relevant slack webhook to get the notifications.
4. _Optional_ add a mongodb information for storing notifications.

## Develop

```Shell
pip install -r requirements.txt
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