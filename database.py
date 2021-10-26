import peewee as pw

db = pw.SqliteDatabase('/data.db')

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
    

@create_table
class TrackedMessage(MyModel):
    tracker = pw.ForeignKeyField(ReactionTracker, index=True)
    posted_at = pw.DateTimeField(index=True)
    reaction_count = pw.IntegerField(default=0, index=True)