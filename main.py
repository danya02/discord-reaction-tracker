import discord
from discord.ext import commands
import asyncio
import os
from database import *
import traceback
import time

from process_history import run_process_history

import logging
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='#')

async def run_top_analysis():
    for tracker in ReactionTracker.select().iterator():
        try:
            top_message = TrackedMessage.select().where(TrackedMessage.tracker == tracker).order_by(-TrackedMessage.reaction_count, -TrackedMessage.message_id).get()
        except TrackedMessage.DoesNotExist:
            tracker.top_message = None
            tracker.save()
            continue

        if top_message.id != tracker.last_top_reacted_message_id:
            tracker.last_top_reacted_message_id = top_message.id
            tracker.save()
            since_last_notification = time.time() - tracker.last_sent_notification_at_unix_time
            if since_last_notification >= tracker.notification_cooldown:
                tracker.last_sent_notification_at_unix_time = int(time.time())
                tracker.save()
                guild = bot.get_guild(tracker.guild_id) or await bot.fetch_guild(tracker.guild_id)
                channel = guild.get_channel(top_message.channel_id)
                top_msg_partial = channel.get_partial_message(top_message.message_id)
                await top_msg_partial.reply(f"This message is now the {tracker.adjective_super} {tracker.single_event_name} in this server, with {top_message.reaction_count} reactions.", mention_author=False)


@bot.command()
async def analyze_top(ctx):
    msg = await ctx.send("Running top analysis...")
    try:
        await run_top_analysis()
        await msg.edit(content="Top analysis done.")
    except:
        await msg.edit(content="Error:\n\n```\n" + traceback.format_exc() + "\n```")


@bot.command()
async def process_history(ctx):
    status_msg = await ctx.send("Processing all visible history...")
    try:
        await run_process_history(status_msg, bot)
    except:
        await status_msg.edit(content="An error occurred:\n```\n" + traceback.format_exc() + "\n```")


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
    TrackedMessage.update(reaction_count=TrackedMessage.reaction_count+1).where(TrackedMessage.message_id==payload.message_id).where(TrackedMessage.tracker == rt).execute()
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

@bot.event
async def on_raw_reaction_clear(payload):
    TrackedMessage.delete().where(TrackedMessage.message_id==payload.message_id).execute()

@bot.event
async def on_raw_reaction_clear_emoji(payload):
    emoji = payload.emoji
    try:
        if emoji.is_unicode_emoji():
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_str==emoji.name).get()
        else:
            rt = ReactionTracker.select().where(ReactionTracker.guild_id == payload.guild_id).where(ReactionTracker.emoji_id==emoji.id).get()
    except ReactionTracker.DoesNotExist:
        return
    TrackedMessage.delete().where(TrackedMessage.tracker == rt).where(TrackedMessage.message_id==payload.message_id).execute()

@bot.event
async def on_raw_message_delete(payload):
    TrackedMessage.delete().where(TrackedMessage.message_id==payload.message_id).execute()

@bot.event
async def on_raw_bulk_message_delete(payload):
    TrackedMessage.delete().where(TrackedMessage.message_id.in_(list(payload.message_ids))).execute()

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start(TOKEN))
