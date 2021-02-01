import errno
import os
import subprocess as sp
import sys
import time
import unicodedata


if sys.version_info[0] == 3:

    def enc(text):
        if isinstance(text, bytes):
            return text
        return text.encode()

    def dec(text):
        if isinstance(text, bytes):
            return text.decode("utf-8")
        return text

    def write(pipe, data):
        try:
            pipe.stdin.write(data)
        except OSError as e:
            if e.errno != errno.EPIPE:
                raise


else:

    def enc(text):
        if isinstance(text, unicode):  # noqa: F821
            return text.encode("utf-8")
        return text

    def dec(text):
        if isinstance(text, unicode):  # noqa: F821
            return text
        return text.decode("utf-8")

    def write(pipe, data):
        pipe.stdin.write(data)


def normalize_path(path):
    # Fix unicode pathnames on OS X
    # See: https://stackoverflow.com/a/5582439/44289
    if sys.platform == "darwin":
        return unicodedata.normalize("NFKC", dec(path))
    return path


def try_rebase(remote, branch):
    cmd = ["git", "rev-list", "--max-count=1", "{}/{}".format(remote, branch)]
    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    (rev, _) = p.communicate()
    if p.wait() != 0:
        return True
    cmd = ["git", "update-ref", "refs/heads/%s" % branch, dec(rev.strip())]
    if sp.call(cmd) != 0:
        return False
    return True


def get_config(key):
    p = sp.Popen(["git", "config", key], stdin=sp.PIPE, stdout=sp.PIPE)
    (value, _) = p.communicate()
    return value.decode("utf-8").strip()


def get_prev_commit(branch):
    cmd = ["git", "rev-list", "--max-count=1", branch, "--"]
    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    (rev, _) = p.communicate()
    if p.wait() != 0:
        return None
    return rev.decode("utf-8").strip()


def mk_when(timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())
    currtz = "%+05d" % (-1 * time.timezone / 36)  # / 3600 * 100
    return "{} {}".format(timestamp, currtz)


def start_commit(pipe, branch, message):
    uname = dec(get_config("user.name"))
    email = dec(get_config("user.email"))
    write(pipe, enc("commit refs/heads/%s\n" % branch))
    write(pipe, enc("committer {} <{}> {}\n".format(uname, email, mk_when())))
    write(pipe, enc("data %d\n%s\n" % (len(message), message)))
    head = get_prev_commit(branch)
    if head:
        write(pipe, enc("from %s\n" % head))
    write(pipe, enc("deleteall\n"))


def add_file(pipe, srcpath, tgtpath):
    with open(srcpath, "rb") as handle:
        if os.access(srcpath, os.X_OK):
            write(pipe, enc("M 100755 inline %s\n" % tgtpath))
        else:
            write(pipe, enc("M 100644 inline %s\n" % tgtpath))
        data = handle.read()
        write(pipe, enc("data %d\n" % len(data)))
        write(pipe, enc(data))
        write(pipe, enc("\n"))


def add_nojekyll(pipe):
    write(pipe, enc("M 100644 inline .nojekyll\n"))
    write(pipe, enc("data 0\n"))
    write(pipe, enc("\n"))


def gitpath(fname):
    norm = os.path.normpath(fname)
    return "/".join(norm.split(os.path.sep))


SRC = "site"
REMOTE = "origin"
BRANCH = "gh-pages"


def ghp_import():
    if not try_rebase(REMOTE, BRANCH):
        print("Failed to rebase %s branch.", BRANCH)

    cmd = ["git", "fast-import", "--date-format=raw", "--quiet"]
    kwargs = {"stdin": sp.PIPE}
    if sys.version_info >= (3, 2, 0):
        kwargs["universal_newlines"] = False
    pipe = sp.Popen(cmd, **kwargs)
    start_commit(pipe, BRANCH, "docs update")
    for path, _, fnames in os.walk(SRC):
        for fn in fnames:
            fpath = os.path.join(path, fn)
            fpath = normalize_path(fpath)
            gpath = gitpath(os.path.relpath(fpath, start=SRC))
            add_file(pipe, fpath, gpath)
    add_nojekyll(pipe)
    write(pipe, enc("\n"))
    pipe.stdin.close()
    if pipe.wait() != 0:
        sys.stdout.write(enc("Failed to process commit.\n"))

    # cmd = ["git", "push", REMOTE, BRANCH]
    # proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    # (out, err) = proc.communicate()
    # result = proc.wait() == 0

    # return result, dec(err)
    return (True, 0)


def gh_deploy():
    (result, error) = ghp_import()
    if not result:
        print("Failed to deploy to GitHub with error: \n%s", error)
        raise SystemExit(1)
    else:
        url = "https://annotation.github.io/text-fabric/tf"
        print("Your documentation should shortly be available at: " + url)


if __name__ == "__main__":
    gh_deploy()
