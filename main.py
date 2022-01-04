import logging

from decouple import config
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Updater, Filters

from forms.google_forms import GoogleForms

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

GOOGLE_FORM_ID = config("GOOGLE_FORM_ID")
TOKEN = config("TOKEN")

google_forms = GoogleForms(GOOGLE_FORM_ID)
update = Updater(TOKEN, use_context=True)
dispatcher = update.dispatcher


def welcome(update, context):
    first_name = update.message.from_user.first_name
    reply_keyboard = [["Start"]]
    update.message.reply_text(
        f"👋 *Welcome {first_name}*"
        + """
__This telegram bot is prepared to gather information from Adama Science and Technology University (ASTU) about their programming life while they are students.__


*Objectives*:
_1. Collect information about the students' programming life.
2. Determine the students' interest in programming.
    - Determine the students' programming skills.
    - Determine the students' programming habits.
3. Identifying problem that students when coding.
4. Identifying any skill gap(if there is)._

*NB*:
_- You are giving your data for only educational purpose. 
- You are not allowed to use this bot for any commercial purpose.
- This bot is not affiliated with any organization._""",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Click start button to start",
        ),
    )


def get_question(update, context):
    update.message.reply_text('Well done!', reply_markup=None)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def cancel(update, context):
    update.message.reply_text('I hope I will see you soon.')

conversation_handler = ConversationHandler(
    entry_points = [MessageHandler(Filters.regex(r'^(S|s)(T|t)(A|a)(R|r)(T|t)$'), get_question)],
    states = {},
    fallbacks=[CommandHandler('cancel', cancel)],
)

# Add handlers
dispatcher.add_handler(CommandHandler("start", welcome))
dispatcher.add_handler(conversation_handler)
dispatcher.add_error_handler(error)


update.start_polling()
# update.idle()
