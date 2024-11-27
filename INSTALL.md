<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [MoneyManagerV2 Installation Guide](#moneymanager-installation-guide)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
  - [Available Make Commands](#available-make-commands)
  - [Additional Information](#additional-information)
  - [Troubleshooting](#troubleshooting)
  - [Running the Project](#running-the-project)
  - [Running Tests](#running-tests)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# MoneyManager Installation Guide

Welcome to the **MoneyManagerV2** project! This guide will help you set up the environment and install dependencies to get started.

## Prerequisites

Before beginning the installation, please ensure you have the following installed:

- **Python** (version 3.8 or higher)
- **Git** (to clone the repository)
- **Docker** (for running MongoDB in a Docker container during testing)

## Installation Steps

1. **Clone the Repository**

   Begin by cloning the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/MoneyManagerV2.git
   cd MoneyManagerV2
   ```

2. **Install Dependencies**

   Run the following command to install all required dependencies:

   ```bash
   make install
   ```

   This command will:
   - Upgrade `pip` to the latest version.
   - Install the required Python packages as specified in the `requirements.txt`.
   - Install pre-commit hooks.

## Fill in the config.py

Before running the application, you need to set up the necessary configurations in the config.py file. Follow these steps:

- **Create a bot and get its token:** Set up a bot using the Telegram Bot API, and obtain the API token required to integrate the bot with the application.
- **Create a Gmail account and get the app password:** Generate an app-specific password for Gmail to enable email functionality securely.
- **Set up a MongoDB database and get the connection token:** Create a MongoDB cluster or database, and retrieve the connection string/token for the database.

Ensure you replace the placeholder values in config.py with the actual credentials and tokens for these services.

## Available Make Commands

Here are the commands available in the `Makefile` to help you work with the project:

- **help**: Show this help message, displaying all available commands.
  ```bash
  make help
  ```

- **install**: Install dependencies in the virtual environment.
  ```bash
  make install
  ```

- **run**: Run the FastAPI application using the virtual environment.
  ```bash
  make api
  ```

  This will execute the FastAPI app located at `api/app.py`.

- **telegram**: Launch the Telegram bot to test its functionality and interaction.
  ```bash
  make telegram
  ```

  This will initialize the telegram bot.

- **test**: Start a MongoDB Docker container, run tests, and clean up after the tests.
  ```bash
  make test
  ```

  This command will:
  - Start a MongoDB container to simulate a database for testing.
  - Run all tests using `pytest`.
  - Stop and remove the MongoDB container after testing is complete.

- **pre-commit**: Will run `black`, `isort`, `pylint` and other checks to ensure the code style is consistent.
  ```bash
  pre-commit run --all-files
  ```

- **clean**: Clean up Python bytecode files, cache, and MongoDB Docker containers.
  ```bash
  make clean
  ```

  This will:
  - Stop and remove the `mongo-test` Docker container if it exists.
  - Remove Python bytecode files (`.pyc`) and caches like `__pycache__`, `.pytest_cache`, and `.mypy_cache`.

- **no_verify_push**: Stage, commit, and push changes with `--no-verify` to skip pre-commit hooks.
  ```bash
  make no_verify_push
  ```

  This command allows you to quickly commit and push changes without running verification checks. It will prompt you for a commit message.

## Additional Information

- **Makefile**: The `Makefile` includes useful commands to set up, run, and test the project. You can inspect it for more details on available commands.
- **Python Environment**: It’s recommended to create a virtual environment for this project to keep dependencies isolated. Run `python -m venv venv` before `make install` if needed.

## Troubleshooting

- **Python Compatibility**: Ensure Python is in your system’s `PATH` and meets the required version.
- **Dependency Issues**: If you encounter issues, check the `requirements.txt` file for compatibility, or re-run `make install` after activating a virtual environment.
- **Docker Issues**: Make sure Docker is installed and running properly before executing commands that require a MongoDB container.

## Running the Project

After installation, you can run the FastAPI server by executing:

```bash
make api
```

This command will start the application, and you can access it in your browser at the specified URL.

## Running Tests

To run the tests, ensure Docker is running and then use:

```bash
make test
```

This command will automatically set up the necessary database for testing purposes.

---

Feel free to reach out if you have any issues setting up **MoneyManagerV2**!
