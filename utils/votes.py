class Votes:

    __slots__ = ['voters', 'for_item']

    def __init__(self, for_item=None):
        self.voters = []
        self.for_item = for_item

    def add_vote(self, user):
        if user not in self.voters:
            self.voters.append(user)
            return True
        else:
            return False

    def is_passed(self, needed):
        if len(self.voters) >= needed:
            return True
        else:
            return False

    @property
    def total_votes(self):
        return len(self.voters)

    @property
    def is_init(self):
        return len(self.voters)


class ActionVotes:

    __slots__ = ['skip', 'jump', 'disconnect']

    def __init__(self):
        self.skip = []
        self.jump = None
        self.disconnect = Votes()
