# 🚀 Crypto Trading Bot with Robinhood and OpenAI 🤖

This bot uses the Robinhood API to trade cryptocurrencies based on advice from OpenAI's GPT-4 model. The bot can trade Bitcoin (BTC), Ethereum (ETH), Binance Coin (BNB), Ripple (XRP), and Cardano (ADA).

## 📚 Dependencies

The bot requires the following Python libraries:

- robin_stocks
- pyotp
- openai
- os
- datetime
- time
- requests
- re

## 🛠 Setup

1. **Robinhood Account:** You need a Robinhood account with two-factor authentication (2FA) enabled. The bot uses the Robinhood API to execute trades.

2. **OpenAI API Key:** You need an OpenAI API key to use the GPT-4 model. You can get this from the OpenAI website.

3. **News API Key:** You need a News API key to fetch news headlines for the cryptocurrencies. You can get this from the News API website.

4. **Environment Variables:** The bot uses environment variables to store sensitive information. You should create a `.env` file in the same directory as your Python script and add the following variables as per .env.template:

    - `ROBINHOOD_EMAIL`: Your Robinhood account email.
    - `ROBINHOOD_PASSWORD`: Your Robinhood account password.
    - `TOTP`: Your Time-based One-Time Password (TOTP) for 2FA. See the TOTP section below for more details.
    - `OPENAI_API_KEY`: Your OpenAI API key.
    - `NEWSAPI_KEY`: Your News API key.

## 🕒 Time-based One-Time Password (TOTP)

The bot uses TOTP for 2FA with Robinhood. Here's how to set it up:

1. Log into your Robinhood account and enable 2FA. When asked which 2FA app you want to use, select "other".

2. Robinhood will present you with an alphanumeric code. This is your TOTP secret. Copy this code and set it as the `TOTP` environment variable in your `.env` file.

3. Run the following Python code to generate a TOTP:

    ```python
    import pyotp
    totp = pyotp.TOTP("YourTOTPSecretHere").now()
    print("Current OTP:", totp)
    ```

    Replace `"YourTOTPSecretHere"` with your TOTP secret. The code will print a 6-digit OTP.

4. Enter this OTP into the prompt on your Robinhood app. Robinhood will give you a backup code. **Do not lose this code or you may be locked out of your account!**

5. You can also enter your TOTP secret into a 2FA app on your phone, such as Google Authenticator. This will generate the same OTPs as your Python code, which is useful if you need to access your Robinhood account from your phone.

## 🏃‍♀️ Running the Bot

To run the bot, simply run the Python script. The bot will start trading cryptocurrencies based on advice from the GPT-4 model. The bot will execute a trade every hour.

## ⚠️ Disclaimer

This bot is for educational purposes only. Use it at your own risk. Cryptocurrency trading involves financial risk, and you should only trade with money you can afford to lose.
