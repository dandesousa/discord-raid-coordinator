import asyncio
import discord

settings = None
client = discord.Client()

POSSIBLE_RAID_CHANNELS = [
    'pallet-town',
    'viridian-city',
    'cerulean-city',
    'vermillion-city',
    'lavender-town',
    'celadon-city',
    'fuschia-city',
    'saffron-city',
    'cinnabar-island',
    'new-bark-town',
    'cherrygrove-city',
    'violet-city',
    'azalea-town',
    'goldenrod-city',
    'ecruteak-city',
    'olivine-city',
    'cianwood-city',
    'mahogany-town',
    'blackthorn-city',
]

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user.name))
    print('------')

    # check channels that exist
    for server in client.servers:
        for channel_stub in POSSIBLE_RAID_CHANNELS:
            channel_name = "{}{}".format(settings.raid_channel_prefix, channel_stub)
            channel = discord.utils.find(lambda c: c.name == channel_name, server.channels)

            # if channel doesn't exist, add it
            if channel:
                print("found: {}".format(channel.name))
            else:
                print("not found: {}".format(channel_name))

            # if channel is missing create it with the right permissions

            # NB: differential change of perms by detecting and correcting each one.


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Pokemon Go administration bot")
    parser.add_argument("--token", required=True, default=None, help="The token to use when running the bot.")
    parser.add_argument("--raid-bot-role", default='raid-bot', help="The role for the raid bot (default: %(default)s).")
    parser.add_argument("--raid-channel-prefix", default='raid-group-', help="Prefix for raid channels (default: %(default)s).")
    args = parser.parse_args()
    return args


def main():
    global settings
    settings = get_args()
    client.run(settings.token)
