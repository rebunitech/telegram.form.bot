import json
import logging
import traceback
from collections import defaultdict

from decouple import config
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageFilter,
                          MessageHandler, Updater)
from telegram.utils.helpers import escape_markdown

from erm_bot.configuration import Setup
from erm_bot.filters import int_filter
from erm_bot.google_forms import GoogleForms
from erm_bot.question import QuestionSet, QuestionType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s | %(funcName)s"
)
logger = logging.getLogger()

GOOGLE_FORM_ID = config("GOOGLE_FORM_ID")
TOKEN = config("TOKEN")
CONFIG_FILE = config("CONFIG_FILE", default="data/config.json")
QUESTION_FILE = config("QUESTION_FILE", default="data/questions.json")


google_forms = GoogleForms(GOOGLE_FORM_ID)
configuration = Setup(CONFIG_FILE)
question_set = QuestionSet(QUESTION_FILE)
update = Updater(TOKEN, use_context=True)
dispatcher = update.dispatcher


class Rebuni:
    @classmethod
    def welcome(cls, update, context):
        first_name = update.message.from_user.first_name
        reply_keyboard = [
            [InlineKeyboardButton("✅ Agree and continue", callback_data="start")]
        ]
        update.message.reply_text(
            f"👋 *Welcome {first_name}*" + configuration.welcome_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
        return 1

    @classmethod
    def get_question(cls, update, context):
        question_id = context.user_data.get("question_id")
        question = question_set.get_question(question_id)

        q_text = question.get_text()
        q_decription = question.get_description()
        q_note = question.get_note()
        q_required = question.get_required()
        q_markup = question.get_markup()

        q_message = q_text + q_decription + q_note + q_required
        message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=q_message,
            parse_mode="MarkdownV2",
            reply_markup=q_markup,
        )

        context.user_data["messages"][question_id] = message.message_id
        return question_id + 1

    @classmethod
    def accept_and_continue(cls, update, context):
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=configuration.accepted_message + "\n\nPress /cance to cancel.", parse_mode="Markdown"
        )
        context.user_data["question_id"] = 1
        context.user_data["answers"] = {}
        context.user_data["messages"] = {}
        return cls.get_question(update, context)

    @classmethod
    def error(cls, update, context):
        logger.warning('Update "%s" caused error "%s"', update, context.error)
        traceback.print_exc()

    @classmethod
    def cancel(cls, update, context):
        update.message.reply_text("I hope I will see you soon.")
        return ConversationHandler.END

    @classmethod
    def done(cls, update, context):
        # Clear answer and reset question
        question_set = QuestionSet(QUESTION_FILE)
        question_id = context.user_data["question_id"]
        message_id = context.user_data["messages"][question_id]
        json.dump(context.user_data["answers"], open("ans.json", "w"), indent=4)
        context.bot.edit_message_text(
            configuration.accepted_message
            + "*\n\nYou are successfuly complete our survy\.\n\nPlease* /start *to start again*",
            chat_id=update.effective_chat.id,
            message_id=message_id,
            parse_mode="MarkdownV2",
        )
        return ConversationHandler.END

    @classmethod
    def next_question(cls, update, context):
        context.user_data["question_id"] += 1
        return cls.get_question(update, context)

    @classmethod
    def skip_question(cls, update, context):
        question_id = context.user_data["question_id"]
        question = question_set.get_question(question_id)
        message_id = context.user_data["messages"][question_id]
        context.bot.edit_message_text(
            "*" + escape_markdown("🔰#." + question.text, version=2) + "*",
            chat_id=update.effective_chat.id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=None,
        )
        return cls.next_question(update, context)

    @classmethod
    def generate_handlers(cls):
        states = {1: [CallbackQueryHandler(Rebuni.accept_and_continue)]}
        for question in question_set:
            state_id = question.id + 1
            states[state_id] = []
            if question.get_markup() is not None:
                if question.type == QuestionType.INLINE_CHOICE and question.last:
                    states[state_id].append(CallbackQueryHandler(cls.done))
                else:
                    states[state_id].append(
                        CallbackQueryHandler(cls.save_and_continue),
                    )
            if question.type == QuestionType.TEXT:
                states[state_id].append(
                    MessageHandler(
                        Filters.text & ~Filters.command, cls.save_and_continue
                    )
                )
            if question.type in [QuestionType.RANGE, QuestionType.NUMBER]:
                states[state_id].append(
                    MessageHandler(int_filter, cls.save_and_continue)
                )
            if question.type == QuestionType.MULTIPLE and question.allow_other:
                states[state_id].append(
                    MessageHandler(
                        Filters.text & ~Filters.command, cls.save_and_continue
                    )
                )
            if not question.required:
                states[state_id].append(CommandHandler("skip", cls.skip_question))
        return states

    @classmethod
    def _save_multiple(cls, update, context, question, response, message_id):
        pass

    @classmethod
    def save_answer(cls, update, context, question, response, message_id):
        if question.type == QuestionType.MULTIPLE:
            return cls.next_question(update, context)
            # return cls._save_multiple(update, context, question, response, message_id)
        else:
            context.user_data["answers"][question.id] = response
            context.bot.edit_message_text(
                "*" + escape_markdown("✅#." + question.text, version=2) + "*",
                chat_id=update.effective_chat.id,
                message_id=message_id,
                parse_mode="MarkdownV2",
                reply_markup=None,
            )
            return cls.next_question(update, context)

    @classmethod
    def save_and_continue(cls, update, context):
        question_id = context.user_data["question_id"]
        question = question_set.get_question(question_id)

        query = update.callback_query
        if query:
            query.answer()
        value = query.data if query else update.message.text

        is_valid, response = question.validate(value)
        if is_valid:
            message_id = context.user_data["messages"][question_id]
            return cls.save_answer(update, context, question, response, message_id)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*{escape_markdown(response + ' Please Try Again!', version=2)}*",
            parse_mode="MarkdownV2",
        )

        """
        if is_valid:
            context.user_data["answers"][question_id] = data
            message_id = context.user_data["messages"][question_id]

            if question.type == QuestionType.MULTIPLE:
                if data != "Done":
                    question.selected += 1
                    if [data] in question.choices:
                        question.choices.remove([data])
                    question.selected_choice.append(data)
                    if (
                        question.limit is not None
                        and question.selected < question.limit
                    ) or (question.limit is None and len(question.choices) > 0):
                        if query is not None:
                            query.delete_message()
                        return cls.get_question(update, context)
                elif question.required and question.selected < 1:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{escape_markdown('This field is required.' + ' Please Try Again!', version=2)}",
                        parse_mode="MarkdownV2",
                    )
                    return question_id

            context.bot.edit_message_text(
                "*" + escape_markdown("✅#." + question.text, version=2) + "*",
                chat_id=update.effective_chat.id,
                message_id=message_id,
                parse_mode="MarkdownV2",
                reply_markup=None,
            )
            return cls.next_question(update, context)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*{escape_markdown(data + ' Please Try Again!', version=2)}*",
            parse_mode="MarkdownV2",
        )"""


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", Rebuni.welcome)],
    states=Rebuni.generate_handlers(),
    fallbacks=[CommandHandler("cancel", Rebuni.cancel)],
)

# Add handlers
dispatcher.add_handler(conversation_handler)
dispatcher.add_error_handler(Rebuni.error)

if __name__ == "__main__":
    update.start_polling()
    update.idle()
