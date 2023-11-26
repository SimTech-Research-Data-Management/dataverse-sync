# Dataverse Repository Sync

Are you looking for an easy way to work with Dataverse? If so, you might find this GitHub workflow helpful. It's basically a mini-git system that syncs your repository with your Dataverse dataset. Here's what it does:

- Pushes all your repository files to your dataset
- Detects any changes and updates your dataset files accordingly
- Removes any files from your dataset that are not in your repository
- Lets you push content to any directory within your dataset.

Hope that helps!

## Usage

```yaml
# Push to the root of the dataset
- name: Synchronize to DV
  uses: JR-1991/dataverse-sync@main
  with:
    dataverse_url: "https://demo.dataverse.org"
    api_token: ${ secrets.MY_API_TOKEN }
    persistent_id: "doi:10.5072/FK2/ABC123"

# Push to a specific sub directory
- name: Synchronize to DV
  uses: JR-1991/dataverse-sync@main
  with:
    dataverse_url: "https://demo.dataverse.org"
    api_token: ${ secrets.MY_API_TOKEN }
    persistent_id: "doi:10.5072/FK2/ABC123"
    directory: "some/sub/dir"
```

> [!CAUTION]
> It is highly recommended to store your `API_TOKEN` as a secret in your repository to prevent unauthorized users from accessing your datasets.

> [!TIP]
> Not sure what secrets are? Find information how to [add](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/managing-secrets-for-your-repository-and-organization-for-github-codespaces) and [use](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) secrets within actions.

## Inputs

## Complete workflow example

```yaml
name: Dataverse Sync

on: [push, release]

jobs:
  dv-sync:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Synchronize to DV
      uses: JR-1991/dataverse-sync@main
      with:
        dataverse_url: "Enter your Dataverse URL here"
        api_token: ${ secrets.DV_API_TOKEN }
        persistent_id: "Enter your dataset persistent ID here"
```