import os
from github import Github


ghConnUnauth = Github()

ghClient = os.environ.get("GHCLIENT", None)
ghSecret = os.environ.get("GHSECRET", None)
ghConnAppToken = Github(client_id=ghClient, client_secret=ghSecret)

personalAccessToken = "xxx"
ghConnPersToken = Github(personalAccessToken)

for gh in (ghConnUnauth, ghConnAppToken, ghConnPersToken):
    rate = gh.get_rate_limit().core
    print(
        f"rate limit is {rate.limit} requests per hour,"
        f" with {rate.remaining} left for this hour"
    )
