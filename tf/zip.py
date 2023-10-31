from .advanced.app import loadApp
from .core.timestamp import DEEP
from .core.helpers import console


def main():
    """Makes a complete zip file.

    Determines the repository that contains the current directory.
    Finds the TF dataset of that repository.

    Then zips its TF data (most recent version) plus all related data modules,
    not only other TF data, but also images that are included.

    Puts the TF data somewhere in your Downloads directory,
    from where you can attach it to a release on GitHub or GitLab.

    TF is instructed to try that file first
    if a user of this dataset needs to download the latest data.
    """
    console("loading TF app ...")
    app = loadApp(silent=DEEP)
    app.zipAll()


if __name__ == "__main__":
    main()
