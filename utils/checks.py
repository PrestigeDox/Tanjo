from discord.ext import commands


class UserNotDeveloper(commands.CheckFailure):
    pass


def is_dev():
    """ Checks whether a user is a developer of the bot """
    dev_list = [('naught0#4417', 142033635443343360), ('Prestige#9162', 350534218998349825),
                ('Ello#7645', 203819318150955008), ('Demo#9465', 159944239688581120),
                ('NCPlayz#7941', 121678432504512512), ('ﾠ ﾠ#1502', 323578534763298816)]

    async def predicate(ctx):
        if ctx.author.id not in (x[1] for x in dev_list):
            raise UserNotDeveloper('User not in developer list.')
        return True
    return commands.check(predicate)
