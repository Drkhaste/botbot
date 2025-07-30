from telethon.sync import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from datetime import datetime
import aiomysql
import aiohttp
import asyncio
import time
import json
import os
import re
import subprocess
import pytz
import platform
import random
import Tools
import BH
import Info

if platform.system() != "Windows":
    pid_file = 'PID'
    if not os.path.exists(pid_file):
        with open(pid_file, 'w') as f:
            random_pid = random.randint(100000000, 999999999)
            f.write(str(random_pid))
    with open(pid_file, 'r+') as f:
        pid = f.read()
        result = subprocess.check_output(f'ps -p {pid} > /dev/null 2>&1 && echo "True" || echo "False"', shell=True)
        result = result.decode()
        if result.strip() == 'True':
            print('err-dup')
            exit()
        else:
            f.seek(0)
            f.write(str(os.getpid()))
            f.truncate()

client = TelegramClient('Bot', Info.api_id, Info.api_hash)

async def get_db_connection():
    try:
        connection = await aiomysql.connect(
            host=Info.dbaddr,
            user=Info.dbuser,
            password=Info.dbpass,
            db=Info.dbname,
            charset="utf8mb4"
        )
        return connection
    except aiomysql.MySQLError as e:
        print(f"Database connection failed: {e}")
        return None

async def set_step(dbc, user, step):
    async with dbc.cursor() as db:
        await db.execute("UPDATE Users SET `Step` = %s WHERE `User` = %s", (step, user))
        await dbc.commit()

async def irequest(url, proxy=None, timeout=5):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
    except aiohttp.ClientError as e:
        raise ProxyError
    except asyncio.TimeoutError as e:
        raise ProxyError
    except Exception as e:
        raise ProxyError

async def send_request(method: str, data: dict = None, timeout: int = 10):
    url = f"https://api.telegram.org/bot{Info.Token}/{method}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, timeout=timeout) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError:
        return None
    except asyncio.TimeoutError:
        return None

class ProxyError(BaseException):
    pass

async def auto_run(interval):
    while True:
        dbc = await get_db_connection()
        async with dbc.cursor() as db:
            await db.execute("SELECT * FROM Timer")
            Timers = await db.fetchall()
            iran_timezone = pytz.timezone('Asia/Tehran')
            iran_time = datetime.now(iran_timezone)
            hour = iran_time.hour
            Ti = time.time()
            for t in Timers:
                if hour == int(t[2]) and (Ti - float(t[3])) >= 86400:
                    await db.execute('UPDATE Timer SET `SHT` = %s WHERE `Id` = %s', (time.time(), t[0]))
                    await dbc.commit()
                    TID = t[1]
                    await db.execute('SELECT * FROM `Tasks` WHERE `Id` = %s', (TID,))
                    Task = (await db.fetchall())[0]
                    Id, Name, Sessions, Messages, Peers, Create_Ti, RunTime, User, Sleep, Status = Task
                    edit = await client.send_message(int(User), f'▶️ ذخیره سازی تسک {Name}...')
                    groups = json.loads(Peers)
                    for group in groups:
                        gid = f'-100{groups[group]}'
                        await send_request('setChatPermissions', {
                            'chat_id': gid,
                            'permissions': json.dumps({
                                'can_send_messages': True,
                                'can_send_photos': True,
                                'can_send_documents': True,
                            })
                        })
                    await db.execute(f"SELECT * FROM `Messages` WHERE `Name` = %s", (Messages,))
                    Mess = await db.fetchall()
                    if len(Mess) == 0: break
                    sid = -1
                    STi = int(time.time())
                    for Mes in Mess:
                        for group in groups:
                            await db.execute('INSERT INTO `Queue` VALUES (0, %s, %s, %s, %s, %s, %s)', (Id, Mes[7], group, Mes[0], STi, User))
                        STi += Sleep
                    await dbc.commit()
                    await asyncio.sleep(2)
                    await edit.edit(f'✅ ذخیره سازی {Name} تکمیل شد.')

        await asyncio.sleep(interval)

@client.on(events.NewMessage())
async def app(event):

    dbc = await get_db_connection()

    async with dbc.cursor() as db:
        import time
        user_id = event.sender_id
        text = str(event.raw_text)
        Ti = time.time()

        chat = await event.get_chat()
        if getattr(chat, 'megagroup', False):
            await db.execute("SELECT * FROM Sessions WHERE `User` = %s", (user_id,))
            user_d = await db.fetchall()
            if db.rowcount == 0:
                pass
                # await event.delete()
            return

        with open("Admins", "r", encoding="utf-8") as f:
            content = f.read()
            Admins = json.loads(content)

        if str(user_id) not in Admins:
            return False

        await db.execute("SELECT * FROM Users WHERE `User` = %s", (user_id,))
        user_d = await db.fetchall()
        if db.rowcount == 0:
            await db.execute("INSERT INTO Users VALUES (0, %s, %s, %s, %s)", (str(user_id), 'none', str(Ti), '[]'))
            await dbc.commit()
            user_data = {
                'Id': db.lastrowid,
                'User': user_id,
                'Step': 'none',
                'Ti': '0',
                'Data': '[]',
            }
        else:
            user_data = {
                'Id': user_d[0][0],
                'User': user_d[0][1],
                'Step': user_d[0][2],
                'Ti': user_d[0][3],
                'Data': user_d[0][4]
            }

        if (time.time() - float(user_data['Ti'])) >= 0.5:
            await db.execute("UPDATE Users SET `Ti` = %s WHERE `User` = %s", (str(Ti), user_id))
            await dbc.commit()
        else:
            return

        hok = [
            [Button.text("💢 ارسال اکانت", resize=True), Button.text("❌ حذف اکانت", resize=True)],
            [Button.text("💢 ارسال اکانت خام", resize=True), Button.text("❌ حذف اکانت خام", resize=True)],
            [Button.text("⚙️ مدیریت تسک", resize=True), Button.text("❌ حذف ردیف", resize=True)],
            [Button.text("⚙️ مدیریت پیام پیشرفته", resize=True), Button.text("⚙️ مدیریت پیام", resize=True)],
        ]

        back = [
            [Button.text("بازگشت", resize=True)],
        ]

        if text.lower() == '/start' or text == 'بازگشت':
            await client.send_message(user_id, '💬 صفحهء اصلی.', buttons=hok)
            await set_step(dbc, user_id, 'none')
            return True

        if text.lower() == '/restart':
            exit()

        if text.lower() == '/stop':
            with open('stop', 'w') as f:
                f.write('stop')
            await client.send_message(user_id, '❌ Signal sent. Please wait...')

        new = re.findall("^/add (.*)$", text)
        if len(new) == 1:
            with open('Admins', 'r+') as f:
                admins = json.load(f)
                admins.append(new[0])
                f.seek(0)
                json.dump(admins, f, indent=4)
                f.truncate()
            await client.send_message(user_id, '💢 کاربر ادمین شد.', buttons=hok)

        new = re.findall("^/del (.*)$", text)
        if len(new) == 1:
            with open('Admins', 'r+') as f:
                admins = json.load(f)
                if new[0] in admins:
                    admins.remove(new[0])
                f.seek(0)
                json.dump(admins, f, indent=4)
                f.truncate()
            await client.send_message(user_id, '💢 کاربر ادمین حذف شد.', buttons=hok)

        if text.startswith('/close_'):
            tid = text.split('_')[1]
            await db.execute('SELECT * FROM `Tasks` WHERE `Id` = %s', (tid,))
            Task = (await db.fetchall())[0]
            Id, Name, Sessions, Messages, Peers, Create_Ti, RunTime, User, Sleep, Status = Task
            groups = json.loads(Peers)
            for group in groups:
                gid = f'-100{groups[group]}'
                await send_request('setChatPermissions', {
                    'chat_id': gid,
                    'permissions': json.dumps({
                        'can_send_messages': False,
                        'can_send_photos': False,
                        'can_send_documents': False,
                    })
                })
            await client.send_message(user_id, '💬 گروه های مورد نظر بسته شدند.')

        if text == '💢 ارسال اکانت':
            await set_step(dbc, user_id, 'registerAccount')
            await client.send_message(user_id, "📍 شمارهء اکانت خود را با فرمت بین المللی ارسال کنید:\n✅ +989998887777", buttons=[
                [Button.text("بازگشت", resize=True)],
            ])

        if user_data['Step'] == 'registerAccount':
            phone = text.replace('+', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            if phone.isdigit():
                await client.send_message(user_id, "⏳ لطفا صبر کنید...")
                apis = await Tools.rTFetch(dbc, 'API')
                devices = await Tools.rTFetch(dbc, 'Devices', f'WHERE `API` = {apis[0]}')
                proxies = Tools.read_file('con_Proxies')
                Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                url = 'https://api.redgenius.top/IP'
                try:
                    _ = await irequest(url, proxy=Proxy)
                except ProxyError as e:
                    while True:
                        print('Change Proxy')
                        proxies = Tools.read_file('con_Proxies')
                        Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                        url = 'https://api.redgenius.top/IP'
                        try:
                            response = await irequest(url, proxy=Proxy)
                            res = await irequest(url)
                            if json.loads(response)['origin'] != json.loads(res)['origin']:
                                break
                        except ProxyError as e:
                            pass
                AHash, AID = apis[1:3]
                device_model, system_version, app_version = devices[1:4]
                ran = Tools.generate_hash(4)
                name = str(user_id) + ran
                Log = await BH.login(
                    api_id=AID,
                    api_hash=AHash,
                    name=name,
                    phone=text,
                    device_model=device_model,
                    system_version=system_version,
                    app_version=app_version,
                    proxy_str=Proxy
                )
                if Log['status'] == 'code':
                    hash_code = Log['hash_code']
                    await db.execute(
                        "INSERT INTO `Sessions` VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            name,
                            AID,
                            AHash,
                            phone,
                            device_model,
                            system_version,
                            app_version,
                            Proxy,
                            user_id,
                            hash_code,
                            0,
                            0,
                            '',
                        )
                    )
                    await dbc.commit()
                    await set_step(dbc, user_id, f'getCode:{db.lastrowid}')
                    await client.send_message(user_id, "📍 کد ارسال شده از سمت تلگرام را ارسال کنید:", buttons=[
                        [Button.text("بازگشت", resize=True)],
                    ])
            else:
                await client.send_message(user_id, "⚠️ فرمت شماره ارسالی اشتباه است.")

        if user_data['Step'].startswith('getCode') and str(text).isdigit():
            Sid = user_data['Step'].split(':')[1]
            await client.send_message(user_id, "⏳ لطفا صبر کنید...")
            await db.execute("SELECT * FROM Sessions WHERE `Id` = %s", (Sid,))
            session = (await db.fetchall())[0]
            session = list(session)
            Proxy = session[8]
            url = 'https://api.redgenius.top/IP'
            try:
                _ = await irequest(url, proxy=Proxy)
            except ProxyError as e:
                while True:
                    print('Change Proxy')
                    proxies = Tools.read_file('con_Proxies')
                    Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                    url = 'https://api.redgenius.top/IP'
                    try:
                        response = await irequest(url, proxy=Proxy)
                        res = await irequest(url)
                        if json.loads(response)['origin'] != json.loads(res)['origin']:
                            await db.execute('UPDATE `Sessions` SET `Proxy` = %s WHERE `Id` = %s', (Proxy, session[0]))
                            await dbc.commit()
                            session[8] = Proxy
                            break
                    except ProxyError as e:
                        pass
            Log = await BH.login(
                api_id=session[2],
                api_hash=session[3],
                name=session[1],
                phone=session[4],
                device_model=session[5],
                system_version=session[6],
                app_version=session[7],
                proxy_str=session[8],
                code=text,
                hash_code=session[10],
                sssid=session[0]
            )
            if Log['status'] == 'ok':
                await db.execute('UPDATE `Sessions` SET `Hash` = %s, `SSession` = %s, `Name` = %s, `User` = %s WHERE `Id` = %s', ('Done', Log['Session'], Log['name'], Log['id'], Sid))
                await dbc.commit()
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "✅ اتصال به اکانت انجام شد.", buttons=hok)
            if Log['status'] == 'password':
                await set_step(dbc, user_id, f'getPassword:{Sid}')
                await dbc.commit()
                await client.send_message(user_id, "📍 رمز 2FA اکانت را ارسال کنید:", buttons=[
                    [Button.text("بازگشت", resize=True)],
                ])
            if Log['status'] == 'error':
                await client.send_message(user_id, '⚠️ کد ارسالی اشتباه است.')

        if user_data['Step'].startswith('getPassword'):
            Sid = user_data['Step'].split(':')[1]
            await client.send_message(user_id, "⏳ لطفا صبر کنید...")
            await db.execute("SELECT * FROM Sessions WHERE `Id` = %s", (Sid,))
            session = (await db.fetchall())[0]
            session = list(session)
            Proxy = session[8]
            url = 'https://api.redgenius.top/IP'
            try:
                _ = await irequest(url, proxy=Proxy)
            except ProxyError as e:
                while True:
                    print('Change Proxy')
                    proxies = Tools.read_file('con_Proxies')
                    Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                    url = 'https://api.redgenius.top/IP'
                    try:
                        response = await irequest(url, proxy=Proxy)
                        res = await irequest(url)
                        if json.loads(response)['origin'] != json.loads(res)['origin']:
                            await db.execute('UPDATE `Sessions` SET `Proxy` = %s WHERE `Id` = %s', (Proxy, session[0]))
                            await dbc.commit()
                            session[8] = Proxy
                            break
                    except ProxyError as e:
                        pass
            Log = await BH.login(
                api_id=session[2],
                api_hash=session[3],
                name=session[1],
                phone=session[4],
                device_model=session[5],
                system_version=session[6],
                app_version=session[7],
                proxy_str=session[8],
                code=session[11],
                hash_code=session[10],
                password=text,
                sssid=session[0]
            )
            if Log['status'] == 'ok':
                await db.execute('UPDATE `Sessions` SET `Hash` = %s, `SSession` = %s, `Name` = %s, `User` = %s WHERE `Id` = %s', ('Done', Log['Session'], Log['name'], Log['id'], Sid))
                await dbc.commit()
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "✅ اتصال به اکانت انجام شد.", buttons=hok)
            else:
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "⚠️ هنگام اتصال به اکانت خطایی رخ داده است.", buttons=hok)

        if text == '💢 ارسال اکانت خام':
            await set_step(dbc, user_id, 'kregisterAccount')
            await client.send_message(user_id, "📍 شمارهء اکانت خود را با فرمت بین المللی ارسال کنید:\n✅ +989998887777", buttons=[
                [Button.text("بازگشت", resize=True)],
            ])

        if user_data['Step'] == 'kregisterAccount':
            phone = text.replace('+', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            if phone.isdigit():
                await client.send_message(user_id, "⏳ لطفا صبر کنید...")
                apis = await Tools.rTFetch(dbc, 'API')
                devices = await Tools.rTFetch(dbc, 'Devices', f'WHERE `API` = {apis[0]}')
                proxies = Tools.read_file('con_Proxies')
                Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                url = 'https://api.redgenius.top/IP'
                try:
                    _ = await irequest(url, proxy=Proxy)
                except ProxyError as e:
                    while True:
                        print('Change Proxy')
                        proxies = Tools.read_file('con_Proxies')
                        Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                        url = 'https://api.redgenius.top/IP'
                        try:
                            response = await irequest(url, proxy=Proxy)
                            res = await irequest(url)
                            if json.loads(response)['origin'] != json.loads(res)['origin']:
                                break
                        except ProxyError as e:
                            pass
                AHash, AID = apis[1:3]
                device_model, system_version, app_version = devices[1:4]
                ran = Tools.generate_hash(4)
                name = str(user_id) + ran
                Log = await BH.login(
                    api_id=AID,
                    api_hash=AHash,
                    name=name,
                    phone=text,
                    device_model=device_model,
                    system_version=system_version,
                    app_version=app_version,
                    proxy_str=Proxy
                )
                if Log['status'] == 'code':
                    hash_code = Log['hash_code']
                    await db.execute(
                        "INSERT INTO `SessionsB` VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            name,
                            AID,
                            AHash,
                            phone,
                            device_model,
                            system_version,
                            app_version,
                            Proxy,
                            user_id,
                            hash_code,
                            0,
                            0,
                            '',
                        )
                    )
                    await dbc.commit()
                    await set_step(dbc, user_id, f'kgetCode:{db.lastrowid}')
                    await client.send_message(user_id, "📍 کد ارسال شده از سمت تلگرام را ارسال کنید:", buttons=[
                        [Button.text("بازگشت", resize=True)],
                    ])
            else:
                await client.send_message(user_id, "⚠️ فرمت شماره ارسالی اشتباه است.")

        if user_data['Step'].startswith('kgetCode') and str(text).isdigit():
            Sid = user_data['Step'].split(':')[1]
            await client.send_message(user_id, "⏳ لطفا صبر کنید...")
            await db.execute("SELECT * FROM SessionsB WHERE `Id` = %s", (Sid,))
            session = (await db.fetchall())[0]
            session = list(session)
            Proxy = session[8]
            url = 'https://api.redgenius.top/IP'
            try:
                _ = await irequest(url, proxy=Proxy)
            except ProxyError as e:
                while True:
                    print('Change Proxy')
                    proxies = Tools.read_file('con_Proxies')
                    Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                    url = 'https://api.redgenius.top/IP'
                    try:
                        response = await irequest(url, proxy=Proxy)
                        res = await irequest(url)
                        if json.loads(response)['origin'] != json.loads(res)['origin']:
                            await db.execute('UPDATE `SessionsB` SET `Proxy` = %s WHERE `Id` = %s', (Proxy, session[0]))
                            await dbc.commit()
                            session[8] = Proxy
                            break
                    except ProxyError as e:
                        pass
            Log = await BH.login(
                api_id=session[2],
                api_hash=session[3],
                name=session[1],
                phone=session[4],
                device_model=session[5],
                system_version=session[6],
                app_version=session[7],
                proxy_str=session[8],
                code=text,
                hash_code=session[10],
                sssid=session[0],
                photo=False
            )
            if Log['status'] == 'ok':
                await db.execute('UPDATE `SessionsB` SET `Hash` = %s, `SSession` = %s, `Name` = %s, `User` = %s WHERE `Id` = %s', ('Done', Log['Session'], Log['name'], Log['id'], Sid))
                await dbc.commit()
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "✅ اتصال به اکانت انجام شد.", buttons=hok)
            if Log['status'] == 'password':
                await set_step(dbc, user_id, f'kgetPassword:{Sid}')
                await dbc.commit()
                await client.send_message(user_id, "📍 رمز 2FA اکانت را ارسال کنید:", buttons=[
                    [Button.text("بازگشت", resize=True)],
                ])
            if Log['status'] == 'error':
                await client.send_message(user_id, '⚠️ کد ارسالی اشتباه است.')

        if user_data['Step'].startswith('kgetPassword'):
            Sid = user_data['Step'].split(':')[1]
            await client.send_message(user_id, "⏳ لطفا صبر کنید...")
            await db.execute("SELECT * FROM SessionsB WHERE `Id` = %s", (Sid,))
            session = (await db.fetchall())[0]
            session = list(session)
            Proxy = session[8]
            url = 'https://api.redgenius.top/IP'
            try:
                _ = await irequest(url, proxy=Proxy)
            except ProxyError as e:
                while True:
                    print('Change Proxy')
                    proxies = Tools.read_file('con_Proxies')
                    Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                    url = 'https://api.redgenius.top/IP'
                    try:
                        response = await irequest(url, proxy=Proxy)
                        res = await irequest(url)
                        if json.loads(response)['origin'] != json.loads(res)['origin']:
                            await db.execute('UPDATE `SessionsB` SET `Proxy` = %s WHERE `Id` = %s', (Proxy, session[0]))
                            await dbc.commit()
                            session[8] = Proxy
                            break
                    except ProxyError as e:
                        pass
            Log = await BH.login(
                api_id=session[2],
                api_hash=session[3],
                name=session[1],
                phone=session[4],
                device_model=session[5],
                system_version=session[6],
                app_version=session[7],
                proxy_str=session[8],
                code=session[11],
                hash_code=session[10],
                password=text,
                sssid=session[0],
                photo=False
            )
            if Log['status'] == 'ok':
                await db.execute('UPDATE `SessionsB` SET `Hash` = %s, `SSession` = %s, `Name` = %s, `User` = %s WHERE `Id` = %s', ('Done', Log['Session'], Log['name'], Log['id'], Sid))
                await dbc.commit()
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "✅ اتصال به اکانت انجام شد.", buttons=hok)
            else:
                await set_step(dbc, user_id, 'none')
                await client.send_message(user_id, "⚠️ هنگام اتصال به اکانت خطایی رخ داده است.", buttons=hok)

        if text == '❌ حذف ردیف':
            await set_step(dbc, user_id, 'deleteDST')
            await client.send_message(user_id, "📍 شمارهء ردیف را ارسال کنید:", buttons=[
                [Button.text("بازگشت", resize=True)],
            ])

        if user_data['Step'] == 'deleteDST':
            await client.send_message(user_id, "⏳ لطفا صبر کنید...")
            db.execute("SELECT * FROM Messages WHERE `Name` = %s", (text,))
            nd = db.fetchall()
            if db.rowcount > 0:
                await db.execute("DELETE FROM Messages WHERE `Name` = %s", (text,))
                await dbc.commit()
                await client.send_message(user_id, "⚠️ ردیف حذف شد.")
            else:
                await client.send_message(user_id, "⚠️ ردیف یافت نشد.")

        if text == '❌ حذف اکانت':
            await set_step(dbc, user_id, 'deleteAccount')
            await client.send_message(user_id, "📍 شمارهء اکانت خود را با فرمت بین المللی ارسال کنید:\n✅ +989998887777", buttons=[
                [Button.text("بازگشت", resize=True)],
            ])

        if user_data['Step'] == 'deleteAccount':
            phone = text.replace('+', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            if phone.isdigit():
                await client.send_message(user_id, "⏳ لطفا صبر کنید...")
                await db.execute("SELECT * FROM Sessions WHERE `Phone` = %s", (phone,))
                session = (await db.fetchall())[0]
                if db.rowcount > 0:
                    session = list(session)
                    Proxy = session[8]
                    url = 'https://api.redgenius.top/IP'
                    try:
                        _ = await irequest(url, proxy=Proxy)
                    except ProxyError as e:
                        while True:
                            print('Change Proxy')
                            proxies = Tools.read_file('con_Proxies')
                            Proxy = random.choice(proxies).replace("\n", "") if len(proxies) > 0 else None
                            url = 'https://api.redgenius.top/IP'
                            try:
                                response = await irequest(url, proxy=Proxy)
                                res = await irequest(url)
                                if json.loads(response)['origin'] != json.loads(res)['origin']:
                                    await db.execute('UPDATE `Sessions` SET `Proxy` = %s WHERE `Id` = %s', (Proxy, session[0]))
                                    await dbc.commit()
                                    session[8] = Proxy
                                    break
                            except ProxyError as e:
                                pass
                    aclient = await BH.connect_client(
                        name=session[1],
                        api_id=session[2],
                        api_hash=session[3],
                        device_model=session[5],
                        system_version=session[6],
                        app_version=session[7],
                        proxy_str=session[8],
                        ssession=session[13]
                    )
                    await aclient.send_message('@spambot', '/start')
                    await aclient.log_out()
                    await db.execute("DELETE FROM Sessions WHERE `Id` = %s", (session[0],))
                    await dbc.commit()
                    await client.send_message(user_id, "⚠️ شماره با موفقیت حذف و لاگ اوت شد.")
                else:
                    await client.send_message(user_id, "⚠️ شماره یافت نشد.")
            else:
                await client.send_message(user_id, "⚠️ فرمت شماره ارسالی اشتباه است.")

        if text == '⚙️ مدیریت پیام':
            await set_step(dbc, user_id, 'MessageConfig')
            await client.send_message(user_id, '💬', buttons=back)
            n_buttons = []
            for i in range(20):
                n_buttons.append(Button.inline(f"🔖 {i + 1}", f'EditMessage:{i}:1'))
            n_buttons = Tools.array_chunk(n_buttons, 5)
            n_buttons.append([
                Button.inline(f"💢 تغییر نام", f'EditName:1')
            ])
            n_buttons.append([
                Button.inline(f"⏪", f'MessageConfig:0'),
                Button.inline(f"➡️", f'MessageConfig:1'),
                Button.inline(f"⏩", f'MessageConfig:-1')
            ])
            await client.send_message(user_id, '📑 جایگاه اکانت مورد نظر را انتخاب کنید (ردیف 1):', buttons=n_buttons)

        if user_data['Step'].startswith('GetMessages'):
            hde = user_data['Step'].split(':')
            hcode = int(hde[1])
            radif = int(hde[2])
            await db.execute("SELECT * FROM Sessions WHERE `Hash` = %s LIMIT 21", ('Done',))
            Sessions = await db.fetchall()
            if text == '🔄 ریست کردن':
                await db.execute("DELETE FROM `Messages` WHERE `Session` = %s AND `Name` = %s", ({hcode}, radif))
                await dbc.commit()
                await client.send_message(user_id, f'💢 شناسهء {hcode} ردیف {radif} ریست شد.')
                return True
            if not event.message.grouped_id:
                if event.message.is_reply:
                    replied_message = await event.message.get_reply_message()
                    rmid = replied_message.id
                else:
                    rmid = 0
                if event.photo:
                    d_file = await event.download_media()
                    ext = os.path.splitext(d_file)[1]
                    s_file = f'Files/{hcode}_{Tools.generate_hash(4)}{ext}'
                    os.rename(d_file, s_file)
                    await db.execute("INSERT INTO Messages VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (
                        radif,
                        radif,
                        'Photo',
                        text,
                        s_file,
                        user_id,
                        hcode,
                        event.message.id,
                        rmid,
                        Ti
                    ))
                    await dbc.commit()
                    await client.send_message(user_id, '📪 عکس با موفقیت ثبت شد.', buttons=[
                        [Button.text("🔄 ریست کردن", resize=True)],
                        [Button.text("بازگشت", resize=True)]
                    ])
                elif event.message.media is None and event.text:
                    hcode = user_data['Step'].split(':')[1]
                    await db.execute("INSERT INTO Messages VALUES (0, %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s)", (
                        radif,
                        radif,
                        'Text',
                        text,
                        '',
                        user_id,
                        hcode,
                        event.message.id,
                        rmid,
                        Ti
                    ))
                    await dbc.commit()
                    await client.send_message(user_id, '📪 متن با موفقیت ثبت شد.', buttons=[
                        [Button.text("🔄 ریست کردن", resize=True)],
                        [Button.text("بازگشت", resize=True)]
                    ])

        if text == '⚙️ مدیریت پیام پیشرفته':
            await set_step(dbc, user_id, 'ProMessageConfig')
            await client.send_message(user_id, '💬', buttons=back)
            await db.execute("SELECT DISTINCT `Name`, `Display` FROM Messages WHERE `Name` LIKE %s LIMIT 21", ('Pro%',))
            Messages = await db.fetchall()
            n_buttons = []
            for i in Messages:
                n_buttons.append(Button.inline(f"✏️ {i[1]}", f'RenameRadif:{i[0]}'))
                n_buttons.append(Button.inline(f"❌ {i[1]}", f'DeleteRadif:{i[0]}'))
            n_buttons = Tools.array_chunk(n_buttons, 2)
            td = []
            if len(Messages) > 20: td.append(Button.inline('➡️ صفحه بعدی', f'ProMessageConfig:1'))
            if len(td) > 0: n_buttons.append(td)
            n_buttons.append([
                Button.inline(f"🔶 ثبت ردیف جدید", f'NewRadif'),
            ])
            await client.send_message(user_id, '📑 عملیات مورد نظر را انتخاب کنید:', buttons=n_buttons)

        if user_data['Step'].startswith('SetMessages'):
            hde = user_data['Step'].split(':')
            hcode = int(hde[1])
            radif = hde[2]
            if text == '🔄 ریست کردن':
                await db.execute("DELETE FROM `Messages` WHERE `Session` = %s AND `Name` = %s", ({hcode}, radif))
                await dbc.commit()
                await client.send_message(user_id, f'💢 شناسهء {hcode} ردیف {radif} ریست شد.')
                return True
            if not event.message.grouped_id:
                if event.message.is_reply:
                    replied_message = await event.message.get_reply_message()
                    rmid = replied_message.id
                else:
                    rmid = 0
                if event.photo:
                    d_file = await event.download_media()
                    ext = os.path.splitext(d_file)[1]
                    s_file = f'Files/{hcode}_{Tools.generate_hash(4)}{ext}'
                    os.rename(d_file, s_file)
                    await db.execute("INSERT INTO Messages VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (
                        radif,
                        radif,
                        'Photo',
                        text,
                        s_file,
                        user_id,
                        hcode,
                        event.message.id,
                        rmid,
                        Ti
                    ))
                    await dbc.commit()
                    await client.send_message(user_id, '📪 عکس با موفقیت ثبت شد.', buttons=[
                        [Button.text("🔄 ریست کردن", resize=True)],
                        [Button.text("بازگشت", resize=True)]
                    ])
                elif event.message.media is None and event.text:
                    hcode = user_data['Step'].split(':')[1]
                    await db.execute("INSERT INTO Messages VALUES (0, %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s)", (
                        radif,
                        radif,
                        'Text',
                        text,
                        '',
                        user_id,
                        hcode,
                        event.message.id,
                        rmid,
                        Ti
                    ))
                    await dbc.commit()
                    await client.send_message(user_id, '📪 متن با موفقیت ثبت شد.', buttons=[
                        [Button.text("🔄 ریست کردن", resize=True)],
                        [Button.text("بازگشت", resize=True)]
                    ])

        if text == '⚙️ مدیریت تسک':
            await set_step(dbc, user_id, 'TasksConfig')
            await client.send_message(user_id, '💬', buttons=back)
            n_buttons = [
                [Button.inline("➕ ثبت تسک جدید", 'NewTask')],
                [Button.inline("🗑 حذف تسک‌های غیرفعال", 'DeleteDT')]
            ]
            await db.execute("SELECT * FROM Tasks")
            Tasks = await db.fetchall()
            for i in Tasks:
                n_buttons.append(
                    [
                        Button.inline('▶️' if i[9] == 1 else '❌', f'RunTask:{i[0]}'),
                        Button.inline('✅' if i[9] == 1 else '❌', f'TasksStatus:{i[0]}'),
                        Button.inline(f"{i[1]} 🔖", f'OpenTask:{i[0]}')
                    ]
                )
                n_buttons.append(
                    [
                        Button.inline('❌⏳' if i[6] == 0 else f'⏳ {int(int(i[6]) - Ti)} ثانیه', f'SchTask:{i[0]}'),
                    ]
                )
            await client.send_message(user_id, '📑 لیست تسک‌های ثبت شده جهت ارسال و زمان‌بندی:', buttons=n_buttons)

        if user_data['Step'].startswith('EditTask'):
            hde = user_data['Step'].split(':')
            hcode = hde[1]
            await db.execute("SELECT * FROM Tasks WHERE `Id` = %s", (hcode,))
            TSK = await db.fetchall()
            if db.rowcount == 1:
                await db.execute('UPDATE `Tasks` SET `Name` = %s WHERE `Id` = %s', (text, hcode))
                await dbc.commit()
                await client.send_message(user_id, '💬 نام جدید تسک اعمال شد.', buttons=hok)
                await set_step(dbc, user_id, 'none')

        if user_data['Step'].startswith('EditName'):
            hde = user_data['Step'].split(':')
            hcode = hde[1]
            await db.execute("SELECT * FROM Messages WHERE `Name` = %s", (hcode,))
            TSK = await db.fetchall()
            if db.rowcount > 0:
                await db.execute('UPDATE `Messages` SET `Display` = %s WHERE `Name` = %s', (text, hcode))
                await dbc.commit()
                await client.send_message(user_id, '💬 نام جدید ردیف پیامی اعمال شد.', buttons=hok)
                await set_step(dbc, user_id, 'none')

        if user_data['Step'].startswith('RenameRadif'):
            hde = user_data['Step'].split(':')
            hcode = hde[1]
            await db.execute("SELECT * FROM Messages WHERE `Name` = %s", (hcode,))
            TSK = await db.fetchall()
            if db.rowcount > 0:
                await db.execute('UPDATE `Messages` SET `Display` = %s WHERE `Name` = %s', (text, hcode))
                await dbc.commit()
                await client.send_message(user_id, '💬 نام جدید ردیف پیامی اعمال شد.', buttons=hok)
                await set_step(dbc, user_id, 'none')

        if user_data['Step'].startswith('DeleteRadif'):
            hde = user_data['Step'].split(':')
            hcode = hde[1]
            await db.execute("SELECT * FROM Messages WHERE `Name` = %s", (hcode,))
            TSK = await db.fetchall()
            if db.rowcount > 0:
                if text == '1':
                    await db.execute('DELETE FROM `Messages` WHERE `Name` = %s', (hcode, ))
                    await dbc.commit()
                    await client.send_message(user_id, '💬 ردیف حذف شد.', buttons=hok)
                    await set_step(dbc, user_id, 'none')

        if user_data['Step'].startswith('SchTask'):
            hde = user_data['Step'].split(':')
            hcode = hde[1]
            await db.execute("SELECT * FROM Tasks WHERE `Id` = %s", (hcode,))
            TSK = await db.fetchall()
            if db.rowcount == 1:
                times = text.split("\n")
                await db.execute('DELETE FROM `Timer` WHERE `TID` = %s', (hcode,))
                await dbc.commit()
                for time in times:
                    await db.execute('INSERT INTO `Timer` VALUES (0, %s, %s, %s)', (hcode, int(time.strip()), 0))
                await dbc.commit()
                await client.send_message(user_id, f'💬 زمان بندی تسک تنظیم شد.', buttons=hok)
                await set_step(dbc, user_id, 'none')

        if user_data['Step'] == 'GetFinal':
            OPT = text.split("\n")
            udata = json.loads(user_data['Data'])
            groups = {}
            if OPT[0].isdigit():
                for i in OPT[1:]:
                    link = await send_request('createChatInviteLink', {'chat_id': i})
                    if link['ok']:
                        groups[link['result']['invite_link']] = int(i[4:])
                    else:
                        await client.send_message(user_id, '⚠️ خطایی رخ داده است.')
                        return False
                await db.execute("INSERT INTO Tasks VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (
                    Tools.generate_hash(8),
                    json.dumps(udata['Sessions']),
                    udata['Messages'][0],
                    json.dumps(groups),
                    Ti,
                    0,
                    user_id,
                    OPT[0],
                    0
                ))
                await dbc.commit()
                await client.send_message(user_id, '💬 عملیات انجام شد؛ صفحهء اصلی.', buttons=hok)
                await set_step(dbc, user_id, 'none')
            else:
                await client.send_message(user_id, '⚠️ خطایی رخ داده است.')


@client.on(events.CallbackQuery())
async def app(event):

    dbc = await get_db_connection()

    async with dbc.cursor() as db:

        user_id = event.sender_id
        Ti = time.time()
        data = str(event.data.decode('utf-8'))

        await db.execute("SELECT * FROM Users WHERE `User` = %s", (user_id,))
        user_d = await db.fetchall()
        user_data = {
            'Id': user_d[0][0],
            'User': user_d[0][1],
            'Step': user_d[0][2],
            'Ti': user_d[0][3],
            'Data': user_d[0][4]
        }

        if data.startswith("MessageConfig"):
            hcode = int(data.split(':')[1])
            n_buttons = []
            if hcode == -1:
                await db.execute("SELECT * FROM Messages ORDER BY `Name` DESC LIMIT 1")
                end_e = await db.fetchone()
                hcode = end_e[1] - 1
            for i in range(20):
                n_buttons.append(Button.inline(f"🔖 {i + 1}", f'EditMessage:{i}:{hcode + 1}'))
            n_buttons = Tools.array_chunk(n_buttons, 5)
            n_buttons.append([
                Button.inline(f"💢 تغییر نام", f'EditName:{hcode + 1}')
            ])
            n_buttons.append([
                Button.inline(f"⏪", f'MessageConfig:0'),
                Button.inline(f"⬅️" if hcode > 0 else '', f'MessageConfig:{hcode - 1}'),
                Button.inline(f"➡️", f'MessageConfig:{hcode + 1}'),
                Button.inline(f"⏩", f'MessageConfig:-1')
            ])
            await event.answer(f'ردیف {hcode + 1}')
            await event.edit(f'📑 جایگاه اکانت مورد نظر را انتخاب کنید (ردیف {hcode + 1}):', buttons=n_buttons)

        if data.startswith("ProMessageConfig"):
            cd = int(data.split(':')[1])
            await db.execute(f"SELECT DISTINCT `Name`, `Display` FROM Messages WHERE `Name` LIKE %s LIMIT 21 OFFSET {cd*20}", ('Pro%',))
            Messages = await db.fetchall()
            n_buttons = []
            for i in Messages:
                n_buttons.append(Button.inline(f"✏️ {i[1]}", f'RenameRadif:{i[0]}'))
                n_buttons.append(Button.inline(f"❌ {i[1]}", f'DeleteRadif:{i[0]}'))
            n_buttons = Tools.array_chunk(n_buttons, 2)
            td = []
            if cd > 0: td.append(Button.inline('صفحه قبلی ⬅️', f'ProMessageConfig:{cd - 1}'))
            if len(Messages) > 20: td.append(Button.inline('➡️ صفحه بعدی', f'ProMessageConfig:{cd + 1}'))
            if len(td) > 0: n_buttons.append(td)
            n_buttons.append([
                Button.inline(f"🔶 ثبت ردیف جدید", f'NewRadif'),
            ])
            await event.edit('📑 عملیات مورد نظر را انتخاب کنید:', buttons=n_buttons)

        if data == 'NewRadif':
            await db.execute('SELECT * FROM `Sessions` WHERE `Hash` = %s', ('Done',))
            Acc = await db.fetchall()
            BT = []
            if len(Acc) > 0:
                for i in range(len(Acc) // 20 + 1 if len(Acc) % 20 != 0 else len(Acc) // 20):
                    BT.append([
                        Button.inline('✖️' + str(i+1), f'NRChooseAcc:{i}'),
                    ])
            else:
                BT.append([Button.inline('⚠️ اکانت یافت نشد.', '#')])
            await event.edit("📱 دسته‌بندی اکانت‌های مورد نظر را انتخاب کنید:", buttons=BT)

        if data.startswith("RenameRadif"):
            sce = data.split(':')
            scode = sce[1]
            await set_step(dbc, user_id, f'RenameRadif:{scode}')
            await event.edit(f'نام جدید را ارسال کنید:')

        if data.startswith("DeleteRadif"):
            sce = data.split(':')
            scode = sce[1]
            await set_step(dbc, user_id, f'DeleteRadif:{scode}')
            await event.edit(f'برای حذف عدد 1 را ارسال کنید:')

        if data.startswith("NRChooseAcc"):
            sce = data.split(':')
            scode = int(sce[1])
            await db.execute(f"SELECT DISTINCT `Name` FROM Messages ORDER BY `Id` DESC LIMIT 1")
            lastone = await db.fetchall()
            if lastone:
                if str(lastone[0][0]).startswith('Pro'):
                    newname = int(str(lastone[0][0])[3:])+1
                else:
                    newname = 1
            else:
                newname = 1
            await db.execute(f'SELECT * FROM `Sessions` WHERE `Hash` = %s LIMIT 20 OFFSET {scode*20}', ('Done',))
            Acc = await db.fetchall()
            n_buttons = []
            for i in Acc:
                n_buttons.append(Button.inline(f"{i[1]}", f'SetMessage:{i[0]}:Pro{newname}'))
            n_buttons = Tools.array_chunk(n_buttons, 3)
            await event.edit(f'📑 اکانت مورد نظر را انتخاب کنید (ردیف {newname}):', buttons=n_buttons)

        if data.startswith("EditMessage"):
            sce = data.split(':')
            scode = int(sce[1])
            await set_step(dbc, user_id, f'GetMessages:{scode}:{sce[2]}')
            await client.send_message(user_id, f'📬 پیام‌های خود را به ترتیب ارسال کنید (اکانت {scode + 1} از ردیف {sce[2]}):', buttons=[
                [Button.text("🔄 ریست کردن", resize=True)],
                [Button.text("بازگشت", resize=True)]
            ])

        if data.startswith("SetMessage"):
            sce = data.split(':')
            scode = int(sce[1])
            await db.execute('SELECT * FROM `Sessions` WHERE `Id` = %s', (scode,))
            result = await db.fetchone()
            name = result[1]
            await set_step(dbc, user_id, f'SetMessages:{scode}:{sce[2]}')
            await client.send_message(user_id, f'📬 پیام‌های خود را به ترتیب ارسال کنید (اکانت {name}):', buttons=[
                [Button.text("🔄 ریست کردن", resize=True)],
                [Button.text("بازگشت", resize=True)]
            ])

        if data.startswith("EditName"):
            sce = data.split(':')
            scode = int(sce[1])
            await set_step(dbc, user_id, f'EditName:{scode}')
            await client.send_message(user_id, f'نام جدید را ارسال کنید:', buttons=[
                [Button.text("بازگشت", resize=True)]
            ])

        if data.startswith("TasksStatus"):
            code = data.split(':')[1]
            await db.execute("SELECT * FROM Tasks WHERE `Id` = %s", (code,))
            TSK = (await db.fetchall())[0]
            if TSK[9] == 1:
                new = 0
            else:
                new = 1
            await db.execute('UPDATE `Tasks` SET `Status` = %s WHERE `Id` = %s', (new, code))
            await dbc.commit()
            data = 'TaskBack'

        if data.startswith("OpenTask"):
            code = data.split(':')[1]
            await set_step(dbc, user_id, f'EditTask:{code}')
            await event.edit("🔐 نام جدید تسک را ارسال کنید:")

        if data.startswith("SchTask"):
            code = data.split(':')[1]
            await set_step(dbc, user_id, f'SchTask:{code}')
            await event.edit("🔐 زمان های شروع تسک را بر حسب ساعت (فرمت 24 ساعته) و هر خط یک عدد ارسال کنید (مثال: 4 و 8 و 16 در هر خط: تسک 3 بار در ساعت های مشخص شده به وقت ایران اجرا خواهد شد):")

        if data.startswith("DeleteDT"):
            await db.execute("DELETE FROM Tasks WHERE `Status` = %s", (0,))
            await dbc.commit()
            data = 'TaskBack'

        if data == 'TaskBack':
            await set_step(dbc, user_id, 'TasksConfig')
            n_buttons = [
                [Button.inline("➕ ثبت تسک جدید", 'NewTask')],
                [Button.inline("🗑 حذف تسک‌های غیرفعال", 'DeleteDT')]
            ]
            await db.execute("SELECT * FROM Tasks")
            Tasks = await db.fetchall()
            for i in Tasks:
                n_buttons.append(
                    [
                        Button.inline('▶️' if i[9] == 1 else '❌', f'RunTask:{i[0]}'),
                        Button.inline('✅' if i[9] == 1 else '❌', f'TasksStatus:{i[0]}'),
                        Button.inline(f"{i[1]} 🔖", f'OpenTask:{i[0]}')
                    ]
                )
                n_buttons.append(
                    [
                        Button.inline('⏳', f'SchTask:{i[0]}'),
                    ]
                )
            await event.edit('📑 لیست تسک‌های ثبت شده جهت ارسال و زمان‌بندی:', buttons=n_buttons)

        if data.startswith("RunTask"):
            await event.answer("✅ شروع عملیات")
            TID = data.split(':')[1]
            await db.execute('SELECT * FROM `Tasks` WHERE `Id` = %s', (TID,))
            Task = (await db.fetchall())[0]
            Id, Name, Sessions, Messages, Peers, Create_Ti, RunTime, User, Sleep, Status = Task
            edit = await client.send_message(user_id, f'▶️ ذخیره سازی تسک {Name}...')
            groups = json.loads(Peers)
            Sessions = json.loads(Sessions)
            for S in Sessions:
                S = int(S)
                await db.execute(f"SELECT * FROM `Messages` WHERE `Name` = %s", (Messages,))
                Mess = await db.fetchall()
                if len(Mess) == 0: break
                sid = -1
                STi = int(time.time())
                for group in groups:
                    gid = f'-100{groups[group]}'
                    await send_request('setChatPermissions', {
                        'chat_id': gid,
                        'permissions': json.dumps({
                            'can_send_messages': True,
                            'can_send_photos': True,
                            'can_send_documents': True,
                        })
                    })
                for Mes in Mess:
                    for group in groups:
                        await db.execute('INSERT INTO `Queue` VALUES (0, %s, %s, %s, %s, %s, %s)', (Id, Mes[7], group, Mes[0], STi, user_id))
                    STi += Sleep
                await dbc.commit()
            await asyncio.sleep(2)
            await edit.edit(f'✅ ذخیره سازی {Name} تکمیل شد.')

        if data.startswith("ChooseAcc"):
            code = data.split(':')[1]
            udata = json.loads(user_data['Data'])
            if str(code) not in udata['Sessions']:
                udata['Sessions'] = [str(code)]
            else:
                udata['Sessions'].remove(str(code))
            jd = json.dumps(udata)
            await db.execute('UPDATE `Users` SET `Data` = %s WHERE `User` = %s', (jd, user_id))
            await dbc.commit()
            user_data['Data'] = jd
            data = 'NewTask:'

        if data.startswith("NewTask"):
            await set_step(dbc, user_id, 'TasksConfig')
            if data == 'NewTask':
                udata = {
                    'Sessions': [],
                    'Messages': [],
                    'Peers': [],
                    'Sleep': 0
                }
                jd = json.dumps(udata)
                await db.execute('UPDATE `Users` SET `Data` = %s WHERE `User` = %s', (jd, user_id))
                await dbc.commit()
            else:
                udata = json.loads(user_data['Data'])
            await db.execute('SELECT * FROM `Sessions` WHERE `Hash` = %s', ('Done',))
            Acc = await db.fetchall()
            BT = []
            if len(Acc) > 0:
                for i in range(len(Acc) // 20 + 1 if len(Acc) % 20 != 0 else len(Acc) // 20):
                    BT.append([
                        Button.inline('✅' if str(i) in udata['Sessions'] else '❌', f'ChooseAcc:{i}'),
                        Button.inline(str(i + 1) + ' 👥', f'ChooseAcc:{i}'),
                    ])
            else:
                BT.append([Button.inline('⚠️ اکانت یافت نشد.', '#')])
            BT.append([Button.inline('➡️ مرحله بعدی', 'ChooseMessage')])
            BT.append([Button.inline('بازگشت', 'TaskBack')])
            await event.edit("📱 دسته‌بندی اکانت‌های مورد نظر را انتخاب کنید:", buttons=BT)

        if data.startswith("ChooseMsg"):
            codei = data.split(':')
            code = codei[1]
            udata = json.loads(user_data['Data'])
            udata['Messages'] = [str(code)]
            jd = json.dumps(udata)
            await db.execute('UPDATE `Users` SET `Data` = %s WHERE `User` = %s', (jd, user_id))
            await dbc.commit()
            user_data['Data'] = jd
            data = f'ChooseMessage:{codei[2]}'

        if data.startswith("ChooseMessage"):
            await set_step(dbc, user_id, 'TasksConfig')
            cdi = data.split(':')
            if len(cdi) == 2:
                cd = int(cdi[1])
                await db.execute(f'SELECT DISTINCT `Name` FROM Messages LIMIT 51 OFFSET {50*cd}')
                MSG = await db.fetchall()
            else:
                cd = 0
                await db.execute('SELECT DISTINCT `Name` FROM Messages LIMIT 51')
                MSG = await db.fetchall()
            udata = json.loads(user_data['Data'])
            BT = []
            if len(MSG) > 0:
                for i in MSG:
                    await db.execute('SELECT * FROM Messages WHERE `Name` = %s LIMIT 1', (str(i[0]), ))
                    _i = await db.fetchone()
                    BT.append([
                        Button.inline(('✅' if str(i[0]) in udata['Messages'] else '❌')+str(_i[2])+' 📨'+str(i[0]), f'ChooseMsg:{i[0]}:{cd}'),
                    ])
            else:
                BT.append([Button.inline('⚠️ پیامی یافت نشد.', '#')])
            td = []
            if cd > 0: td.append(Button.inline('صفحه قبلی ⬅️', f'ChooseMessage:{cd-1}'))
            if len(MSG) > 50: td.append(Button.inline('➡️ صفحه بعدی', f'ChooseMessage:{cd+1}'))
            if len(td) > 0: BT.append(td)
            BT.append([Button.inline('مرحله قبلی ⬅️', 'NewTask:'), Button.inline('➡️ مرحله بعدی', 'ChoosePeers')])
            BT.append([Button.inline('بازگشت', 'TaskBack')])
            await event.edit("📱 دسته‌بندی پیام‌های مورد نظر را انتخاب کنید:", buttons=BT)

        if data.startswith("ChoosePeers"):
            await set_step(dbc, user_id, 'GetFinal')
            BT = [
                [Button.inline('مرحله قبلی ⬅️', 'ChooseMessage')],
                [Button.inline('بازگشت', 'TaskBack')]
            ]
            await event.edit("⚠️ در خط اول زمان انتظار بین هر دو ارسال و در خطوط بعدی لینک (مانند https://t.me/+TDfy555JRStiNTZk) یا Username (مانند @durov) بنویسید و ارسال کنید.", buttons=BT)

async def start():

    await client.start(bot_token=Info.Token)
    await asyncio.create_task(auto_run(5))
    await client.run_until_disconnected()

asyncio.run(start())
