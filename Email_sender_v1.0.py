import smtplib, ssl
from smtplib import SMTPException, SMTPAuthenticationError
import os
import time
import base64
import shutil
import datetime
import mimetypes
from glob import glob
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
import pandas as pd
from pyfiglet import Figlet
import tkinter as tk
from tkinter import filedialog
import spnego

#==================Функция открытия директории=======================
def select_dir(title_:str, intialdir_:str):
    """Выбор директории с помощью проводника системы

    Args:
        title_ (str): Имя окна проводника
        intialdir_ (str): Начальная дериктория

    Returns:
        str: Путь до дериктории
    """
    root = tk.Tk()
    root.wm_attributes('-topmost', True)
    root.withdraw()
    filepath = filedialog.askdirectory(title=title_, initialdir=intialdir_)
    root.destroy()
    return filepath + "\\"

#==================Функция открытия директории=======================
def open_file(title_:str, intialdir_:str):
    """Выбор файла с помощью проводника системы

    Args:
        title_ (str): Имя окна проводника
        intialdir_ (str): Начальная дериктория

    Returns:
        str: Путь до файла
    """
    root = tk.Tk()
    root.wm_attributes('-topmost', True)
    root.withdraw()
    filepath = filedialog.askopenfilename(title=title_, initialdir=intialdir_)
    root.destroy()
    return filepath

#==================Функция авторизации на почте(взято со stackoverflow)=======================
def ntlm_authenticate(smtp, username, password):
    auth = spnego.client(username, password, service="SMTP", protocol="ntlm")
    ntlm_negotiate = auth.step()

    code, response = smtp.docmd("AUTH", "NTLM " + base64.b64encode(ntlm_negotiate).decode())
    if code != 334:
        raise SMTPException("Server did not respond as expected to NTLM negotiate message")

    # I'm unsure of the format that is returned but if it's like the above this should work
    # This is essentially getting the base64 decoded value of challenge response
    ntlm_challenge = base64.b64decode(response)
    ntlm_auth = auth.step(ntlm_challenge)
    code, response = smtp.docmd("", base64.b64encode(ntlm_auth).decode())
    if code != 235:
        raise SMTPAuthenticationError(code, response)

#====================================Функция прикрепления===================================
def attach_file(msg, file_path, file_name):
    """Функция прикрепления файла к письму

    Args:
        msg : письмо MIMEMultipart()
        file_path (ste): путь до файла
        file_name (str): имя файла
    """
    ftype, encoding = mimetypes.guess_type(file_path)
    file_type, subtype = ftype.split("/")
    if file_type == "application":
        with open(file_path, "rb") as f:
            file = MIMEApplication(f.read(), subtype)
    else:
        with open(file_path, "rb") as f:
            file = MIMEBase(file_type, subtype)
            file.set_payload(f.read())
            encoders.encode_base64(file)
    file.add_header('content-disposition', 'attachment', filename=file_name)
    msg.attach(file)


#=============================Функция отправки письма=========================================
def send_mail( msg_subj, msg_text, path, move_path, to_send, has_sent, df_report):
    """Функция отправки писем

    Args:
        msg_subj (str): Тема письма
        msg_text (str): Текст письма
        path (str): Путь до директории с файлами
        move_path (str): Путь до дериктории куда перемещать отправленные файлы
        to_send (list): Список куда добавляются имя файлов на отправку
        has_sent (list): Список имен файлов отправленных
        df_report (DataFrame): отчетный ДатаФрейм где имя файла и адресс отправления

    Returns:
        to_send (list): Список имен файлов на отправку
        has_sent (list): писок имен файлов отправленных
        df_report (DataFrame): отчетный ДатаФрейм где имя файла и адресс отправления
    """
    sender = "email@mos.ru"                        # Адрес почты с которой будет производится отправка
    username='login'                               # Логин поочты
    password='password'                      # Пароль почты

    # context = ssl.create_default_context()
    try:                                            # Создаем соединение с SMTP сервером
        server = smtplib.SMTP('pochta.mos.ru', 587)
        server.ehlo()
    except Exception as _ex:                        # Выводим ошибку в случае неудачи
        print(f'{_ex}\nCheck connect')
    # server.starttls(context=context)
    # server.ehlo()
    try:                                            # Пробуем авторизаваться на спочтовом сервере
        ntlm_authenticate(server, username, password)
        print('Authorization complate...')
    except Exception as _ex:
        print(f'{_ex}\nCheck your login and password')

    #======================Поиск файлов по папке и отправка================================
    df_adres = pd.read_excel(r"Workflow\Email_sender\adres_book_all.xlsx") # Загружаем адресную книгу в DataFrame
    list_path = glob(path + "\\*.zip")                            # Создаем список полных путей до файлов в папке
    total = 0                                                 # Счетчик отправленных писем нужен чтобы не привышать лимит по одновременной отправке писем
    for file_path in list_path:                               # Цикл для прикрепления фаила и отправки его на нужную почту
        msg = MIMEMultipart()                                 # Создаем письмо
        msg['From'] = sender                                  # Прикрепляем Отправителя к письму
        msg["Subject"] = msg_subj                             # Прикрепляем Тему письма
        msg.attach(MIMEText(msg_text))                        # Прикрепляем Текст письма
        if os.path.isfile(file_path):                         # Проверяем является ли путь файлом или нет
            file_name = os.path.basename(file_path)           # Выделяем из пути название фаила c расширением
            name = file_name.rsplit('.', 1)[0]                # Выделяем имя файла без расширения
            if name in list(df_adres.MO):                     # Находим соответствие имя файла в адресной книги
                idx = df_adres[df_adres['name'] == name].index  # берем индекс из адресной книги
                addr_to = df_adres.at[idx[0] , 'Email']       # Получаем емайл адрес куда отправить
                if pd.notna(addr_to):                         # Если адрес не пустой прикрепляем файл к письму
                    attach_file(msg, file_path, file_name)    
                    addr_to = addr_to.split(', ')             # Если адресов несколько делаем список и по очереди отправляем
                    flag = 0                                  # Счетчик показывающая на то что файл отправлен на все указаные адреса в строке
                    for adress in addr_to:                    
                        msg["To"] = adress                    # Прикрепляем адрес отправления
                        print('Sending...')                   
                        to_send.append(file_name)             # Добавляем имя файла в список на отправление
                        time.sleep(0.5)                       
                        try:
                            server.sendmail(sender, adress , msg.as_string()) # Отправляем письмо
                            print(f'{file_name} sent complete')               #
                            flag += 1                                         # Повышаем счетчики
                            total += 1                                        # 
                            df_report.loc[len(df_report)]=[adress, file_name] # Добавляем в отчетный Датафрейм адрес и имя файла
                        except Exception as _ex:
                            print(f"{_ex}\n{file_name} Not sent...")          # Оповещение в случие если письмо не отправилось
                    if flag == len(addr_to):                                  # Если счетчик равен длинне списка адрессов для файла
                            has_sent.append(file_name)                        # Добавляем имя файла в список отправленных
                            shutil.move( file_path, move_path + '\\' + file_name) # Перемещаем файл из папки на отправление в папку отправленых
                    else:
                        continue
        if total >= 4:                                                        # Если счетчик равен 4 ждем 60 сек
            total = 0                                                         #
            time.sleep(60)                                                    #
            continue
    return to_send, has_sent, df_report

    # except Exception as _ex:
    #     print(f'{_ex}\nCheck your login and password')

# ===================================Основное тело программы=================================
def main():
    #==================================Подготовка=============================================
    font_text = Figlet(font="slant")
    print(font_text.renderText("SEND EMAIL"))
    print('Preparing...')

    path = select_dir('Введите путь до файлов:', 'folder')
    move_path = select_dir("Введите путь куда перемещать отправленные фаилы:", 'folder')
    execution = input('Введите дату исполнения в формате dd.mm.yyyy: ') # в письме указывается срок исполнения

    with open(open_file('Выберете шаблон письма', 'folder'), 'r', encoding='utf-8') as f: # Выбираем шаблон письма
        lines = f.readlines()
        msg_subj = lines[0].strip()[6:]  # извлекаем тему письма
        body = ''.join(lines[1:])  # извлекаем текст письма без первой строки (темы)
    msg_text = body.format(execution=execution) #  В текс письма добавляем дату

    print("Processing...")
    start_time = time.time() # метка для отслеживания времени выполнения программы
    df_report = pd.DataFrame( columns=['Email', 'file_name']) # создаем отчетный Датафрейм
    to_send = [] # создаем список на отправку для проверки
    has_sent = [] # создаем список на отправку для проверки 
    
    send_mail(msg_subj, msg_text, path, move_path, to_send, has_sent, df_report) # отправляем файл
    
    print("Sending messages complete!!!")

    #==============================Проверка отправились ли все письма=================================================
    while len(set(to_send)) != len(set(has_sent)):   # До тех пор пока длинна множества на отправку и множества отправленых не будут равны повторять отправку
        diff = list(set(to_send).difference(set(has_sent)))
        print(diff)
        time.sleep(30)
        send_mail(msg_subj, msg_text, path, move_path, to_send, has_sent, df_report)
        
    print('Everything OK!')
    to_day = datetime.date.today().strftime('%Y-%m-%d') #
    with pd.ExcelWriter('E:\\DZM\\Report_Rassilka\\'+ msg_subj+ '_'+ to_day +'.xlsx', engine = 'xlsxwriter') as writer:
        df_report.to_excel(writer, sheet_name= 'Sheet1', index=False)
        
    print('Report created!')
    print(
        '-- Количество минут затраченых на выполнение: {0:.0f} --'.format((time.time() - start_time)/ 60)
        )

if __name__ == "__main__":
    main()
