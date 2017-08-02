# Raid Bot

## Why?

Many Pokemon Go players use discord. Discord lacks threaded conversations. Once your discord server gets about a few hundred members, coordinating raids becomes a huge challenge. Noise dominates, no one can figure out what is going on. This bot attempts to solve the problem by creating private raid channels and isolating relevant conversations.

This bot uses a convention for managing Raids that has worked well for our group. Someone announces the raid in a channel for which the bot has read messages permission. The bot looks for messages with role mentions matching a certain pattern. The bot will echo the message and open up a private channel for discussing the raid. Other users may enter by reacting to the the announcement with a designatd emoji.

## Features

- Users can leave the raid at any time. 
- Channels automatically expire after 2 hours or when everyone leaves.
- The creator or designated raid organizers can end the raid (free up the channel) at any time.
- Does not require permissions to create and delete channels.
- Uses only the amount of channel set aside for it.

## Setup

At the moment, there is no public bot that can be added to your server. You will need to setup and host your own bot.

### Create a new Bot

### Invite URL

`https://discordapp.com/oauth2/authorize?client_id=<SETCLIENTIDHERE>&scope=bot&permissions=268435456`

You will want to grant your bot manage role permissions.

### Channel Configuration

TODO
