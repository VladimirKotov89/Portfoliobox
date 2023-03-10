import string
from random import choice, shuffle
from pyfiglet import Figlet



def generate_password(length:int):
    """
    Генерирует случайные пароли заданной длины,
    используя буквы в верхнем и нижнем регистре,
    цифры и исключая похожие символы
    (например, 'O' и 'I', 'l' и 'o').

    Аргументы:
    length -- длина пароля (целое число)

    Возвращает:
    строку, содержащую сгенерированный пароль
    """
    letters1 = [с for с in string.ascii_uppercase if с not in 'OI']
    letters2 = [с for с in string.ascii_lowercase if с not in 'ol']
    letters3 = list(string.digits[2:])
    letters4 = [с for с in string.punctuation if с in '!#$%&()*+,-./:;<=>?@[\]_']
    letters = letters1 + letters2 + letters3

    result = [choice(i) for i in (letters1, letters2, letters3, letters4)]
    rs = {i : result.count(i) for i in result}
    while len(result) < length:
        new_char = choice(letters)
        if rs.get(new_char, 0) < 3:
            result.append(new_char)
            rs[new_char] = rs.get(new_char, 0) + 1
    shuffle(result)

    return ''.join(result)

def generate_passwords(count:int, length:int):
    """
    Генерирует заданное количество паролей заданной длины.

    Аргументы:
    count -- количество паролей (целое число)
    length -- длина каждого пароля (целое число)

    Возвращает:
    список строк, содержащих сгенерированные пароли
    """
    result = set()
    while len(result) < count:
        result.add(generate_password(length))
    return list(result)

def main():
    """
    Запрашивает у пользователя длину пароля, генерирует несколько паролей и выводит их на экран.
    """
    font_text = Figlet(font="slant")
    print(font_text.renderText("GENERATE PASSWORDS"))
    for i in generate_passwords(5, int(input('Введите длинну пароля: '))):
        print(i)

if __name__ == "__main__":
    main()
