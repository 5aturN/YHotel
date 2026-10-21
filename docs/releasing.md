# Release process

## Branches

- `main` contains reviewed, releasable code.
- `develop` collects changes for the next release.
- `feature/<purpose>` branches start from `develop` and return there after review and automated checks pass.

## Version numbers

The project follows Semantic Versioning: `MAJOR.MINOR.PATCH`.

- Increase `MAJOR` for incompatible API changes.
- Increase `MINOR` for backward-compatible functionality.
- Increase `PATCH` for backward-compatible fixes.

Before a release, update `CHANGELOG.md`, run the test and security checks, and merge the verified release candidate into `main`. Create an annotated Git tag in the form `vMAJOR.MINOR.PATCH` on the released commit. Keep credentials and deployment secrets in the hosting environment, not in the repository.
