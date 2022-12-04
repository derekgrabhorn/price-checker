import os
import atexit

from flask import Flask, render_template, request, jsonify, url_for, redirect
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import boto3 

load_dotenv()
app = Flask(__name__)
ses_client = boto3.client(
    "ses",
    aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

URLheaders = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

@app.route('/')
def hello():
    watch_list = []
    prices_file = open(os.getenv('DATA_FILE'), 'r')
    prices_to_check = prices_file.readlines()
    for entry in prices_to_check:
        data = entry.strip().split(' ')
        watch_list.append([data[0], data[1]])
    return render_template('index.html', watch_list=watch_list)

@app.route('/add', methods = ['POST', 'GET'])
def add_price_check():
    if request.method == 'POST':
        result = request.form
        with open(os.getenv('DATA_FILE'), 'a') as write_file:
            write_file.write(result.getlist('URL')[0])
            write_file.write(' ')
            write_file.write(result.getlist('Store')[0])
            write_file.write('\n')
        return redirect('http://127.0.0.1:5000/')
    elif request.method == 'GET':
        return render_template('add.html')

@app.route('/delete', methods = ['POST'])
def delete_entry():
    soupped_href = BeautifulSoup(request.form['URL']).find('a').get('href')
    line_to_delete = get_line_of_entry(soupped_href)
    if line_to_delete:
        remove_line_number(line_to_delete)
        resp = jsonify(success=True)
        return resp
    else:
        resp = jsonify(success=False)
        return resp

def check_prices():
    prices_file = open(os.getenv('DATA_FILE'), 'r')
    prices_to_check = prices_file.readlines()
    for entry in prices_to_check:
        data = entry.split(' ')
        url_to_check = data[0].strip()
        store = data[1].strip().lower()
        raw_page_data = requests.get(url_to_check, headers=URLheaders)
        parsed_page = BeautifulSoup(raw_page_data.text, 'html.parser')
        if store == 'costco':
            parse_costco_data(parsed_page, url_to_check)

def parse_costco_data(soup_data, web_url):
    product_name, merchandisingText, promotionalText = '', '', ''
    for data in soup_data.find_all(attrs={"automation-id":True}):
        product_name = soup_data.find("h1", itemprop="name").get_text()
    for data in soup_data.find_all("p", class_="merchandisingText"):
        merchandisingText = data.get_text()
    for data in soup_data.find_all("p", class_="PromotionalText"):
        promotionalText = data.get_text()
    send_notification(web_url, product_name, merchandisingText)

def get_line_of_entry(url):
    with open(os.getenv('DATA_FILE'),'r') as read_file:
        line_number = 0
        lines = read_file.readlines()
        for line in lines:
            line_number += 1
            if url in line:
                return line_number

def remove_line_number(line_to_skip):
    with open(os.getenv('DATA_FILE'),'r') as read_file:
        lines = read_file.readlines()

    currentLine = 1
    with open(os.getenv('DATA_FILE'),'w') as write_file:
        for line in lines:
            if currentLine == line_to_skip:
                pass
            else:
                write_file.write(line)
	
            currentLine += 1

def send_notification(website, product, information):
    CHARSET = 'utf-8'
    
    try:
        #Provide the contents of the email.
        response = ses_client.send_email(
            Destination={ 'ToAddresses': [os.getenv('TO_EMAIL')] },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': f'Visit {website} for more details.',
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': f'{product} - {information}',
                },
            },
            Source=os.getenv('FROM_EMAIL')
        )
    # Display an error if something goes wrong.	
    except Exception as error:
        print(f'Error sending the email: {error}')
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_prices, trigger="interval", days=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == 'main':
    app.run(host='localhost', port=5000)