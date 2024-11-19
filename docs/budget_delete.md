<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [About MyDollarBot's budget_delete module](#about-mydollarbots-budget_delete-module)
- [Location of Code for this Feature](#location-of-code-for-this-feature)
- [Code Description](#code-description)
  - [Functions](#functions)
- [How to run this feature?](#how-to-run-this-feature)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# About MyDollarBot's budget_delete module
The budget_view module contains all the functions required to implement the display delete/removal feature. In essence, all operations involved in removal and deletion of a budget are taken care of in this module and are implemented here.

# Location of Code for this Feature
The code that implements this feature can be found [here](https://github.com/sak007/MyDollarBot-BOTGo/blob/main/code/budget_delete.py)

# Code Description
## Functions

1. run(message, bot):
This is the main function used to implement the budget delete feature. It takes 2 arguments for processing - **message** which is the message from the user, and **bot** which is the telegram bot object from the main code.py function. It gets the user's chat ID from the message object, and reads all user data through the read_json method from the helper module. It then proceeds to empty the budget data for the particular user based on the user ID provided from the UI. It returns a simple message indicating that this operation has been done to the UI.


# How to run this feature?
Once the project is running(please follow the instructions given in the main README.md for this), please type /budget into the telegram bot. Add a budget and then type /budget again. Please choose the option for deleting a budget.
