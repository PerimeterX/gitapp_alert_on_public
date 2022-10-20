# gitapp_alert_on_public

A service for finding newly created public repositories for GitHub users who are part of a GitHub organization.

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