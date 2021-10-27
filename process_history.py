import discord
import os
from database import *
import datetime

TOKEN = os.getenv('DISCORD_TOKEN')

bot = discord.Client()

@bot.event
async def on_ready():
    print("Client ready, fetching all tracked guilds...")
    guilds = {}
    earliest_messages = {}
    trackers = []
    for item in ReactionTracker.select().iterator():
        trackers.append(item)
        if item.emoji_str:
            earliest_messages[item.guild_id] = 0
        else:
            earliest_messages[item.guild_id] = min(earliest_messages.get(item.guild_id, float('inf')), item.emoji_id)
        if item.guild_id not in guilds:
            try:
                guilds[item.guild_id] = await bot.fetch_guild(item.guild_id)
                print("Fetched guild ID", item.guild_id, "as", repr(guilds[item.guild_id]))
            except:
                print("Could not fetch guild ID", item.guild_id)
                continue
    for guild in guilds:
        guild = guilds[guild]
        for channel in (await guild.fetch_channels()):
            if not isinstance(channel, discord.TextChannel):
                print("Skipping", repr(channel))
                continue
            print("Processing channel", repr(channel))
            msg_count = 0
            async for message in channel.history(limit=None, oldest_first=True, after=discord.Object(earliest_messages[guild.id])):
                msg_count += 1
                if (msg_count % 100) == 0:
                    print("Processed", msg_count, "messages")
                for tracker in trackers:
                    count = tracker.message_has_reactions_count(message)
                    if not count: continue
                    print("Message", message, "has", count, "reactions by", repr(tracker))
                    tm, _ = TrackedMessage.get_or_create(tracker=tracker, channel_id=message.channel.id, message_id=message.id)
                    tm.reaction_count = count
                    tm.last_full_update = datetime.datetime.now()
                    tm.save()
    print("Processed all, exiting")
    await bot.close()

bot.run(TOKEN)
