# Frequently Asked Questions

## Bot Features

#### Can I add more raid groups to the server while the bot is running?

Yes. Try to do this on an empty raid group so you copy an empty channel with no users permissioned for it.

#### How do you keep track of everything?

The bot uses no database or local storage aside from the in-memory cache provided by discord.py. 

This means its always safe to restart your bot and it will pick up where it left off. 

All relationships are stored on the discord server itself, through setting permissions and channel topics.

## Service and Help

#### Can you setup a bot for my server?

Sorry, but no. Every public bot I've used has had periods of opaque downtime and I'm not prepared to support servicing the many existing PoGo discord servers. This repo should contain all the instructions necessary to set it up yourself.


#### I noticed a bug, where can I report it?

Please file and issue ticket on the github page. If possible include screenshots and be descriptive. Some behaviors are known and a result of transient discord server issues.

#### I want the bot to do X, can you make it do X?

Open up an issue on the github page and we can discuss it. There are many suggestions of features to add, but it is important to keep them universally applicable and useful to most PoGo discord groups. If its of use to most servers, we can talk about adding it to the bot.
