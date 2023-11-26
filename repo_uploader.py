import argparse
import fnmatch
import os
from pathlib import Path

from dvuploader import DVUploader, File
import requests

DATASET_ENDPOINT = "{URL}/api/datasets/:persistentId/?persistentId={PID}"
USAGE = """

Dataverse Repository Uploader

This script can be used to upload and sync the content of a given GitHub/Lab repository
to a Dataverse installation. Used in an action, the script is capable of tracking changes
within a repository and applies them accordingly to a Dataverse dataset og choice.

--Installation--

UNIX

python3 -m pip install -r ./requirements.txt

WIN

python -m pip install -r ./requirements.txt

--Usage--

python repo_uploader.py \\
    --dataverse-url https://demo.dataverse.org \\
    --persistent-id doi:10.5072/FK2/ABC123 \\
    --api-token <API_TOKEN> 

"""


def _get_dv_version(dv_url: str) -> str:
    """
    Get the version of the Dataverse instance.

    Returns:
        str: The version of the Dataverse instance.
    """
    url = f"{dv_url.rstrip('/')}/api/info/version"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()["data"]["version"]


def _to_file_object(path: str, subdir: str) -> File:
    """
    Convert a list of file paths to a list of File objects.

    Args:
        paths (list[str]): A list of file paths.

    Returns:
        List[File]: A list of File objects.
    """

    return File(
        filepath=path,
        directoryLabel=(os.path.join(subdir, os.path.dirname(path))),
    )


def _get_repo_paths() -> list[str]:
    """
    Get a list of file paths in the current directory, excluding ignored files and the .git directory.

    Returns:
        List[str]: A list of file paths.
    """
    filenames = [str(f) for f in Path(".").rglob("*") if f.is_file()]

    if os.path.exists(".gitignore"):
        # Filter out the files
        # repo = git.Repo(".", search_parent_directories=True)
        # ignored = repo.ignored(filenames)  # type: ignore
        # repo.close()
        ignored = []
    else:
        ignored = []

    return [f for f in filenames if not f in ignored and not f.startswith(".")]


def _write_dvregistry(file_paths: list[str]) -> None:
    """
    Write the .dvregistry file.

    Args:
        file_paths (list[str]): A list of file paths.
    """
    with open(".dvregistry", "w") as f:
        for file_path in file_paths:
            f.write(f"{file_path}\n")


def _get_dataset_registry(
    file_list: list[str],
    API_TOKEN: str,
    DV_URL: str,
):
    dvregistry_obj = list(filter(lambda f: f["label"] == ".dvregistry", file_list))  # type: ignore

    if len(dvregistry_obj) > 0:
        file_id = dvregistry_obj[0]["dataFile"]["id"]  # type: ignore

        # Fetch the dataset .dvregistry file
        url = f"{DV_URL}/api/access/datafile/{file_id}"
        headers = {"X-Dataverse-key": API_TOKEN}
        response = requests.get(headers=headers, url=url)
        response.raise_for_status()
        return response.text.split("\n")

    return []


def _get_file_list(
    dataverse_url: str,
    persistent_id: str,
    api_token: str,
) -> list[str]:
    """
    Get a list of files in the dataset.

    Returns:
        List[str]: A list of file paths.
    """

    if dataverse_url.endswith("/"):
        dataverse_url = dataverse_url[:-1]

    url = DATASET_ENDPOINT.format(URL=dataverse_url, PID=persistent_id)
    headers = {"X-Dataverse-key": api_token}
    response = requests.get(headers=headers, url=url)
    response.raise_for_status()
    return response.json()["data"]["latestVersion"]["files"]


def _remove_unused_files(dataset_files: list[str], repo_files: list[str]) -> None:
    """
    Remove unused files from the dataset.

    Args:
        dataset_files (list[str]): List of files in the dataset.
        repo_files (list[str]): List of files in the repository.

    Returns:
        None
    """
    for file in dataset_files:
        # Combine the directory label and the file name
        file_path = os.path.join(file.get("directoryLabel", ""), file["label"])  # type: ignore

        if not any(repo_file in file_path for repo_file in repo_files):
            file_id = file["dataFile"]["id"]  # type: ignore

            print(
                f"├── File '{file_path}' is not present in the repository anymore - Deleting."
            )

            if not dv_version.startswith("5.12"):
                headers = {"X-Dataverse-key": API_TOKEN}
                url = f"{DV_URL.rstrip('/')}/api/files/{file_id}"
                response = requests.delete(headers=headers, url=url)
                response.raise_for_status()

                print(f"├── File '{file_path}' deleted.")


def _filter_paths(paths: list[str]) -> list[str]:
    """
    Filter out the .git directory and the .dvregistry file.

    Args:
        paths (list[str]): A list of file paths.

    Returns:
        List[str]: A list of file paths.
    """

    gitignore = Path(".gitignore").read_text().splitlines()
    gitignore = [line for line in gitignore if not line.startswith("#")]

    to_keep = []
    for file in Path(".").rglob("*"):
        if not any(fnmatch.fnmatch(str(file), pattern) for pattern in gitignore):
            to_keep.append(file)

    return to_keep


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(usage=USAGE)
    argparser.add_argument(
        "--dataverse-url",
        required=True,
        help="The base URL of the Dataverse repository.",
    )
    argparser.add_argument(
        "--persistent-id",
        required=True,
        help="The persistent identifier (PID) of the dataset.",
    )
    argparser.add_argument(
        "--api-token",
        required=True,
        help="The API token for authentication.",
    )
    argparser.add_argument(
        "--directory",
        required=False,
        default="",
        help="The directory to upload to.",
    )

    args = argparser.parse_args()

    DV_URL = args.dataverse_url
    PID = args.persistent_id
    API_TOKEN = args.api_token
    SUBDIR = args.directory

    # Get the Dataverse version
    dv_version = _get_dv_version(dv_url=DV_URL)

    # Write the .dvregistry file
    repo_files = _get_repo_paths()

    if os.path.exists(".gitignore"):
        # Filter out the files that are ignored
        repo_files = _filter_paths(repo_files)

    _write_dvregistry(repo_files)

    # Get registry of files in the dataset
    dataset_files = _get_file_list(
        dataverse_url=DV_URL,
        persistent_id=PID,
        api_token=API_TOKEN,
    )

    # Get the dataset .dvregistry file to check if there are files that
    # are not present in the repository anymore.
    _get_dataset_registry(
        file_list=dataset_files,
        API_TOKEN=API_TOKEN,
        DV_URL=DV_URL,
    )

    # Remove files that are not present in the repository anymore
    _remove_unused_files(
        dataset_files=dataset_files,
        repo_files=repo_files,
    )

    # Compile all files to upload
    files = [_to_file_object(file, SUBDIR) for file in repo_files + [".dvregistry"]]

    dvuploader = DVUploader(files=files)
    dvuploader.upload(
        api_token=API_TOKEN,
        dataverse_url=DV_URL,
        persistent_id=PID,
    )
