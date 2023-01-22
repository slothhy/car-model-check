
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert

from scrapy import Selector
import base64
import re

import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT = os.environ.get("TELEGRAM_BOT")

def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    image = vision.Image(content=path)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')

    for text in texts:
        print('\n"{}"'.format(text.description))
        return(text.description)


    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
                
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Checking, one moment.")
    vehiclemodel = await browsercheck(context, update.effective_chat.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=vehiclemodel)

def sendImage(image, chat_id):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT}/sendPhoto';
    files = {'photo': base64.decodebytes(image.encode('utf-8'))}
    data = {'chat_id' : chat_id}
    r= requests.post(url, files=files, data=data)
    print(r.status_code, r.reason, r.content)

async def browsercheck(context, chat_id):
    carplate = context.args[0]
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    d = driver.get("https://vrl.lta.gov.sg/lta/vrl/action/pubfunc?ID=EnquireRoadTaxExpDtProxy")
    # time.sleep(10)

    print(driver.page_source)
    if "System Maintenance in Progress" in driver.page_source:
        return("System maintenance in progress.")

    try:
        alert = Alert(driver)
        alert.accept()
    except:
        print("No alerts")
    
    captchaform = driver.find_element("xpath", '/html/body/section/div[3]/div[4]/div[2]/div[2]/form/div[2]/div/div/input[1]').get_attribute("value")
    print(f'captchaform: {captchaform}')

    captchatoken = driver.find_element("xpath", '/html/body/section/div[3]/div[4]/div[2]/div[2]/form/input[1]').get_attribute("value")
    print(f'captchatoken: {captchatoken}')
    iframe = driver.find_element("xpath", '/html/body/section/div[3]/div[4]/div[2]/div[2]/form/div[2]/div/iframe')
    driver.switch_to.frame(iframe)
  
    captchadata = driver.find_element(By.XPATH, "/html/body/img").get_attribute("src").split(",")[1]
    
    print(f'captchadata: {captchadata}')

    windowID = driver.execute_script("return sessionStorage.getItem('windowID')")

    sendImage(captchadata, chat_id)
    # call api
    captchatext = detect_text(captchadata)
    await context.bot.send_message(chat_id, text=captchatext)

    request_cookies_browser = driver.get_cookies()

    session = requests.Session()
    for cookie in request_cookies_browser:
        session.cookies.set(cookie['name'], cookie['value'], path=cookie['path'])

    url = f'https://vrl.lta.gov.sg/lta/vrl/action/enquireRoadTaxExpDtProxy?FUNCTION_ID={captchaform}'

    payload=f'org.apache.struts.taglib.html.TOKEN={captchatoken}&dispatch=submitEnquireRoaxTaxExpDtProxy&vehicleNo={carplate}&captchaFrom={captchaform}&captchaResponse={captchatext}&agreeTC=Y&windowID={windowID}'
    headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-SG,en-US;q=0.9,en;q=0.8,ja;q=0.7,da;q=0.6,zh-CN;q=0.5,zh;q=0.4',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://vrl.lta.gov.sg',
    'Referer': 'https://vrl.lta.gov.sg/lta/vrl/action/pubfunc?ID=EnquireRoadTaxExpDtProxy',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
    }

    response = session.request("POST", url, headers=headers, data=payload)
    
    # print(response.text)
    val = Selector(text = response.text)

    if "The characters you entered didn't match the word verification. Please try again." in response.text:
        return("Wrong captcha input")
    else:
        driver.quit()
        result = val.xpath('/html/body/section/div[3]/div[4]/div[2]/div[2]/form/div[1]/div[3]/div/div[2]/div[2]/p/text()').extract()[0]
        result = re.sub(r"[\n\t]*", "", result)
        return(result)


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT).build()

    check_handler = CommandHandler('check', check)
    
    application.add_handler(check_handler)
    
    application.run_polling()
