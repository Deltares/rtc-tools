# Contributing to RTC-Tools 2

There are many ways you can contribute to RTC-Tools, such as:

- **Reporting issues**: If you encounter any bugs, errors, or unexpected behavior while using RTC-Tools, 
please report them on our [issue tracker](https://github.com/deltares/rtc-tools/issues).
Please follow the issue template and provide as much information as possible to help us reproduce and fix the issue.
- **Suggesting features**: If you have any ideas or suggestions for new features or improvements, 
please share them on our [issue tracker](https://github.com/deltares/rtc-tools/issues).
Please use the appropriate category and tag for your topic and explain your motivation and use case clearly.
- **Submitting pull requests**: If you want to contribute code or documentation to RTC-Tools, please create a pull request. Before submitting, please follow the [Guidelines for creating merge requests](#guidelines-for-creating-merge-requests) below.  
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
2. **Description**: Describe the issue in detail. Include steps to reproduce the issue, expected behavior, and actual behavior. Mention the versions of RTC-Tools, Python and external packages you're using (CasADi, Pymoca, numpy), along with relevant details about your operating system.
3. **Minimal reproducible example**: Whenever possible, include a minimal reproducible example that demonstrates the issue. This should be the smallest amount of code and data necessary to reproduce the problem. Providing a minimal example helps maintainers quickly understand, reproduce, and address your issue.
4. **Labels**: Use labels to categorize the issue. This helps in prioritizing and resolving issues.

### Security Reporting

If you discover a security vulnerability, please report it responsibly by emailing [rtctools@deltares.nl](mailto:rtctools@deltares.nl) rather than opening a public issue.

## Guidelines for creating merge requests
1. **Identify or create an issue**: Before making any changes, open an issue following the [guidelines](#guidelines-for-creating-issues) above, or comment on an existing one in the [issue tracker](https://github.com/deltares/rtc-tools/issues) to discuss your ideas with the maintainers. This helps avoid duplication and ensures your contribution aligns with project goals and the [governance model](GOVERNANCE.md).
2. **Fork or Branch**:
    - New Contributors: Fork the repository and create a new branch in your fork.
    - Committers: Create a new branch directly in the main repository.Use a descriptive branch name, such as `feature/short-description`, `bugfix/issue-123`, or `docs/update-readme`.
3. **Commit**: Make clear, focused commits following the [Commits and Commit Messages](#commits-and-commit-messages) guidelines.
4. **Write tests**: If possible, write tests that cover your changes and add them to the `tests` folder. This helps ensure your changes work as intended and prevent regressions.
5. **Documentation**: Update documentation and add examples to the `examples` folder if necessary.
6. **Create a pull request**: Reference the corresponding issue in your PR description. Clearly describe what changes you've made, why, and any relevant context.
7. **Check CI status**: Ensure all automated checks and tests pass before requesting a review.
8. **Request review**: Ask for a code review from your peers and address any comments or suggestions.

Contributors should rebase their branches on the latest main branch before submitting pull requests, and maintainers will use rebase when integrating changes.

Keep pull requests small and focused for easier review and faster merging.

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
- **Code coverage**: Ensure a code coverage of at least 80% to comply with SonarQube requirements.
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

## Project Governance

RTC-Tools is governed according to the [Technical Charter](CHARTER.md) and detailed in the [Governance](GOVERNANCE.md) document, which together establish:

- The project structure and roles
- Decision-making processes
- Contribution guidelines
- Code of conduct requirements

All contributors are expected to follow the governance model outlined in the [Technical Charter](CHARTER.md) and [Governance](GOVERNANCE.md) documents.

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