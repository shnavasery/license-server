import telebot
import requests
import time

# ==================== تنظیمات ====================
TOKEN = '8674949577:AAFQ7VKrPFRs06lXe415etoDYOmSpRUh2Kw'
SERVER_URL = 'https://license-server-cyi5.onrender.com'

bot = telebot.TeleBot(TOKEN)

# ==================== دستورات ربات ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🤖 به ربات تولید لایسنس خوش آمدید!\n\n"
        "لطفاً Hardware ID خود را ارسال کنید تا لایسنس دریافت کنید.\n\n"
        "🔑 برای دریافت Hardware ID، برنامه را اجرا کنید و روی دکمه 'دریافت شناسه سیستم' کلیک کنید."
    )

@bot.message_handler(commands=['status'])
def check_server(message):
    try:
        response = requests.get(f'{SERVER_URL}/api/status', timeout=5)
        if response.status_code == 200:
            bot.reply_to(message, '✅ سرور فعال است.')
        else:
            bot.reply_to(message, '❌ سرور پاسخ نمی‌دهد.')
    except:
        bot.reply_to(message, '❌ اتصال به سرور برقرار نشد.')

@bot.message_handler(func=lambda message: True)
def handle_hardware_id(message):
    hardware_id = message.text.strip()
    
    if len(hardware_id) < 10:
        bot.reply_to(
            message,
            "❌ Hardware ID نامعتبر است. لطفاً دوباره ارسال کنید.\n\n"
            "🔑 برای دریافت Hardware ID، برنامه را اجرا کنید و روی دکمه 'دریافت شناسه سیستم' کلیک کنید."
        )
        return
    
    bot.reply_to(message, '⏳ در حال تولید لایسنس... لطفاً صبر کنید.')
    
    try:
        response = requests.post(
            f'{SERVER_URL}/api/generate',
            json={'hardware_id': hardware_id},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                license_key = data.get('license_key')
                expires_at = data.get('expires_at', 'نامشخص')
                
                bot.reply_to(
                    message,
                    f"✅ لایسنس شما با موفقیت تولید شد:\n\n"
                    f"🔑 `{license_key}`\n\n"
                    f"📅 تاریخ انقضا: {expires_at}\n\n"
                    f"⚠️ لطفاً این کد را کپی کنید و در برنامه وارد کنید."
                )
            else:
                license_key = data.get('license_key', '')
                if license_key:
                    bot.reply_to(
                        message,
                        f"⚠️ این Hardware ID قبلاً لایسنس دریافت کرده است.\n\n"
                        f"🔑 لایسنس شما: `{license_key}`"
                    )
                else:
                    bot.reply_to(
                        message,
                        f"❌ خطا در تولید لایسنس: {data.get('message', 'خطای ناشناخته')}"
                    )
        else:
            bot.reply_to(
                message,
                f"❌ خطا در ارتباط با سرور. کد خطا: {response.status_code}"
            )
    except requests.exceptions.Timeout:
        bot.reply_to(message, '❌ زمان پاسخ‌دهی سرور به پایان رسید. لطفاً دوباره تلاش کنید.')
    except Exception as e:
        bot.reply_to(message, f'❌ خطا: {str(e)}')

# ==================== اجرای ربات ====================
if __name__ == '__main__':
    print('🤖 ربات تلگرام شروع به کار کرد...')
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f'خطا: {e}')
            time.sleep(5)