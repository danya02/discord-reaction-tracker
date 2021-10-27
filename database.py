import peewee as pw

db = pw.SqliteDatabase('./data.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls

@create_table
class ReactionTracker(MyModel):
    guild_id = pw.BigIntegerField(null=True)
    emoji_str = pw.CharField(null=True)
    emoji_id = pw.BigIntegerField(null=True)
    article = pw.CharField(default='', help_text='Article to use for referring to a single instance of the condition involved, i.e. "A message that has the {emoji_str} reaction is called {article} {single_event_name}"')
    single_event_name = pw.CharField(help_text='Name for a single instance of the condition involved, i.e. "This message has the most {emoji_str} reactions, it is now the {adjective_super} {single_event_name}."')
    plural_event_name = pw.CharField(help_text='Name for a group of instances: "{adjective_norm} {plural_event_name} of all time"')
    adjective_norm = pw.CharField(help_text='Adjective describing the instances with many reactions, like "top", "hot" or "cool"')
    adjective_comp = pw.CharField(help_text='Comparative form of the adjective: "higher", "hotter", "cooler"')
    adjective_super = pw.CharField(help_text='Superlative form of the adjective: "top", "hottest", "coolest"')
    
    last_sent_notification_at_unix_time = pw.IntegerField(default=0)
    notification_cooldown = pw.IntegerField(default=300)
    last_top_reacted_message_id = pw.IntegerField(null=True)  # refers to the TrackedMessage table, but is not a foreign key, because this is allowed to dangle.

    def message_has_reactions_count(self, message):
        count = 0
        for reaction in message.reactions:
            if isinstance(reaction.emoji, str):
                if reaction.emoji == self.emoji_str:
                    count += reaction.count
            else:
                if reaction.emoji.id == self.emoji_id:
                    count += reaction.count
        return count

@create_table
class TrackedMessage(MyModel):
    tracker = pw.ForeignKeyField(ReactionTracker, index=True)
    channel_id = pw.BigIntegerField(index=True)
    message_id = pw.BigIntegerField(index=True)
    # no timestamp, because that can be derived from message_id
    reaction_count = pw.IntegerField(default=0, index=True)
    last_full_update = pw.DateTimeField(null=True, index=True)
    content = pw.TextField(null=True)
