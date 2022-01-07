from telegram.ext import MessageFilter


class IntegerFilter(MessageFilter):
    def filter(self, message):
        if message.text is None:
            return False
        return message.text.isdigit() or message.text.lstrip("-").isdigit()


int_filter = IntegerFilter()
