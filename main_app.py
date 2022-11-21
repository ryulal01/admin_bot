import os
import sys
from time import sleep
import telebot
from telebot import types


TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)
try:
	BOT_ID = int(TOKEN.split(':')[0])
except:
	print('Запустите докер через терминал\n'
		  'docker run -e TOKEN=ВАШ_ТОКЕН НАЗВАНИЕ ОБРАЗА')
	print('Программа остановлена')
	sys.exit()
dict_of_messages = {}


def step_user_make_admin(message, call_arrived_from_message_id):
	message_arrived_from_user_id = message.from_user.id
	chat_id = message.chat.id
	if not dict_of_messages.get(
			call_arrived_from_message_id) == message_arrived_from_user_id:
		bot.send_message(chat_id,
						 'Другой пользователь вмешался в диалог, попробуйте заново')
		return
	if message.reply_to_message is None:
		bot.send_message(chat_id,
						 'Попробуйте заново, требуется именно переслать сообщение пользователя'
						 '\nИ оно должно быть после вступления бота')
		return

	list_of_admins_objs = bot.get_chat_administrators(chat_id)
	admins_ids = [admin_obj.user.id for admin_obj in list_of_admins_objs]
	name_to_send = message.reply_to_message.from_user.first_name
	user_id_to_make_admin = message.reply_to_message.from_user.id
	if user_id_to_make_admin in admins_ids:
		bot.send_message(chat_id, 'Пользователь уже админ')
		return

	bot.promote_chat_member(
		chat_id,
		user_id_to_make_admin,
		can_change_info = True,
		can_post_messages = True,
		can_edit_messages = True,
		can_delete_messages = True,
		can_invite_users = True,
		can_restrict_members = True,
		can_pin_messages = True,
		can_promote_members = True,
		can_manage_chat = True)

	bot.send_message(chat_id,
					 f'Сделали админом {name_to_send} ')


def step_user_ban(message, call_arrived_from_message_id):
	message_arrived_from_user_id = message.from_user.id
	chat_id = message.chat.id
	if not dict_of_messages.get(
			call_arrived_from_message_id) == message_arrived_from_user_id:
		bot.send_message(chat_id,
						 'Другой пользователь вмешался в диалог, попробуйте заново')
		return
	if message.reply_to_message is None:
		bot.send_message(chat_id,
						 'Попробуйте заново, требуется именно переслать сообщение пользователя'
						 '\nИ оно должно быть после вступления бота')
		return

	user_id_to_ban_unban = message.reply_to_message.from_user.id
	name_user_to_send = message.reply_to_message.from_user.first_name
	user_status = bot.get_chat_member(chat_id, user_id_to_ban_unban).status
	if user_status == 'kicked':
		if bot.unban_chat_member(chat_id, user_id_to_ban_unban,
								 only_if_banned = True):
			bot.send_message(chat_id,
							 f'Разбанили {name_user_to_send} ')
	elif user_status != 'creator':
		if bot.ban_chat_member(chat_id, user_id_to_ban_unban,
							   99999):
			bot.send_message(chat_id,
							 f'Забанили {name_user_to_send} ')


@bot.message_handler(content_types = ["new_chat_members"])
def new_user_join(message):
	user_id = message.new_chat_members[0].id

	name_to_send = obj_user = message.new_chat_members[0].first_name
	inline_markup = types.InlineKeyboardMarkup()
	for option in range(4):
		inline_markup.row(types.InlineKeyboardButton(
			text = option + 1, callback_data = 'wr')) # wrong
	inline_markup.row(
		types.InlineKeyboardButton(text = '5', callback_data = 'nj_5')) #new joined 5
	msg_id_await_reply = bot.reply_to(message,
									  text = f"Здравствуйте! Пройдите проверку {name_to_send} 2+3?",
									  reply_markup = inline_markup)
	dict_of_messages[msg_id_await_reply.message_id] = user_id


@bot.message_handler(commands = ['admin_commands'])
def admin_commands(message):
	if message.chat.type not in ("group", "supergroup"):
		bot.send_message(chat_id = message.chat.id,
						 text = "Команда может использоваться только в группе")
		return
	call_arrived_from_user_id = message.from_user.id
	list_of_admins_objs = bot.get_chat_administrators(message.chat.id)
	admins_ids = [admin_obj.user.id for admin_obj in list_of_admins_objs]
	# бот админ?
	if BOT_ID not in admins_ids:
		bot.send_message(chat_id = message.chat.id,
						 text = "Бот не является админом")
		return

	if call_arrived_from_user_id not in admins_ids:
		bot.send_message(chat_id = message.chat.id,
						 text = "Вы не являетесь админом")
		return
	user_obj = bot.get_chat_member(message.chat.id, message.from_user.id)
	admin_inline_markup = types.InlineKeyboardMarkup()
	if user_obj.can_promote_members or user_obj.status == 'creator':
		option_make_admin = types.InlineKeyboardButton(
			text = 'Сделать админом участника', callback_data = 'm_a')
		admin_inline_markup.row(option_make_admin)
	if user_obj.can_restrict_members or user_obj.status == 'creator':
		option_ban_unban = types.InlineKeyboardButton(
			text = 'Забанить/разбанить участника', callback_data = 'b_unb')
		admin_inline_markup.row(option_ban_unban)
	if user_obj.can_manage_chat or user_obj.status == 'creator':
		option_get_statics = types.InlineKeyboardButton(
			text = 'Получить статистику по чату', callback_data = 'g_s')
		admin_inline_markup.row(option_get_statics)
	if user_obj.can_change_info or user_obj.status == 'creator':
		option_bot_exit_from_chat = types.InlineKeyboardButton(
			text = 'Боту требуется покинуть чат', callback_data = 'b_ex')
		admin_inline_markup.row(option_bot_exit_from_chat)

	msg_id_await_reply = bot.send_message(chat_id = message.chat.id,
										  text = "Какую команду выбираете?",
										  reply_markup = admin_inline_markup)
	dict_of_messages[msg_id_await_reply.message_id] = call_arrived_from_user_id


@bot.callback_query_handler(func = lambda call: True)
def answer(call):
	call_arrived_from_user = call.from_user.id
	call_arrived_from_message_id = call.message.message_id
	name_to_send = obj_user = call.from_user.first_name
	print(call.data)
	print(call)
	if call.data == 'nj_5' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		dict_of_messages.pop(call_arrived_from_message_id, None)
		bot.send_message(call.message.chat.id,
						 f"Правильный ответ {name_to_send}")
	elif call.data == 'wr' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		dict_of_messages.pop(call_arrived_from_message_id, None)
		bot.send_message(call.message.chat.id,
						 f"{name_to_send} Прислал неверный ответ и будет исключен ")
		bot.ban_chat_member(call.message.chat.id, call_arrived_from_user,
							3600)
	elif call.data == 'wr' or call.data == 'nj_5':
		bot.send_message(call.message.chat.id,
						 f"Кнопки для другого пользователя")
	if call.data == 'g_s' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		dict_of_messages.pop(call_arrived_from_message_id, None)
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		bot.send_message(call.message.chat.id,
						 f'Статистика по чату \nВсего участников: {bot.get_chat_members_count(call.message.chat.id)}\nВсего админов: {len(bot.get_chat_administrators(call.message.chat.id))}')
	if call.data == 'b_ex' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		dict_of_messages.pop(call_arrived_from_message_id, None)
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		bot.send_message(call.message.chat.id,
						 """Бот покидает чат, зовите еще!""")
		bot.leave_chat(call.message.chat.id)
	if call.data == 'm_a' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		msg = bot.send_message(call.message.chat.id,
							   """Перешлите сообщение пользователя и мы сделаем его админом""")
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		bot.register_next_step_handler(msg, step_user_make_admin,
									   call_arrived_from_message_id)
	if call.data == 'b_unb' and dict_of_messages.get(
			call_arrived_from_message_id) == call_arrived_from_user:
		msg = bot.send_message(call.message.chat.id,
							   """Перешлите сообщение пользователя и мы его забаним/разбаним""")
		bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
		bot.register_next_step_handler(msg, step_user_ban,
									   call_arrived_from_message_id)

	bot.answer_callback_query(call.id)
bot.enable_save_next_step_handlers(delay = 2)
bot.load_next_step_handlers()


while True:
	try:
		bot.polling(none_stop = True)
	except Exception as e:
		print(e)
		sleep(15)
