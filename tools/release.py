import sys
import os

from github import Github, GithubException

from tf.core.helpers import console


def makeRelease(org, repo, tag, name, msg, silent=True):
    ghPerson = os.environ.get("GHPERS", None)
    if ghPerson:
        ghConn = Github(ghPerson)
    rate = ghConn.get_rate_limit().core
    if not silent:
        console(
            f"rate limit is {rate.limit} requests per hour,"
            f" with {rate.remaining} left for this hour"
        )
        if rate.limit < 100:
            console(
                "To increase the rate,"
                "see https://annotation.github.io/text-fabric/Api/Repo/"
            )

    try:
        if not silent:
            console(
                f"\tconnecting to online GitHub repo {org}/{repo} ... ", newline=False,
            )
        repoOnline = ghConn.get_repo(f"{org}/{repo}")
        if not silent:
            console("connected")
    except GithubException as why:
        console("failed", error=True)
        console(f"GitHub says: {why}", error=True)
    except IOError:
        console("no internet", error=True)

    if not repoOnline:
        return 1

    try:
        repoOnline.create_git_release(tag, name, msg)
        result = 0
    except GithubException:
        console("failed", error=True)
        console("GitHub says: {why}", error=True)
        result = 1
    except IOError:
        console("no internet", error=True)
        result = 1
    if result == 0:
        if not silent:
            console(f"{org}/{repo} @ {tag} ({name}: {msg})")
        else:
            console("done")
    return result


if __name__ == "__main__":
    exit(makeRelease(*sys.argv[1:]))