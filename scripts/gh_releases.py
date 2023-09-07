from github import Github

# Authentication is defined via github.Auth
from github import Auth

# using an access token
auth = Auth.Token("Personal access tokens (classic)")

# First create a Github instance:

# Public Web Github
g = Github(auth=auth)

repo = g.get_repo("makslevental/wheels")
release = repo.get_release(113028511)
assets = release.get_assets()
for ass in assets:
    if "18.0.0.20230907" in ass.name:
        print(ass.name)
        assert ass.delete_asset()


repo = g.get_repo("makslevental/mlir-wheels")
release = repo.get_release(111725799)
assets = release.get_assets()
for ass in assets:
    if "18.0.0.20230907" in ass.name:
        print(ass.name)
        assert ass.delete_asset()
