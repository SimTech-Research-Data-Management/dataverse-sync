import os
import requests
import hashlib

from pathlib import Path

# Retrieve environment variables
API_TOKEN = os.environ["DV_API_TOKEN"]
DV_URL = os.environ["DV_URL"]
PID = os.environ["DV_PID"]


if __name__ == "__main__":
    # Fetch files from the dataset
    ENDPOINT = f"{DV_URL.rstrip('/')}/api/datasets/:persistentId/?persistentId={PID}"
    response = requests.get(ENDPOINT, headers={"X-Dataverse-key": API_TOKEN})
    response.raise_for_status()
    files = response.json()["data"]["latestVersion"]["files"]

    # Convert files to paths and their MD5 checksums
    ds_files = [
        (
            os.path.join(file.get("directoryLabel", ""), file["label"]),
            file["dataFile"]["md5"],
        )
        for file in files
        if file["label"] != ".dvregistry"
    ]

    # Do the same for the repository files
    repo_files = {
        str(path): hashlib.md5(path.read_bytes()).hexdigest()
        for path in Path(".").rglob("*")
        if path.is_file() and not str(path).startswith(".")
    }

    assert len(ds_files) == len(repo_files), (
        f"Length mismatch: {len(ds_files)} != {len(repo_files)}"
    )

    for ds_name, ds_hash in ds_files:
        assert ds_name in repo_files, f"File not found: {ds_name}"

        r_hash = repo_files[ds_name]

        assert ds_hash == r_hash, f"Hash mismatch: {ds_hash} != {r_hash}"

    print("🎉 Tests were successful!")
