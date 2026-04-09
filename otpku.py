import requests
import time
from datetime import datetime
import re
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, Forbidden, BadRequest

# ================================================
#  CONFIG
# ================================================
API_URL = "http://147.135.212.197/crapi/st/viewstats"

TOKEN = "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ=="

params = {
    "token": TOKEN,
    "records": ""
}

TELEGRAM_BOT_TOKEN = "7250319217:AAHfvakVDSZXcBpfVsMm2B_WbdXtUDoKpUA"

TELEGRAM_GROUP_ID = -1003090338172

CHECK_DELAY = 7
SEND_DELAY = 1
RETRY = 3


# ================================================
# COUNTRY MAP (TIDAK DIUBAH)
# ================================================
COUNTRY_MAP = {

    "1":("United States","🇺🇸"),
    "7":("Russia","🇷🇺"),
    "20":("Egypt","🇪🇬"),
    "27":("South Africa","🇿🇦"),
    "30":("Greece","🇬🇷"),
    "31":("Netherlands","🇳🇱"),
    "32":("Belgium","🇧🇪"),
    "33":("France","🇫🇷"),
    "34":("Spain","🇪🇸"),
    "36":("Hungary","🇭🇺"),
    "39":("Italy","🇮🇹"),
    "40":("Romania","🇷🇴"),
    "41":("Switzerland","🇨🇭"),
    "43":("Austria","🇦🇹"),
    "44":("United Kingdom","🇬🇧"),
    "45":("Denmark","🇩🇰"),
    "46":("Sweden","🇸🇪"),
    "47":("Norway","🇳🇴"),
    "48":("Poland","🇵🇱"),
    "49":("Germany","🇩🇪"),
    "51":("Peru","🇵🇪"),
    "52":("Mexico","🇲🇽"),
    "53":("Cuba","🇨🇺"),
    "54":("Argentina","🇦🇷"),
    "55":("Brazil","🇧🇷"),
    "56":("Chile","🇨🇱"),
    "57":("Colombia","🇨🇴"),
    "58":("Venezuela","🇻🇪"),
    "60":("Malaysia","🇲🇾"),
    "61":("Australia","🇦🇺"),
    "62":("Indonesia","🇮🇩"),
    "63":("Philippines","🇵🇭"),
    "64":("New Zealand","🇳🇿"),
    "65":("Singapore","🇸🇬"),
    "66":("Thailand","🇹🇭"),
    "81":("Japan","🇯🇵"),
    "82":("South Korea","🇰🇷"),
    "84":("Vietnam","🇻🇳"),
    "86":("China","🇨🇳"),
    "91":("India","🇮🇳"),
    "92":("Pakistan","🇵🇰"),
    "93":("Afghanistan","🇦🇫"),
    "94":("Sri Lanka","🇱🇰"),
    "95":("Myanmar","🇲🇲"),
    "98":("Iran","🇮🇷"),

}

# ================================================
# APP ICON MAP (TIDAK DIUBAH)
# ================================================
APP_ICONS = {

"whatsapp":"💬",
"telegram":"✈️",
"instagram":"📸",
"twitter":"🐦",
"facebook":"👤",
"tiktok":"🎵",
"snapchat":"👻",
"google":"🔍",
"gmail":"📧",
"yahoo":"💜",
"microsoft":"🪟",
"amazon":"📦",
"apple":"🍎",
"paypal":"💳",
"uber":"🚗",
"grab":"🟢",
"gojek":"🟢",
"shopee":"🛍️",
"lazada":"🛒",
"tokopedia":"🟢",
"discord":"🎮",
"netflix":"🎬",
"spotify":"🎵",
"steam":"🎮",
"imo":"📞",
"line":"💚",
"viber":"💜",
"wechat":"🟢",
"signal":"🔵",
"smsinfo":"💌",

}


# ================================================
# HELPERS
# ================================================
def esc(text):

    special=r'\_*[]()~`>#+-=|{}.!'

    return ''.join(
        '\\'+c if c in special else c for c in str(text)
    )


def get_app_icon(app):

    name=app.lower()

    for key,icon in APP_ICONS.items():

        if key in name:

            return icon

    return "📱"


def get_country(phone):

    clean=phone.lstrip('+').lstrip('0')

    for code in sorted(COUNTRY_MAP.keys(),key=len,reverse=True):

        if clean.startswith(code):

            return COUNTRY_MAP[code]

    return ("Unknown","🌍")


def extract_otp(message):

    patterns=[

        r'(?:code|verification|otp)[^\d]{0,10}(\d{4,8})',

        r'\b(\d{6})\b',

        r'\b(\d{4,8})\b',

    ]

    for pat in patterns:

        m=re.search(pat,message,re.I)

        if m:

            return m.group(1)

    return "N/A"


def parse_timestamp(ts):

    try:

        return datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")

    except:

        return None


def fetch_sms():

    try:

        r=requests.get(API_URL,params=params,timeout=25)

        r.raise_for_status()

        data=r.json()

        if isinstance(data,list):

            return data

        return []

    except Exception as e:

        print("[API ERROR]",e)

        return []


# ================================================
# SAFE TELEGRAM SEND
# ================================================
async def safe_send(bot,text,markup):

    for i in range(RETRY):

        try:

            await bot.send_message(

                chat_id=TELEGRAM_GROUP_ID,

                text=text,

                parse_mode=ParseMode.MARKDOWN_V2,

                reply_markup=markup

            )

            return True

        except BadRequest:

            try:

                await bot.send_message(

                    chat_id=TELEGRAM_GROUP_ID,

                    text=text,

                    reply_markup=markup

                )

                return True

            except Exception:
                pass

        except Forbidden:

            print("BOT NOT IN GROUP")

            return False

        except NetworkError:

            print("NETWORK RETRY")

            await asyncio.sleep(3)

        except TelegramError as e:

            print("TG ERROR",e)

            await asyncio.sleep(2)

    return False


# ================================================
# SEND OTP
# ================================================
async def send_otp(bot,app,phone,msg,ts):

    icon=get_app_icon(app)

    country,flag=get_country(phone)

    otp=extract_otp(msg)

    clean=msg.replace("\n"," ")

    text=(

f"╔══════════════════════╗\n"
f" {icon} *{esc(app.upper())} OTP*\n"
f"╚══════════════════════╝\n\n"

f"🔐 *OTP*\n"

f"`{esc(otp)}`\n\n"

f"{flag} *Country:* {esc(country)}\n"

f"📱 `{esc(phone)}`\n"

f"📲 {esc(app)}\n"

f"🕐 {esc(ts)}\n\n"

f"```\n{esc(clean)}\n```"

)

    keyboard=[

[InlineKeyboardButton("Channel",url="https://t.me/javfunx")],

[InlineKeyboardButton(f"OTP {otp}",callback_data="otp")]

]

    markup=InlineKeyboardMarkup(keyboard)

    ok=await safe_send(bot,text,markup)

    if ok:

        print("SENT",phone,otp)

    else:

        print("FAILED",phone)


# ================================================
# MAIN
# ================================================
async def main():

    print("STARTING BOT")

    try:

        bot=Bot(TELEGRAM_BOT_TOKEN)

        me=await bot.get_me()

        print("BOT:",me.username)

    except Exception as e:

        print("BOT FAIL",e)

        return


    try:

        chat=await bot.get_chat(TELEGRAM_GROUP_ID)

        print("GROUP OK:",chat.title)

    except Exception as e:

        print("CHAT ERROR")

        print("ADD BOT TO GROUP")

        print(e)

        return


    last=None

    while True:

        try:

            entries=fetch_sms()

            if not entries:

                await asyncio.sleep(CHECK_DELAY)

                continue


            new=[]

            if last is None:

                new=entries[:8]

                if new:

                    last=parse_timestamp(new[0][3])

            else:

                for e in entries:

                    ts=parse_timestamp(e[3])

                    if ts and ts>last:

                        new.append(e)


            if new:

                t=parse_timestamp(new[0][3])

                if t:

                    last=t

                print("NEW OTP:",len(new))


            for e in reversed(new):

                try:

                    await send_otp(

                        bot,

                        e[0],

                        e[1],

                        e[2],

                        e[3]

                    )

                    await asyncio.sleep(SEND_DELAY)

                except Exception as er:

                    print("SEND FAIL",er)


            await asyncio.sleep(CHECK_DELAY)

        except Exception as loop_error:

            print("LOOP ERROR",loop_error)

            await asyncio.sleep(10)


# ================================================
# RUN
# ================================================
if __name__=="__main__":

    asyncio.run(main())