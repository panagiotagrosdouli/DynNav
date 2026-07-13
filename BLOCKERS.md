# DynNav Blockers

Only genuine environmental or optional-integration blockers belong in this file. Software defects belong in `AUDIT.md` and must not be hidden here.

## Required verification environment

### Command runner cannot resolve GitHub

**Status:** Active environmental blocker

A clean-clone attempt failed before checkout with:

```text
fatal: unable to access 'https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git/':
Could not resolve host: github.com
```

This prevents truthful execution of the required fresh-checkout protocol in the current command runner. Repository files remain accessible through the connected GitHub integration, which is being used for inspection and branch updates, but that integration is not an executable filesystem checkout.

**Resolution:** run the verification workflow on GitHub Actions or another network-enabled Linux runner with Python, Node, npm, Docker, and Git available.

## Optional integrations

The following are optional until their runtimes are available and must remain clearly labelled rather than treated as core failures:

- ROS 2
- Nav2
- Gazebo
- physical-robot hardware
- optional MP4 codecs when a verified GIF fallback is generated

No optional integration is represented as validated merely because documentation or scaffolding exists.
