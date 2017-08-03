import asyncio
import discord
import functools
import json
import re
import sys
import time
import traceback
import pytz
from collections import namedtuple
from datetime import datetime, timedelta, timezone


# buffer for busier servers
MAX_MESSAGES = 10000


# process level client
client = discord.Client(max_messages=MAX_MESSAGES)

# process level cache by server
# discord.Server -> dict()
cache = dict()

# bot specific settings
settings = None

#
# Bot Cacheable Attributes

def get_raid_additional_roles(server):
    """Gets roles that should get read perms when the raid is started."""
    return [r for r in server.roles if r.name in settings.raid_additional_roles]


def get_raid_organizer_roles(server):
    """Gets roles that can help organizer raids."""
    return [r for r in server.roles if r.name in settings.raid_organizer_roles]


def encode_message(message):
    """Encodes the message."""
    return "{}|{}".format(message.channel.id, message.id)


def decode_message(data):
    """Decode the message."""
    try:
        channel_id, message_id = data.split('|')
    except:
        return None, None

    return channel_id, message_id


def lookup_raid_channel(message):
    server = message.server
    if message.channel_mentions:
        raid_channel = message.channel_mentions[0]
        channel_id, message_id = decode_message(raid_channel.topic)
        return raid_channel if message.channel.id == channel_id and message_id == message.id else None


def get_raid_channels(server):
    """Gets the list of raid channels for ther server."""
    raid_channels = []
    rx = re.compile(settings.raid_channel_regex)
    for channel in server.channels:
        p = channel.permissions_for(server.me)
        if rx.search(channel.name) and p.manage_roles and p.manage_messages and p.manage_channels and p.read_messages:
            raid_channels.append(channel)
    return raid_channels



#
# End server cacheable attributes
#


#
# Configuration abstraction
#

def get_join_emoji():
    """Gets the join emoji for a server."""
    return settings.raid_join_emoji


def get_leave_emoji():
    """Gets the leave emoji for a server."""
    return settings.raid_leave_emoji


def get_full_emoji():
    """Gets the full emoji for a server."""
    return settings.raid_full_emoji


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def adjusted_datetime(dt, tz='US/Eastern'):
    zone = pytz.timezone(tz)
    return dt + zone.utcoffset(dt)


def get_raid_expiration(started_dt):
    return started_dt + timedelta(seconds=settings.raid_duration_seconds)

#
#
#

#
# Raid properties
#


def get_raid_role(channel):
    return discord.utils.find(lambda r: r.name == channel.name, channel.server.roles)


def get_raid_members(channel):
    return [target for target, _ in channel.overwrites if isinstance(target, discord.User)]


def get_raid_start_embed(creator, started_dt, expiration_dt):
    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'A raid has started!'
    embed.add_field(name='creator', value=creator.mention, inline=True)
    embed.add_field(name='started at', value=started_dt.strftime(settings.time_format), inline=False)
    embed.add_field(name='channel expires', value=expiration_dt.strftime(settings.time_format), inline=False)
    embed.set_footer(text='To join, tap {} below'.format(get_join_emoji()))
    return embed


def get_raid_end_embed(creator, started_dt, ended_dt):
    duration = ended_dt - started_dt
    embed = discord.Embed()
    embed.color = discord.Color.red()
    embed.title = 'This raid has ended.'
    embed.add_field(name='creator', value=creator.mention if creator else None, inline=True)
    embed.add_field(name='duration', value=strfdelta(duration, '{hours:02}:{minutes:02}:{seconds:02}'), inline=True)
    embed.add_field(name='started at', value=started_dt.strftime(settings.time_format), inline=False)
    embed.add_field(name='ended at', value=ended_dt.strftime(settings.time_format), inline=False)
    return embed


def get_success_embed(text):
    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.description = text
    return embed


def get_error_embed(text):
    embed = discord.Embed()
    embed.color = discord.Color.red()
    embed.description = text
    return embed


def get_raid_busy_embed():
    embed = discord.Embed()
    embed.color = discord.Color.dark_teal()
    embed.title = 'All raid channels are busy at the moment.'
    embed.description = 'Coordinate this raid in another channel instead. More channels will be available later.'
    return embed


def get_raid_members_embed(members):
    embed = discord.Embed()
    embed.title = "Raid Members ({})".format(len(members))
    embed.description = "\n".join(sorted(member.display_name for member in members))
    embed.color = discord.Color.green()
    return embed


def get_raid_summary_embed(creator, channel_name, expiration_dt, text):
    embed = discord.Embed()
    embed.title = 'Welcome to this raid channel!'
    embed.description = "**{}**".format(text)
    embed.add_field(name='creator', value=creator.mention)
    embed.add_field(name='channel expires', value=expiration_dt.strftime(settings.time_format))
    embed.add_field(name='raid group', value='@{}'.format(channel_name), inline=False)
    embed.add_field(name="commands", value="You can use the following commands:", inline=False)
    embed.add_field(name="$leaveraid", value="Removes you from this raid.", inline=False)
    embed.add_field(name="$listraid", value="Shows all current members of this raid channel.", inline=False)
    embed.add_field(name="$endraid", value="Ends the raid and closes the channel.", inline=False)
    embed.set_footer(text='You can also leave the raid with the {} reaction below.'.format(get_leave_emoji()))
    embed.color = discord.Color.green()
    return embed


def is_raid_start_message(message):
    """Whether this is the start of a new raid."""
    if message.role_mentions:
        rx = re.compile(settings.raid_start_regex)
        return any(rx.search(mention.name) for mention in message.role_mentions)


def is_raid_channel(channel):
    """Whether the channel is a valid raid_channel.
    """
    return channel and channel in get_raid_channels(channel.server)



def is_open(channel):
    return channel.topic is None


async def get_announcement_message(raid_channel):
    """Gets the message that created this channel."""
    server = raid_channel.server
    channel_id, message_id = decode_message(raid_channel.topic)
    try:
        channel = server.get_channel(channel_id)
        if channel:
            message = await client.get_message(channel, message_id)
            return message
    except:
        return None  # an error occurred, return None TODO: log here



async def get_raid_creator(raid_channel):
    message = await get_announcement_message(raid_channel)
    if message and message.embeds:
        embed = message.embeds[0]
        fields = embed.get('fields', [])
        if fields:
            creator_mention = fields[0]['value']

            # try in the overwrites
            for target, _ in raid_channel.overwrites:
                if isinstance(target, discord.User) and target.mention == creator_mention:
                    return target

            # otherwise try in the server users (less efficient but right)
            for target in raid_channel.server.members:
                if isinstance(target, discord.User) and target.mention == creator_mention:
                    return target

def get_raid_channel(message):
    """Pulls out the channel field from the message embed."""
    return message.channel_mentions[0] if message.channel_mentions else None


async def is_raid_expired(raid_channel):
    message = await get_announcement_message(raid_channel)
    if message is None:
        return True  # can't find message, clean up the raid channel
    create_ts = message.timestamp.replace(tzinfo=timezone.utc).timestamp()
    return settings.raid_duration_seconds < time.time() - create_ts


def get_available_raid_channel(server):
    """We may need to wrap function calls to this in a lock."""
    for channel in get_raid_channels(server):
        if is_open(channel):
            return channel




async def start_raid_group(user, message, description):
    # get the server
    server = user.server

    # find an available raid channel
    channel = get_available_raid_channel(server)

    if channel:
        # set the topic
        await client.edit_channel(channel, topic=encode_message(message))

        # create a role with the same name as this channel
        role = await client.create_role(server, name=channel.name, mentionable=True)

        # calculate expiration time
        expiration_dt = adjusted_datetime(get_raid_expiration(message.timestamp))
        summary_message = await client.send_message(channel, embed=get_raid_summary_embed(user, channel.name, expiration_dt, description))

        # add shortcut reactions for commands
        await client.add_reaction(summary_message, get_leave_emoji())

        # set channel permissions to make raid viewers see the raid.
        for role in get_raid_additional_roles(server):
            perms = discord.PermissionOverwrite(read_messages=True)
            await client.edit_channel_permissions(channel, role, perms)

        return channel

async def end_raid_group(channel):
    # get the creator before we remove roles
    creator = await get_raid_creator(channel)

    # remove all the permissions
    raid_viewer_roles = get_raid_additional_roles(channel.server)
    for target, _ in channel.overwrites:
        if isinstance(target, discord.User) or target in raid_viewer_roles:
            await client.delete_channel_permissions(channel, target)

    # remove the role
    role = get_raid_role(channel)
    if role:
        try:
            await client.delete_role(channel.server, role)
        except:
            print('Unable to delete role, it was already removed {}.'.format(role.name))

    # purge all messages
    await client.purge_from(channel)

    # update the message if its available
    message = await get_announcement_message(channel)
    if message:
        started_dt = adjusted_datetime(message.timestamp)
        ended_dt = adjusted_datetime(datetime.utcnow())
        await client.edit_message(message, embed=get_raid_end_embed(creator, started_dt, ended_dt))
        await client.clear_reactions(message)

    # remove the topic
    channel = await client.edit_channel(channel, topic=None)


async def invite_user_to_raid(channel, user):
    # adds an overwrite for the user
    perms = discord.PermissionOverwrite(read_messages=True)
    await client.edit_channel_permissions(channel, user, perms)

    # invite user to role
    role = get_raid_role(channel)
    if role:
        await client.add_roles(user, role)

    # sends a message to the raid channel the user was added
    await client.send_message(channel,
                              "{}, you are now a member of this raid group.".format(user.mention),
                              embed=get_success_embed('{} has joined the raid!'.format(user.mention)))


async def uninvite_user_from_raid(channel, user):
    # reflect the proper number of members (the bot role and everyone are excluded)
    await client.delete_channel_permissions(channel, user)
    await client.send_message(channel, embed=get_error_embed('{} has the left raid!'.format(user.mention)))

    # delete user from role
    role = get_raid_role(channel)
    if role:
        await client.remove_roles(user, role)

    # remove the messages emoji
    server = channel.server
    announcement_message = await get_announcement_message(channel)
    await client.remove_reaction(announcement_message, get_join_emoji(), user)


async def list_raid_members(channel):
    members = get_raid_members(channel)
    await client.send_message(channel, embed=get_raid_members_embed(members))


async def cleanup_raid_channels():
    await client.wait_until_ready()
    while not client.is_closed:
        try:
            for server in client.servers:
                channels = get_raid_channels(server)
                for channel in channels:
                    if not is_open(channel):
                        expired = await is_raid_expired(channel)
                        if expired or not get_raid_members(channel):
                            await end_raid_group(channel)
        except:
            print('An exception was thrown in the cleanup thread. But we saved it:')
            traceback.print_exc()

        await asyncio.sleep(settings.raid_cleanup_interval_seconds)


@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user.name))
    print('------')


    for server in client.servers:
        print('server: {}'.format(server.name))

        raid_channels = get_raid_channels(server)
        print('{} raid channel(s)'.format(len(raid_channels)))
        for channel in raid_channels:
            print('raid channel: {}'.format(channel.name))

            # adds the message back into the cache
            message = await get_announcement_message(channel)
            if message is not None:
                client.messages.append(message)  # this is a hack but it puts the message back in the cache to resume


@client.event
async def on_reaction_add(reaction, user):
    """Invites a user to a raid channel they react to they are no already there."""
    server = reaction.message.server
    message = reaction.message
    if user == server.me:
        return


    if reaction.emoji == get_join_emoji():
        raid_channel = lookup_raid_channel(message)
        if raid_channel:
            # NB: use overwrites for, since admins otherwise won't be notified
            # we know the channel is private and only overwrites matter
            if raid_channel.overwrites_for(user).is_empty():
                await invite_user_to_raid(raid_channel, user)

    elif reaction.emoji == get_leave_emoji():
        raid_channel = message.channel
        if is_raid_channel(raid_channel) and reaction.message.author == server.me:
            # NB: use overwrites for, since admins otherwise won't be notified
            # we know the channel is private and only overwrites matter
            if not raid_channel.overwrites_for(user).is_empty():
                await uninvite_user_from_raid(raid_channel, user)

                # remove this reaction
                await client.remove_reaction(message, reaction.emoji, user)


@client.event
async def on_reaction_remove(reaction, user):
    """Uninvites a user to a raid when they remove a reaction if they are there."""
    server = reaction.message.server
    message = reaction.message
    if user == server.me:
        return

    if reaction.emoji == get_join_emoji():
        raid_channel = lookup_raid_channel(message)
        if raid_channel:
            # NB: use overwrites for, since admins otherwise won't be notified
            # we know the channel is private and only overwrites matter
            if not raid_channel.overwrites_for(user).is_empty():
                await uninvite_user_from_raid(raid_channel, user)

@client.event
async def on_message(message):
    # we'll need this for future
    server = message.server
    channel = message.channel
    user = message.author
    if user == server.me:
        return

    if channel not in get_raid_channels(server) and is_raid_start_message(message):
        # send the message, then edit the raid to avoid a double notification
        raid_message = await client.send_message(channel, "Looking for open channels...")
        raid_channel = await start_raid_group(user, raid_message, message.clean_content)
        if raid_channel:
            started_dt = adjusted_datetime(raid_message.timestamp)
            expiration_dt = adjusted_datetime(get_raid_expiration(raid_message.timestamp))
            raid_message = await client.edit_message(raid_message,
                                                     '**{}**\n\n**in:** {}'.format(message.content, raid_channel.mention),
                                                     embed=get_raid_start_embed(user, started_dt, expiration_dt))

            # invite the member
            await invite_user_to_raid(raid_channel, user)

            # add a join reaction to the message
            join_emoji = get_join_emoji()
            await client.add_reaction(raid_message, join_emoji)
        else:
            m = await client.edit_message(raid_message, "", embed=get_raid_busy_embed())
            await client.add_reaction(m, get_full_emoji())
    elif is_raid_channel(channel) and message.content.startswith('$leaveraid'):
        await uninvite_user_from_raid(channel, user)
    elif is_raid_channel(channel) and message.content.startswith('$listraid'):
        await list_raid_members(channel)
    elif is_raid_channel(channel) and message.content.startswith('$endraid'):
        is_organizer = [role for role in get_raid_organizer_roles(user.server) if role in user.roles]
        if is_organizer:
            await end_raid_group(channel)
        else:
            creator = await get_raid_creator(channel)
            if user == creator:
                await end_raid_group(channel)
            else:
                await client.send_message(channel, embed=get_error_embed('Only the creator or raid organizer may end the raid.'))


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Pokemon Go discord bot for coordinating raids.")
    parser.add_argument("--token", required=True, default=None, help="The token to use when running the bot.")
    parser.add_argument("--raid-channel-regex", default="^raid-group-.+",
                        help="Pattern which all raid channels must have. (default: %(default)s)")
    # matches if starts with raid- but not raid-group
    parser.add_argument("--raid-start-regex", default="^raid-(?!group).+",
                        help="Regex for role mentions to trigger a raid. (default: %(default)s)")
    parser.add_argument("--raid-duration-seconds", type=int, default=7200,
                        help="Time until a raid group expires, in seconds (default: %(default)s).")
    parser.add_argument("--raid-cleanup-interval-seconds", type=int, default=60,
                        help="Time between checks for cleaning up raids (default: %(default)s)")
    parser.add_argument("--raid-additional-roles", default=[], action='append',
                        help="Additional roles to permission on active raid channels (default: %(default)s)")
    parser.add_argument("--raid-organizer-roles", default=['raid-organizer'], action='append',
                        help="Additional roles to help with coordinating raids (default: %(default)s)")
    parser.add_argument("--raid-join-emoji", default='\U0001F464', help="Emoji used for joining raids (default: %(default)s)")
    parser.add_argument("--raid-leave-emoji", default='\U0001F6AA', help="Emoji used for leaving raids (default: %(default)s)")
    parser.add_argument("--raid-full-emoji", default='\U0001F61F', help="Emoji used for full raid channels (default: %(default)s)")
    parser.add_argument("--time-format", default='%Y-%m-%d %I:%M:%S %p', help="The time format to use. (default: %(default)s)")
    args = parser.parse_args()
    return args


def main():
    global settings
    settings = get_args()
    client.loop.create_task(cleanup_raid_channels())
    client.run(settings.token)

