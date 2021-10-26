import discord
import asyncio
import os
from database import *

import logging
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

bot = discord.Client()

async def run_top_analysis():
    pass  # TODO: implement

@bot.event
async def on_raw_message_delete(payload):
    TrackedMessage.delete().where(TrackedMessage.message_id==payload.message_id).execute()

@bot.event
async def on_raw_bulk_message_delete(payload):
    TrackedMessage.delete().where(TrackedMessage.message_id.in_(list(payload.message_ids))).execute()

@bot.event
async def on_raw_reaction_add(payload):
    emoji = payload.emoji
    try:
        if emoji.is_unicode_emoji():
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_str==emoji.name).get()
        else:
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_id==emoji.id).get()
    except ReactionTracker.DoesNotExist:
        return
    msg = TrackedMessage.get_or_create(tracker=rt, channel_id=payload.channel_id, message_id=payload.message_id)
    TrackedMessage.update(reaction_count=TrackedMessage.reaction_count+1).where(TrackedMessage.message_id==payload.message_id).execute()
    await run_top_analysis()

@bot.event
async def on_raw_reaction_remove(payload):
    emoji = payload.emoji
    try:
        if emoji.is_unicode_emoji():
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_str==emoji.name).get()
        else:
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_id==emoji.id).get()
    except ReactionTracker.DoesNotExist:
        return

    TrackedMessage.update(reaction_count=TrackedMessage.reaction_count-1).where(TrackedMessage.message_id==payload.message_id).where(TrackedMessage.tracker == rt).execute()
    await run_top_analysis()


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start(TOKEN))
