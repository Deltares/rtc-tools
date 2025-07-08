# Contributing to RTC-Tools 2

There are many ways you can contribute to RTC-Tools, such as:

- **Reporting issues**: If you encounter any bugs, errors, or unexpected behavior while using RTC-Tools, 
please report them on our [issue tracker](https://github.com/deltares/rtc-tools/issues).
Please follow the issue template and provide as much information as possible to help us reproduce and fix the issue.
- **Suggesting features**: If you have any ideas or suggestions for new features or improvements, 
please share them on our [issue tracker](https://github.com/deltares/rtc-tools/issues).
Please use the appropriate category and tag for your topic and explain your motivation and use case clearly.
- **Submitting pull requests**: If you want to contribute code or documentation to RTC-Tools, please  create a pull request. Before submitting, please follow the [Guidelines for creating merge requests](#guidelines-for-creating-merge-requests) below.  
- **Improving documentation**: If you find any errors, typos, or inconsistencies in the documentation,
 or if you want to add more examples, tutorials, or explanations, 
 please feel free to edit the documentation files in the docs folder and submit a merge request.
Please follow the [Sphinx syntax and style guide](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) for writing documentation.
- **Reviewing merge requests**: If you are familiar with RTC-Tools and want to help us maintain the quality and consistency of the code and documentation,
 please review the open merge requests and provide constructive feedback and suggestions.
- **Testing new releases**: If you want to help us test the new features and bug fixes before they are officially released, 
please install the latest development version of RTC-Tools from the [GitHub repository](https://github.com/deltares/rtc-tools)
 and report any issues or feedback on the [issue tracker](https://github.com/deltares/rtc-tools/issues).

## Guidelines for creating issues
1. **Title**: Provide a concise and informative title. The title should summarize the problem.
2. **Description**: Describe the issue in detail. Include steps to reproduce the issue, expected behavior, and actual behavior. Mention the version of RTC-Tools, Python and external packages you're using (CasADi, Pymoca, numpy), along with relevant details about your operating system.
4. **Minimal reproducible example**: Whenever possible, include a minimal reproducible example that demonstrates the issue. This should be the smallest amount of code and data necessary to reproduce the problem. Providing a minimal example helps maintainers quickly understand, reproduce, and address your issue.
3. **Labels**: Use labels to categorize the issue. This helps in prioritizing and resolving issues.

### Security Reporting

If you discover a security vulnerability, please report it responsibly by emailing [rtctools@deltares.nl](mailto:rtctools@deltares.nl) rather than opening a public issue.

## Guidelines for creating merge requests
1. **Identify or create an issue**: Before making any changes, open an issue following the [guidelines](#guidelines-for-creating-issues) above, or comment on an existing one in the [issue tracker](https://github.com/deltares/rtc-tools/issues) to discuss your ideas with the maintainers. This helps avoid duplication and ensures your contribution aligns with project goals.
2. **Fork or Branch**:
    - New Contributors: Fork the repository and create a new branch in your fork.
    - Contributors with : Create a new branch directly in the main repository.Use a descriptive branch name, such as `feature/short-description`, `bugfix/issue-123`, or `docs/update-readme`.
3. **Commit**: Make clear, focused commits following the [Commits and Commit Messages](#commits-and-commit-messages) guidelines.
4. **Write tests**: If possible, write tests that cover your changes and add them to the `tests` folder. This helps ensure your changes work as intended and prevent regressions.
5. **Documentation**: Update documentation and add examples to the `examples` folder if necessary.
6. **Create a pull request**: Reference the corresponding issue in your PR description. Clearly describe what changes you've made, why, and any relevant context.
7. **Check CI status**: Ensure all automated checks and tests pass before requesting a review.
8. **Request review**: Ask for a code review from your peers and address any comments or suggestions.

Try to keep pull requests small and focused for easier review and faster merging.

## Commits and Commit Messages

Each commit ideally satisfies the following:

- Each commit has a clear and single purpose.
- After each commit, all unit tests should still pass.

Commit messages should have the following structure:

```text
<scope>: <short description>

<complete description>
```

- scope: explains which part of the code is affected, e.g.:
    - optimization (only affects the optimization part)
    - homotopy_mixin (only affects the homotopy_mixin module)
    - tests (only affects the tests)
    - doc (only affects the documentation)
- short description: describes what is changed in the commit with a single sentence.
- complete description: explain in detail what is done in the commit and why.
    This can take up multiple paragraphs.


## Code Quality Guidelines

To maintain a high standard of code quality in RTC-Tools, please follow these guidelines when contributing:

- **Type Annotations**: Use [PEP 484](https://peps.python.org/pep-0484/) type hints where appropriate to improve code clarity and enable static analysis.
- **Docstrings**: Add clear and concise docstrings to all public modules, classes, functions, and methods. Use [PEP 257](https://peps.python.org/pep-0257/) conventions.
- **Pre-commit Hooks**: Use the provided pre-commit configuration by running `pre-commit install` to automatically check formatting and linting before each commit.
- **Follow PEP 8 and address SonarQube feedback**: Write Python code that adheres to [PEP 8](https://peps.python.org/pep-0008/) style guidelines. All code is analyzed by SonarQube for code quality and security issues—please review and address any issues or recommendations reported by SonarQube before submitting your pull request.
- **Çode coverage**: Ensure a code coverage of at least 80% to comply with SonarQube requirements.
- **Avoid Code Duplication**: Reuse existing utilities and functions where possible. Refactor code to eliminate duplication.
- **Readability**: Write code that is easy to read and understand. Use meaningful variable and function names.
- **Error Handling**: Handle exceptions gracefully and provide informative error messages.
- **Dependencies**: Only add new dependencies if necessary and discuss them with maintainers first.
- **Performance**: Consider the performance impact of your changes, especially in core computation routines.

By following these guidelines, you help ensure RTC-Tools remains robust, maintainable, and accessible

## Setting up a development environment

To set up your development environment, you will need:

- Python 3.9 or higher (up to 3.13)
- Git

You can clone the repository and install it from source:

```bash
git clone https://github.com/Deltares/RTC-Tools.git
cd RTC-Tools
uv sync
```

To ensure that your code meets our standards, we recommend using pre-commit.
Run the following command to set up the pre-commit hook:
```bash
pre-commit install
```
. This will
automatically check your code for formatting and linting issues before each
commit.


To run the tests:

```bash
pytest tests
```

To build the documentation:

```bash
cd doc
make html
```

## Version numbering and release cycle

For version numbers we use the guidelines described in <https://semver.org>:

> Given a version number MAJOR.MINOR.PATCH, increment the:
> 
> 1. MAJOR version when you make incompatible API changes
> 2. MINOR version when you add functionality in a backward compatible manner
> 3. PATCH version when you make backward compatible bug fixes
> 
> Additional labels for pre-release and build metadata are available
> as extensions to the MAJOR.MINOR.PATCH format.

The development of a new MINOR version in RTC-Tools consists of four stages:

1. Alpha (a): Version that is not yet feature complete and may contain bugs.
    Each alpha release can either fix bugs or add new features.
2. Beta (b): Version that is feature complete but is likely to contain bugs.
    After a beta version has been created, no new features can be added anymore.
    A beta version is tested more thoroughly.
3. Release candidate (rc): Version that has been tested through the beta versions releases
    and can now be tested as if it were the stable release.
    If bugs still pop up, new RC versions can be created to fix them.
    Additions are allowed but should be code-unrelated,
    such as changes to the documentation required for the release.
4. Stable release: Final version that has passed all tests.

There can be multiple alpha-, beta-, and rc-versions,
but we should not go back to a previous stage.

An example of a release sequence is:

- 2.6.0a1 Add a feature.
- 2.6.0a2 Add another feature and fix a bug.
- 2.6.0b1 First beta release.
- 2.6.0b2 Fixed a bug.
- 2.6.0b3 Fixed another bug.
- 2.6.0rc1 First release candidate after having tested thoroughly.
- 2.6.0rc2 Fixed a bug that did not show up in the standard tests.
- 2.6.0 **Stable release**.
    No changes were made after last release candidate.
- 2.6.1 Fixed a bug.
- 2.6.2 Fixed another bug.

If we start with a new release cycle for X.Y+1,
and still want to fix a bug for the previous version X.Y,
we create a separate branch `maintenance/X.Y` where we add patches for X.Y.

## Merging Policy and Backwards Compatibility

All contributions to RTC-Tools are reviewed and merged according to the following policy, in line with the project’s technical charter:

- **Review and Approval**: All pull requests must be reviewed by at least one maintainer or committer before being merged. The Technical Steering Committee (TSC) may require additional reviews for significant or controversial changes.
- **Consensus and Voting**: The project aims to operate by consensus. If consensus cannot be reached, the TSC may call a vote as described in the charter.
- **Backwards Compatibility**:
  - CI tests and TeamCity tests are run to ensure that changes do not break existing functionality and maintain API compatibility.
  - Changes that break backwards compatibility (i.e., incompatible API changes) should only be made when necessary and must be clearly documented in the release notes.
  - Contributors are encouraged to maintain backwards compatibility whenever possible. Deprecation warnings should be provided before removing or changing public APIs.
- **Stable Branches**: Bug fixes for previous stable versions should be submitted to the corresponding `maintenance/X.Y` branch.
- **Documentation**: All breaking changes must be accompanied by updates to the documentation and clear migration instructions for users.
- **Release Approval**: The TSC is responsible for approving releases, especially those that include major or backwards-incompatible changes.

By following this merging policy, RTC-Tools ensures a stable and predictable experience for all users and contributors, in accordance with the project’s charter.

## Project Governance

RTC-Tools is governed by a Technical Steering Committee (TSC), responsible for technical oversight, community norms, workflows, and project direction.  

### Governance Roles
- **Contributors**: Anyone who contributes code, documentation, or other artifacts.
- **Committers**: Contributors who have earned the ability to modify (“commit”) source code, documentation, or other technical artifacts.
- **TSC Members**: Initially, the Project’s Committers. The TSC may update its membership and roles as documented here.


### Operational Roles

Contributors, Committers and TSC Members can assume different operational roles, depending on their expertise, interests, and availability. These roles help distribute project responsibilities and ensure smooth operations:

- **Release Manager**: Coordinates releases, manages version numbering, ensures release quality, and oversees release processes.
- **Maintainer**: Day-to-day code maintenance, pull request reviews, and issue triage.
- **Community Manager**: Facilitates community engagement, manages communications, supports contributor onboarding, and moderates discussions.
- **Security, Quality and DevOps Lead**: Handles security vulnerabilities, maintains testing standards, ensures code quality processes, oversees CI/CD infrastructure, and handles DevOps operations.
- **Documentation Lead**: Maintains documentation quality, coordinates documentation efforts.

### TSC Voting

The TSC operates openly and transparently. Meetings are open to the public and may be held electronically or in person.  
Decisions are made by consensus when possible; if a vote is required, each voting member has one vote. 
- Quorum for TSC meetings is at least 50% of voting members.
- Decisions at meetings require a majority of those present, provided quorum is met.
- Electronic votes require a majority of all voting members.
- If a vote cannot be resolved, any voting member may refer the matter to the Series Manager for assistance.

### Becoming a Committer 
To become a Committer, a Contributor must be approved by a majority of existing Committers. Committers may be removed by a majority of the other existing Committers.

### Open Participation

Participation is open to anyone, regardless of affiliation, as long as they abide by this Charter and the project’s policies.

### Code of Conduct

RTC-Tools follows the [LF Projects Code of Conduct](https://lfprojects.org/policies/).  
All participants are expected to act respectfully and professionally.

For more details, see the [Technical Charter](link-to-charter-if-available).


## Licensing and Developer Certificate of Origin (DCO)

- **Code contributions**: All code must be contributed under the GNU Lesser General Public License v3.0 (LGPL-3.0).  
  See [COPYING](https://github.com/Deltares/rtc-tools/blob/master/COPYING) for details.
- **Documentation contributions**: All documentation is licensed under the [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).
- **SPDX Identifiers**: Please include appropriate SPDX license identifiers in new files.

All contributions must also be signed off using the [Developer Certificate of Origin (DCO)](https://developercertificate.org/):

```text
Signed-off-by: Your Name <your.email@example.com>
```

You can add this automatically with:

```bash
git commit -s
```

## Contact

If you have any questions or comments about RTC-Tools, please contact us at rtctools@deltares.nl.

We hope you enjoy using and contributing to RTC-Tools!