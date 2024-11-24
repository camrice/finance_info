# Finance Data Script

## Setup

### FRED API

Obtain an API key from the FRED API by signing up [here](https://fred.stlouisfed.org).

### Google App Password

For the email function to work, you need to create an app password for Google. Follow instructions [here](https://support.google.com/accounts/answer/185833?hl=en).

### .env File

This script relies on environment variables. These I have stored in a `.env` file.

```Bash
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=password
FRED_API_KEY=FRED API Key
EMAIL_LIST=["email1@gmail.com", "email2@gmail.com"]
```

Some notes:

* `EMAIL_USER` is the from address and the email that has the Google app password
* `EMAIL_PASS` is the Google App password
* `FRED_API_KEY` your API key
* `EMAIL_LIST` is the list of destination emails

### Python Environment and Running

Recommended to create an environment to install dependecies and run. For example `venv`:

```Bash
# Create environment
python3 -m venv myenv

# Activate
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python finance_info.py
```

## Cronjob

To schedule the script to run locally, use a `cronjob` like below. Note that the path to the Python binary should be the one from the environment.

```Bash
# Edit cronjobs
crontab -e

# This example cronjob runs the script at 8AM PST Monday through Friday
0 8 * * 1-5 TZ="America/Los_Angeles" /path/to/finance_info/myenv/bin/python /path/to/finance_info/finance_info.py
```
