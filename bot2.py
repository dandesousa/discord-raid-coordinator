import asyncio
import discord
import json
import sys
import time


settings_path = "settings.json" if len(sys.argv) == 1 else sys.argv[1]
settings = json.load(open(settings_path, "rt"))

client = discord.Client()


def get_announcement_channel(server):
    """Gets the announcement channel for a server."""
    return discord.utils.find(lambda c: c.name == settings['announcement_channel'], server.channels)


def get_join_emoji(server):
    """Gets the join emoji for a server."""
    return discord.utils.find(lambda e: e.name == settings['join_emoji'], server.emojis)


def get_raid_group_channel_general_permissions():
    """Permissions everyone should have by default in the raid group channel."""
    return discord.PermissionOverwrite(read_messages=False)


def get_raid_group_channel_bot_permissions():
    """Permissions the bot should have in the raid group channel."""
    return discord.PermissionOverwrite(read_messages=True,
                                       manage_channels=True,
                                       manage_roles=True)


def is_raid_channel(channel, expired=False):
    """Whether the channel is a valid raid_channel.

    A channel is a valid raid channel if:
        - It looks like a raid channel (prefix-ts-userid).
        - This raid bot can read the messages in the channel.
        - It has a timestamp for expiration.
        - If expired is True, the expiration_ts is earlier than now
        - If expired is False (default), expiration_ts is later than now
    """
    if channel:
        bot_can_read = channel.permissions_for(channel.server.me).read_messages
        try:
            prefix, expiration_ts, user_id = channel.name.split('-', 2)
            is_expired = (int(expiration_ts) - int(time.time())) < 0
            return settings['raid_group_prefix'] == prefix and bot_can_read and expired == is_expired
        except ValueError:
            pass


@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user.name))
    print('------')
    await cleanup_raid_channels()


async def announce_raid(announcement_channel, raid_channel, *roles):
    """Announces that a raid occurred on a channel."""
    msg = ' '.join(role.mention for role in roles)
    if msg:
        msg += '. '
    msg += 'A raid has started in {}!'.format(raid_channel.mention)
    await client.send_message(announcement_channel, msg)


async def invite_user_to_raid(channel, user):
    perms = discord.PermissionOverwrite(read_messages=True)
    await client.edit_channel_permissions(channel, user, perms)
    msg = await client.send_message(channel, '{} has joined the raid!'.format(user.mention))
    return msg


async def cleanup_raid_channels():
    """EXTREMELY paranoid cleanup of channels.

    Only cleanup channels that look like raid channels.

    Also bot has to be explicitly overridden.
    """
    while True:
        channels = list(client.get_all_channels())
        for channel in channels:
            if is_raid_channel(channel, expired=True):
                pass
                # NB: PLEASE BE VERY VERY VERY VERY VERY VERY CAREFUL HERE.
                # there is no way to restrict permissions to delete only channels
                # the bot has created, so we make is_raid_channel very restrictive.
                # This is still a bool and subject to making a mistake.
                # Reconsider this:
                # await client.delete_channel(channel)
        await asyncio.sleep(30)


@client.event
async def on_reaction_add(reaction, user):
    """Invites a user to a raid channel they react to they are no already there."""
    message = reaction.message
    raid_channel = message.channel_mentions[0] if message.channel_mentions else None
    if is_raid_channel(raid_channel, expired=False):
        # NB: use overwrites for, since admins otherwise won't be notified
        # we know the channel is private and only overwrites matter
        if raid_channel.overwrites_for(user).is_empty():
            await invite_user_to_raid(raid_channel, user)


@client.event
async def on_message(message):
    server = message.server
    creation_channel = message.channel
    creation_user = message.author
    expiration_ts = int(time.time()) + settings['raid_group_duration_seconds']
    raid_group_channel_name = '{}-{}-{}'.format(settings['raid_group_prefix'],
                                                expiration_ts,
                                                creation_user.id)

    if message.content.startswith('$startraid'):
        # set the channel creation message
        channel_creation_msg = await client.send_message(creation_channel, 'Creating {}...'.format(raid_group_channel_name))

        # create the channel
        raid_channel = await client.create_channel(server, raid_group_channel_name,
                                                   (server.default_role, get_raid_group_channel_general_permissions()),
                                                   (server.me, get_raid_group_channel_bot_permissions()),
                                                   )

        # update the channel creation message
        await client.edit_message(channel_creation_msg, 'Raid has started in {}!'.format(raid_channel.mention))

        # invite the original raid creator to the channel
        # await invite_user_to_raid(raid_channel, creation_user)

        # makes an announcement in the announcement channel people can respond to.
        announcement_channel = get_announcement_channel(server)
        await announce_raid(announcement_channel, raid_channel)
        # post the instructions in the raid channel


        #announcement_message = await client.send_message(announce_channel, 'A raid has started!')
        #print("Waiting for reaction")
        #e = join_emoji(server)
        #response = await client.wait_for_reaction([e], message=announcement_message)
        #print("Got for reaction")
        #their_perms = discord.PermissionOverwrite(read_messages=True)
        #await client.edit_channel_permissions(raid_channel, response.user, their_perms)
        #welcome = await client.send_message(raid_channel, '{} has joined the raid group'.format(response.user.mention))
        #await asyncio.sleep(15)
        #await client.delete_channel(raid_channel)
        #await client.edit_message(tmp, 'Raid Group Closed')


client.run(settings['token'])
