from bs4 import BeautifulSoup as bs
import requests
import re
import transliterate as trns
from pymongo import MongoClient as mncl
from pymongo import errors


def get_int(a):
    int_str = ''
    for i in a:
        int_str += i

    return int(int_str)

def get_text_html():

    profession = input('Искать вакансии по профессии: ')
    web_resource = input('HH или SJ 1|2: ')
    if web_resource == '1':
        link = f'https://hh.ru/search/vacancy?area=1&text={profession}&from=suggest_post'
    elif web_resource == '2':
        profession = trns.translit(profession, reversed=True)
        link = f'https://www.superjob.ru/vakansii/{profession}.html?geo%5Bt%5D%5B0%5D=4'
    else:
        print('Не корректно указан web-ресурс')
        return False

    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
    html = requests.get(link, headers=headers)

    return html.text

def wright_text(text, name):

    f = open(name, 'w',  encoding='utf-8')
    f.write(text)
    f.close()

def read_text(name):

    f = open(name,  encoding='utf-8')
    text = f.read()
    f.close()

    return text

def get_compensation_dic(compensation_info, type_site):

    if type_site == 'hh':
        reg1 = r'(\d*) 000-'
        reg2 = r'-(\d*)'
    elif type_site == 'sj':
        reg1 = r'(\d*) 000 —'
        reg2 = r'— (\d*)'

    reg3 = r'(\d*) '

    if compensation_info:

        compensation_info = compensation_info.get_text()

        if compensation_info[:17] != 'По договорённости':

            if compensation_info[-3:] == 'USD':
                course = 66.61
            elif compensation_info[-3:] == 'EUR':
                course = 73.88
            else:
                course = 1

            if compensation_info[:2] == 'от':
                compensation = get_int(re.findall(r'\d*', compensation_info))
                compensation_info_type = 1
                compensation_min = compensation * course
                compensation_max = 1000000

            elif compensation_info[:2] == 'до':
                compensation = get_int(re.findall(r'\d*', compensation_info))
                compensation_info_type = 2
                compensation_min = 0
                compensation_max = compensation * course

            elif compensation_info.find('-') > 0 or compensation_info.find('—') > 0:

                compensation_info_type = 3
                compensation_min = int(re.findall(reg1, compensation_info)[0]) * 1000 * course
                compensation_max = int(re.findall(reg2, compensation_info)[0]) * 1000 * course

            else:

                compensation_info_type = 4
                compensation_min = int(re.findall(reg3, compensation_info)[0]) * 1000 * course
                compensation_max = int(re.findall(reg3, compensation_info)[0]) * 1000 * course

        else:
            compensation_info_type = 0
            compensation_min = 0
            compensation_max = 1000000
    else:
        compensation_info_type = 0
        compensation_min = 0
        compensation_max = 1000000

    return {'compensation_info_type': compensation_info_type,
        'compensation_min': compensation_min,
        'compensation_max': compensation_max}

def get_hh_vacancy_dic(html_text):

    parsed_html = bs(html_text, 'html.parser')
    vacancies = parsed_html.find_all('div', {'class': 'vacancy-serp-item'})

    db_vacancy = get_db()

    for vacncy in vacancies:
        name_block = vacncy.find('a', {'class': 'bloko-link HH-LinkModifier'}, href=True)
        name = name_block.get_text()
        requirement = vacncy.find('div', {'data-qa': 'vacancy-serp__vacancy_snippet_requirement'}).get_text()
        compensation_info = vacncy.find('div', {'class': 'vacancy-serp-item__compensation'})
        compensation_dic = get_compensation_dic(compensation_info, 'hh')
        employer = vacncy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).get_text()
        v_link = name_block['href']
        number_errors = 0

        try:
            db_vacancy.insert_one({'name': name,
                    'requirement': requirement,
                    'compensation_dic': compensation_dic,
                    'employer': employer,
                    'v_link': v_link})

        except errors.DuplicateKeyError:
            number_errors += 1
            print(number_errors)

def get_sj_vacancy_dic(html_text):

    parsed_html = bs(html_text, 'html.parser')
    vacancies = parsed_html.find_all('div', {'class': '_3zucV _2GPIV i6-sc _3VcZr'})

    db_vacancy = get_db()

    for vacncy in vacancies:
        name = vacncy.find('div', {'class': '_3mfro CuJz5 PlM3e _2JVkc _3LJqf'}).get_text()
        requirement = vacncy.find('div', {'class': '_2kyiZ _2XXYS _2cxK3'}).get_text()
        compensation_info = vacncy.find('span', {'class': '_3mfro _2Wp8I f-test-text-company-item-salary PlM3e _2JVkc _2VHxz'})
        compensation_dic = get_compensation_dic(compensation_info, 'sj')
        employer = vacncy.find('span', {'class': '_3mfro _3Fsn4 f-test-text-vacancy-item-company-name _9fXTd _2JVkc _3e53o _15msI'})
        if employer:
            employer = employer.get_text()
        else:
            employer = '-'
        v_link = vacncy.find('a', {'class': '_1QIBo'}, href=True)['href']
        v_link = 'https://www.superjob.ru' + v_link
        number_errors = 0

        try:
            db_vacancy.insert_one({'name': name,
                    'requirement': requirement,
                    'compensation_dic': compensation_dic,
                    'employer': employer,
                    'v_link': v_link})
        except errors.DuplicateKeyError:
            number_errors += 1

def get_db():

    client = mncl('mongodb://127.0.0.1:27017')
    db = client['db_vacancy']
    return db.db_vacancy

#Main programm

# text_html = get_text_html()
# wright_text(text_html, 'hh.txt')

# html_text = read_text('sj.txt')
# get_sj_vacancy_dic(html_text)

html_text = read_text('hh.txt')
get_hh_vacancy_dic(html_text)



