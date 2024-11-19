<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [About MyDollarBot's /history Feature](#about-mydollarbots-history-feature)
- [Location of Code for this Feature](#location-of-code-for-this-feature)
- [Code Description](#code-description)
  - [Functions](#functions)
- [How to run this feature?](#how-to-run-this-feature)
  - [DATE, CATEGORY, AMOUNT](#date-category-amount)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# About MyDollarBot's /history Feature
This feature enables the user to view all of their stored records i.e it gives a historical view of all the expenses stored in MyDollarBot.

# Location of Code for this Feature
The code that implements this feature can be found [here](https://github.com/prithvish-doshi-17/MyDollarBot-BOTGo/blob/main/code/history.py)

# Code Description
## Functions

1. run(message, bot):
This is the main function used to implement the delete feature. It takes 2 arguments for processing - **message** which is the message from the user, and **bot** which is the telegram bot object from the main code.py function. It calls helper.py to get the user's historical data and based on whether there is data available, it either prints an error message or displays the user's historical data.

# How to run this feature?
Once the project is running(please follow the instructions given in the main README.md for this), please type /add into the telegram bot.

Below you can see an example in text format:

Vraj Chokshi, [23.11.21 20:33]
/display

Vraj Chokshi, [23.11.21 20:33]
Month

mydollarbot20102021, [23.11.21 20:33]
Hold on! Calculating...

Vraj Chokshi, [23.11.21 20:53]
/history

mydollarbot20102021, [23.11.21 20:53]
Here is your spending history :
DATE, CATEGORY, AMOUNT
----------------------
01-Dec-2021,Transport,100.0
23-Nov-2021 15:13,Groceries,500.0

Along with the spending history, the histogram displaying spending of each month is plotted, which can help user to manage his/her expenses.

![Test Image ](https://github.com/prithvish-doshi-17/MyDollarBot-BOTGo/blob/main/histo.png)
