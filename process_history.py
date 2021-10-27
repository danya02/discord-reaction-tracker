import discord
import os
from database import *
import datetime

TOKEN = os.getenv('DISCORD_TOKEN')

bot = discord.Client()

class FakeMessage:
    async def edit(self, content=None):
        print(content)

@bot.event
async def on_ready():
    await run_process_history(FakeMessage(), bot)
    await bot.close()


async def run_process_history(status_message, bot):
    old_content = status_message.content
    async def write(*args):
        await status_message.edit(content=old_content+' '+' '.join(map(str, args)))

    await write("Fetching all tracked guilds...")
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
                #print("Fetched guild ID", item.guild_id, "as", repr(guilds[item.guild_id]))
            except:
                await write("Could not fetch guild ID", item.guild_id)
                continue
    for gind, guild in enumerate(guilds):
        guild = guilds[guild]
        channels = await guild.fetch_channels()
        for cind, channel in enumerate(channels):
            if not isinstance(channel, discord.TextChannel):
                #print("Skipping", repr(channel))
                continue
            await write("Processing guild", f"{gind+1}/{len(guilds)},", "channel", f"{cind+1}/{len(channels)}", repr(channel), "0 messages")
            msg_count = 0
            latest_msg_date = datetime.datetime.min
            async for message in channel.history(limit=None, oldest_first=True, after=discord.Object(earliest_messages[guild.id])):
                msg_count += 1
                latest_msg_date = message.created_at
                if (msg_count % 500) == 0:
                    await write("Processing guild", f"{gind+1}/{len(guilds)},", "channel", f"{cind+1}/{len(channels)}", repr(channel), str(msg_count), "messages, latest is at", latest_msg_date.isoformat())
                for tracker in trackers:
                    count = tracker.message_has_reactions_count(message)
                    if not count: continue
                    #print("Message", message, "has", count, "reactions by", repr(tracker))
                    tm, _ = TrackedMessage.get_or_create(tracker=tracker, channel_id=message.channel.id, message_id=message.id)
                    tm.reaction_count = count
                    tm.last_full_update = datetime.datetime.now()
                    tm.content = message.content
                    tm.save()
    await write("Processed all visible messages!")

if __name__ == '__main__':
    bot.run(TOKEN)
