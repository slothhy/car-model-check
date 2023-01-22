# car-model-check
Retrieves car model from LTA website using Google Vision AI

## Installation
```
pip3 install -r requirements.txt
```

## Configuration
1. Create a telegram bot
2. Create a [Google API credentials key](https://cloud.google.com/vision/docs/before-you-begin) and store in the project's root directory
3. In your project's root directory, create a file called .env. Fill in the keys as below
```
GOOGLE_APPLICATION_CREDENTIALS=
TELEGRAM_BOT=
```

## How to use
1. python carmodel.py

## Bugs
Feel free to report any bugs running the script.

## Disclaimer
This is a private experiment/project to retrieve car model on the roads conveniently. It was a learning opportunity to test out Google Vision AI's capability to solve the captchas automatically.