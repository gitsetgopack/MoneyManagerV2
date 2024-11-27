<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Contributing to Money Manager](#contributing-to-money-manager)
  - [Getting Started](#getting-started)
    - [1. Fork the Repository](#1-fork-the-repository)
    - [2. Clone Your Fork](#2-clone-your-fork)
    - [3. Set Up Environment](#3-set-up-environment)
    - [4. Fill in the config.py]()
    - [5. Create a Branch](#5-create-a-branch)
    - [6. Make Changes](#6-make-changes)
    - [7. Pre-commit checks]()
    - [8. Run Locally]()
    - [9. Commit Changes](#9-commit-changes)
    - [10. Push Changes](#10-push-changes)
    - [11. Submit a Pull Request](#11-submit-a-pull-request)
  - [Code of Conduct](#code-of-conduct)
  - [Guidelines](#guidelines)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contributing to Money Manager V2

Thank you for considering contributing to **MoneyManagerV2**! We welcome all types of contributions, whether you're fixing a bug, adding a feature, improving documentation, or suggesting an idea.

## Getting Started

To get started with contributing to this project, please follow these guidelines.

### 1. Fork the Repository

Start by forking the main repository on GitHub. This creates a copy of the repository under your GitHub account.

- Navigate to [MoneyManager GitHub Repo](https://github.com/gitsetgopack/MoneyManagerV2)
- Click the **Fork** button in the top-right corner.

### 2. Clone Your Fork

Once you've forked the repository, clone your fork locally:

```bash
git clone https://github.com/your-username/MoneyManagerV2.git
cd MoneyManagerV2
```

Replace `your-username` with your GitHub username.

### 3. Set Up Environment

To set up the environment, use the following command to install dependencies:

```bash
make install
```

This will install all necessary Python packages and set up the pre-commit hooks.

### 4. Fill in the config.py

Before running the application, you need to set up the necessary configurations in the config.py file. Follow these steps:

- **Create a bot and get its token:** Set up a bot using the Telegram Bot API, and obtain the API token required to integrate the bot with the application.
- **Create a Gmail account and get the app password:** Generate an app-specific password for Gmail to enable email functionality securely.
- **Set up a MongoDB database and get the connection token:** Create a MongoDB cluster or database, and retrieve the connection string/token for the database.

Ensure you replace the placeholder values in config.py with the actual credentials and tokens for these services.

### 5. Create a Branch

It's good practice to create a new branch for each change. This makes it easier to submit pull requests.

```bash
git checkout -b feature/new-feature
```

Replace `feature/new-feature` with a meaningful name for your branch.

### 6. Make Changes

Make your changes to the codebase. Ensure you write unit tests if applicable.

To run tests locally:

```bash
make test
```

### 7. Pre-commit checks

Before committing your changes, it's essential to ensure your code adheres to the project's coding standards and conventions. Use the pre-commit framework to automate these checks. Run the following command to execute all pre-commit hooks:

```bash
pre-commit run --all-files
```

This command will run `black`, `isort`, 'pylint' and other checks to ensure the code style is consistent.

### 8. Run locally

Once the necessary configurations and pre-commit checks are completed, you can run the application locally to test your changes. Use the following commands:

Start the backend API server using the following command:
```bash
make api
```
This initializes the API server, making it accessible for integration testing and further development.

Launch the Telegram bot to test its functionality and interaction:
```bash
make telegram
```
Ensure both the API and bot are running concurrently for seamless operation. Test various features thoroughly to confirm that your changes are working as expected.

### 9. Commit Changes

Commit your changes with a descriptive commit message:

```bash
git add .
git commit -m "Added a new feature to manage categories"
```

### 10. Push Changes

Push your changes to your forked repository:

```bash
git push origin feature/new-feature
```

### 11. Submit a Pull Request

Once you've pushed your changes, go to the main repository on GitHub and submit a pull request (PR) from your forked repository.

- Navigate to your fork on GitHub.
- Click **Compare & Pull Request**.
- Provide a clear and concise description of your changes in the PR description.

## Code of Conduct

We expect all contributors to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please respect others' work and efforts, and let's collaborate effectively to improve **MoneyManagerV2** together.

## Guidelines

- Write clear, concise commit messages.
- Test your changes thoroughly.
- Include tests for any new functionality.
- If you have any questions, please open an issue or contact the maintainers.

Thank you for your contributions and for making **Money ManagerV2** better!
