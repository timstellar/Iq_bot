import telebot
import mysql.connector
import random
import time    
import datetime

bot = telebot.TeleBot("YOUR_TOKEN")

dialogs = {
	"start": "Привет, это IQ bot.\nДоступные команды:\n/start, /help - вывод этого сообщения,\n/iq - прибавляет или убавляет ваш IQ от 1 до 10,\n /iqstats - вывод топа гениев этого чата.",
	"iqUp": [
		", ты посмотрел в окно и повысил свой IQ на ",
		", ты сыграл в шахматы с голубем и повысил свой IQ на ",
		", ты просто проснулся и повысил свой IQ на ",
		", ты посмотрел домашнее задание и повысил свой IQ на ",
		", ты посмотрел новости и повысил свой IQ на "
	],
	"iqDown": [
		", ты посмотрел лайфхаки от трум трум и твой IQ понизился на ",
		", пока ты отбивался от насекомых твой IQ понизился на ",
		", пока ты разрабатывал новую систему заработка твой IQ понизился на ",
		", ты зашёл в Доту и твой IQ понизился на ",
		", тебе дали подзатыльник и твой IQ понизился на "
	],
	"iq": ", ты ничего не делал, и твой IQ остался ",
	"iqCurrent": "Сейчас твой IQ составляет ",
	"iqTop": "Твоё место в топе: ",
	"tryPlay": ", ты уже играл.\n Попробуй через "
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, dialogs["start"])

mydb = mysql.connector.connect(
  host="your_host",
  user="your_user",
  password="your_password",
  database="your_database"
)

tables = mydb.cursor()

def setTime (time):
	if (time < 10):
		time = "0" + str(time)
	return str(time)

def setDB (name):
	res = ""
	if (name < 0):
		res = "m" + str(name)[1:]
	else:
		res = str(name)
	return "b" + res

def setIQMessage (message, iq):
	dialog = dialogs["iq"]
	if (iq > 0):
		dialog = dialogs["iqUp"][random.randint(0, 4)]
	elif (iq < 0):
		dialog = dialogs["iqDown"][random.randint(0, 4)]

	sql = "SELECT name, iq FROM `" + setDB(message.chat.id) + "` ORDER BY iq DESC"
	tables.execute(sql)
	result = tables.fetchall()
	topPlace = 1
	currentIQ = iq
	for item in result:
		if (item[0] == str(message.from_user.id)):
			currentIQ = item[1]
			break
		topPlace += 1

	return message.from_user.first_name + dialog + str(iq) + ".\n" + dialogs["iqCurrent"] + str(currentIQ) + ".\n" + dialogs["iqTop"] + str(topPlace) + "."

def createDB(message):
	sql = "CREATE TABLE " + setDB(message.chat.id) + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), iq INT NOT NULL DEFAULT '0', updateTime TIMESTAMP)"
	tables.execute(sql)

@bot.message_handler(commands=['iq'])
def send_welcome(message):
	mydb.connect()
	tables.execute("SHOW TABLES")
	res = tables.fetchall()
	if (len(res)):
		isFound = False
		for i in res:
			if (i[0] == setDB(message.chat.id)):
				response = ""
				sql = "SELECT name, iq, updateTime FROM `" + setDB(message.chat.id) + "` WHERE name=" + str(message.from_user.id)
				tables.execute(sql)
				result = tables.fetchall()
				if (len(result)):
					last = datetime.datetime.now() - result[0][2]
					wait = datetime.timedelta(hours=23, minutes=59, seconds=59) - last
					time.sleep(1)
					response = message.from_user.first_name + dialogs["tryPlay"] + setTime(wait.seconds // 3600) + ":" + setTime((wait.seconds // 60) % 60) + ":" + setTime(wait.seconds % 60)
					if (last.days):
						iq = random.randint(-9, 10)
						sql = "UPDATE " + setDB(message.chat.id) + " SET iq='" + str(int(result[0][1]) + iq) + "', updateTime='" + time.strftime('%Y-%m-%d %H:%M:%S') + "' WHERE name=" + str(message.from_user.id)
						tables.execute(sql)
						mydb.commit()
					else:
						bot.reply_to(message, response)
						break
				else:
					iq = random.randint(-9, 10)
					sql = "INSERT INTO " + setDB(message.chat.id) + " (`name`, `iq`, `updateTime`) VALUES ('" + str(message.from_user.id) + "', '" + str(iq) + "', '" + time.strftime('%Y-%m-%d %H:%M:%S') + "')"
					tables.execute(sql)
					mydb.commit()
				
				sql = "SELECT iq FROM `" + setDB(message.chat.id) + "` WHERE name=" + str(message.from_user.id)
				tables.execute(sql)
				result = tables.fetchall()

				response = setIQMessage(message, iq)
				isFound = True
				bot.reply_to(message, response)
				break
		if (not isFound):
			createDB(message)
	else:
		createDB(message)
	mydb.close()

@bot.message_handler(commands=['iqstats'])
def send_welcome(message):
	mydb.connect()
	tables.execute("SHOW TABLES")
	res = tables.fetchall()
	if (len(res)):
		isFound = False
		for i in res:
			if (i[0] == setDB(message.chat.id)):	
				sql = "SELECT name, iq FROM `" + setDB(message.chat.id) + "` ORDER BY iq DESC"
				tables.execute(sql)
				result = tables.fetchall()
				response = "Гении этого чата:\n"
				index = 1
				isExists = False
				for item in result:
					isExists = True
					username = str(bot.get_chat_member(message.chat.id, int(item[0])).user.first_name)
					if (not username):
						continue
					response += str(index) + ") " + username + ": " + str(item[1]) + " IQ\n"
					index += 1
				if (not isExists):
					response = "Гениев в этом чате пока нет :("
				bot.reply_to(message, response)
				isFound = True
				break
		if (not isFound):
			createDB(message)
	else:
		createDB(message)
	
	mydb.close()

mydb.close()

bot.infinity_polling()
