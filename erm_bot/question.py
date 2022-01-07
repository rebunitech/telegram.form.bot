import json

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.utils.helpers import escape_markdown


class QuestionType:
    (NUMBER, INLINE_CHOICE, BUTTON_CHOICE, TEXT, RANGE, MULTIPLE) = range(6)


class Question:
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.setup()

    def setup(self):
        if self.type == QuestionType.MULTIPLE:
            self.selected = 0
            self.choices.append(["Done"])
            self.selected_choice = []

    def _get_number_markup(self):
        MIN, MAX = self.min, self.max
        if MIN is not None and MAX is not None and MAX - MIN < 10:
            inlines = []
            for i in range(MIN, MAX + 1, 3):
                group = []
                for j in range(i, i + 3):
                    if j > MAX:
                        break
                    group.append(InlineKeyboardButton(j, callback_data=j))
                inlines.append(group)
            return InlineKeyboardMarkup(inlines)

    def _get_inline_choice(self):
        lines = []
        for row in self.choices:
            line = []
            for item in row:
                line.append(InlineKeyboardButton(item, callback_data=str(item)))
            lines.append(line)
        return InlineKeyboardMarkup(lines)

    def get_markup(self):
        if self.type == QuestionType.NUMBER:
            return self._get_number_markup()

        if (
            self.type == QuestionType.INLINE_CHOICE
            or self.type == QuestionType.MULTIPLE
        ):
            return self._get_inline_choice()

    def validate(self, value):
        if self.type == QuestionType.NUMBER:
            return self._validate_as_number(int(value))
        if self.type == QuestionType.INLINE_CHOICE:
            return self._validate_as_inline_choice(value)
        if self.type == QuestionType.TEXT:
            return self._validate_as_text(value)
        if self.type == QuestionType.RANGE:
            return self._validate_as_range(int(value))
        if self.type == QuestionType.MULTIPLE:
            return self._validate_as_multiple(value)

    def _validate_as_text(self, value):
        return (True, value)

    def _validate_as_number(self, value):
        if self.min is not None and value < self.min:
            return (False, f"The number must be greater than or equal to {self.min}.")
        if self.max is not None and value > self.max:
            return (False, f"The number must be less than or equal to {self.max}.")
        return (True, value)

    def _validate_as_inline_choice(self, value):
        all_choices = []
        for row in self.choices:
            for c in row:
                all_choices.append(c)
        if value in all_choices:
            return (True, value)
        return ("False", "Invalid Option")

    def _validate_as_range(self, value):
        MIN, MAX = self.range
        if value < MIN or value > MAX:
            return (False, f"{value} not in range [{MIN}, {MAX}].")
        return (True, value)

    def _validate_as_multiple(self, value):
        return (True, value)

    def get_text(self):
        return f"*{escape_markdown('#.' + self.text, version=2)}*"

    def get_description(self):
        if self.description is not None:
            desc = escape_markdown("\n\n * " + self.description, version=2)
            return f"_{desc}_"
        return ""

    @property
    def has_note(self):
        return self.type in [
            QuestionType.RANGE,
            QuestionType.MULTIPLE,
            QuestionType.NUMBER,
        ]

    def get_note(self):
        if self.has_note:
            if self.type == QuestionType.RANGE:
                MIN, MAX = self.range
                return (
                    f"\n\n`{' ' * 7}`*{MIN}* {'▫️'* 5} *{MAX}*\n\n"
                    + f"`{MIN}` \- `{escape_markdown(self.min_description, version=2)}`\n"
                    + f"`{MAX}` \- `{escape_markdown(self.max_description, version=2)}`"
                )

            elif self.type == QuestionType.MULTIPLE:
                note = ""
                if self.limit is not None:
                    note += f"\n\t_maximum choice: `{self.limit}`_\n\n"
                if self.allow_other:
                    note += f"\n\t*Write if other option exists\.*\n\n"
                return note
            elif self.type == QuestionType.NUMBER and self.get_markup() is None:
                return f"\n`{'-' * 20}`\n_ Enter a number between_ `{self.min}` _and_ `{self.max }`\."
        return ""

    def get_required(self):
        if not self.required:
            return "\n\n /skip this question"
        return ""


class QuestionSet:
    def __init__(self, file):
        self.questions = {}
        data = json.load(open(file, "r"))
        for item in data:
            q = Question(**item)
            self.questions[q.id] = q

    def get_question(self, q_id):
        return self.questions.get(q_id, False)

    def __iter__(self):
        return iter(self.questions.values())
