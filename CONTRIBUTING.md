# Contributing

Thank you for your interest in contributing!

We welcome contributions from the community and appreciate your efforts to improve this project.

---

## 📝 Contributor License Agreement

**Before your first contribution can be accepted, you must sign the Perforce Contributor License Agreement ("CLA").**

The CLA grants Perforce a perpetual, worldwide, royalty-free copyright and patent license to use, reproduce, modify, and distribute your contributions as part of this project. It also includes your representations that you are entitled to make the contribution, that your submission is your original work, and that you have disclosed any known third-party licenses or restrictions associated with your contribution.

To sign the CLA:

1. Download the CLA here: [CLA.docx](https://github.com/perforce/p4python/blob/master/CLA.docx);
2. Complete the signature block, including your name, title, date, and GitHub username; and
3. Return the signed CLA to [contracts@perforce.com](mailto:contracts@perforce.com) prior to submitting your first pull request.

Electronic signatures are accepted. Your pull request will not be reviewed until a signed CLA is on file with Perforce.

If you are contributing in the course of your employment, or your employer has intellectual property rights in your submission by contract or applicable law, you must obtain written permission from your employer before signing the CLA. In that case, the CLA will be treated as signed on behalf of both you and your employer. Please refer to Section 3 of the CLA for full details.

Signing the CLA does not affect your rights to use your own contributions for any other purpose.

---

## 🚀 Getting Started

1. **Fork the Repository**

    ```
    git clone https://github.com/<your-username>/p4python.git
    cd p4python
    ```
2. **Create a Branch**

    ```
    git checkout -b feature/<short-description>
    ```

    Use clear, descriptive branch names. For example:

    * `feature/<description>`
    * `fix/<description>`
    * `docs/<description>`

---

## 📋 Coding Guidelines

* Follow language-specific style guidelines
* Keep changes focused and minimal
* Maintain backward compatibility where possible
* Add comments where behavior is not obvious
* Update documentation when modifying functionality

---

## 🧪 Testing Guidelines

Before submitting a pull request (PR):

* Ensure the code builds and runs locally
* Test your changes in a realistic environment
* Validate both standard and edge-case behavior
* Ensure error handling is clear and actionable

Be especially careful with:

* Data modification or destructive operations
* Configuration or environment handling
* Validation and error handling logic

---

## 🧠 Commit Message Guidelines

Use clear, imperative commit messages.

**Good examples:**

* Added validation for configuration input
* Fixed issue with environment variable parsing
* Improved error handling for API failures

**Bad examples:**

* Fixed stuff
* Update
* Changes

Reference issues when applicable:

```
Fixes #123
```

---

## 🔄 Contribution Workflow

We accept pull requests (PRs), but **do not merge them directly on GitHub**.

Instead, contributions follow this process:

1. PR is reviewed on GitHub
2. If accepted:

    * A Jira ticket is created internally
    * Changes are integrated into our internal system
    * The update is included in a future release

3. Maintainers will comment on the PR to:

    * Confirm acceptance or request changes
    * Provide additional context if needed
    * Indicate if/when the change will be included in a release

### What this means for contributors

* Your PR may be **closed without being merged**, even if accepted
* Accepted contributions are still implemented through our internal workflow
* You may be asked to revise your PR before it is accepted

This process ensures proper validation, testing, and controlled releases.

---

## 🔐 Security and Safety

Contributions must:

* Avoid introducing unsafe or destructive behavior by default
* Ensure proper validation and safeguards are in place
* Not expose sensitive information (credentials, tokens, etc.)
* Follow secure coding practices

---

## 🐞 Reporting Issues

Use GitHub Issues to report:

* Bugs
* Feature requests
* Documentation gaps

Include:

* Environment details (OS, runtime version, etc.)
* Steps to reproduce
* Relevant logs or screenshots
* Expected vs actual behavior

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.
