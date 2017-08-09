# Raid Coordinator

## Why?

Many Pokemon Go players use discord. Discord lacks threaded conversations. Once your discord server gets about a few hundred members, coordinating raids becomes a challenge. Noise dominates, no one can figure out what is going on. This bot attempts to solve the problem by creating private raid channels and isolating relevant conversations.

This bot uses a convention for managing raids that has worked well for our group. Someone announces the raid in a channel for which the bot has read messages permission. The bot looks for messages with role mentions matching a certain pattern. 

![raid start image](images/raid_start.png)

The bot will announce the raid and open up a private channel for discussing the raid. Other users may enter by reacting to this announcement with an emoji.

When all raid channels are occupied, you will see the following message:

![](images/raid_full.png)

## Features

- Users can join / leave the raid at any time. 
- Channels automatically expire after 2 hours or when everyone leaves.
- The creator or designated raid organizers can end the raid (free up the channel) at any time.
- Does not require permissions to create and delete channels.
- Uses only the amount of channel set aside for it.

## Setup

At the moment, there is no public bot that can be added to your server. You will need to setup and host your own bot.

### Create a new Bot

1. Go to https://discordapp.com/developers/applications/me.

2. Add a new app.

3. Give it a name, optionally a description.

4. Save it and select the option to "create a bot user".


### Invite URL

`https://discordapp.com/oauth2/authorize?client_id=<SETCLIENTIDHERE>&scope=bot&permissions=268435456`

You will want to grant your bot manage role permissions, so it can create some sub-roles. Place the bot role at the bottom of your heirarchy if you don't want it to risk impacting any other roles.

### Channel Configuration

The bot will automatically detect any channels it can use as a raid group. To be detected, the channel must have the following:

- Start with `raid-group-`
- Grant the bot the following permissions (in the channel only):
    - Manage Channel
    - Manage Permissions
    - Read Messages
    - Manage Messages


#### Guide

First, create a new channel with the appropriate name (starting with `raid-group-`)

![](images/create_channel_name.png)

Then, make sure the bot has permission to read it (your role will be whatever role was created when you permissioned the bot for your server, not generic-raid-bot).

![](images/create_channel_bot.png)

Then, go into permissions and grant the bot permissions above

![](images/create_channel_perms1.png)
![](images/create_channel_perms2.png)


You may then right click and hit `clone channel` to copy and make additional channels. Make sure to name them uniquely so as not to confuse your members.


### Running the Bot

To run the bot, install the built wheel or use pip:

`pip install discord-raid-coordinator`

Launch the bot with this:

`raid_coordinator --token "YOUR BOT TOKEN HERE"`

#### Optional Roles

To create the auxillary roles (like raid-viewer, raid-organizer) the first time run:

`raid_coordinator --token "YOUR BOT TOKEN HERE"` --create-roles

Afterwards, you can run the bot without the argument.


### Testing the Bot

To test the bot, you will need to enable it to announce raids on a channel-by-channel basis.

The bot requires read and manage message permissions in any channel its capable of announcing raids.

Make or update a channel with the following permissions:

![](images/create_channel_perms2.png)

Then, test the bot by mentioning a role that starts with `raid-`

![](images/raid_start.png)
