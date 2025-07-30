from telethon.sync import TelegramClient, events
from telethon.tl.custom import Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
import aiomysql
import aiohttp
import asyncio
import time
import json
import os
import re
import subprocess
import threading
import platform
import random
import glob
import Tools
import BH
import Info


if platform.system() != "Windows":
    pid_file = 'CPID'
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

stop_event = threading.Event()

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

async def irequest(url, proxy=None, timeout=10):
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

async def sub_run(tid):
    print(f'Sub Run Task: {tid}')
    dbc = await get_db_connection()
    async with dbc.cursor() as db:

        await db.execute('SELECT * FROM `Tasks` WHERE `Id` = %s', (tid,))
        Task = (await db.fetchall())[0]
        Id, Name, Sessions, Messages, Peers, Create_Ti, RunTime, User, Sleep, Status = Task

        groups = json.loads(Peers)
        Sessions = json.loads(Sessions)

        if Messages.startswith('Pro'):
            for S in Sessions:
                S = int(S)

                await db.execute(f"SELECT DISTINCT `SID` FROM `Queue` WHERE `TID` = %s", (tid,))
                Active_S = await db.fetchall()

                Accounts = {}
                for ASI in Active_S:
                    new = False
                    while True:
                        await db.execute(f"SELECT * FROM `Sessions` WHERE `Id` = %s", (ASI,))
                        sts = await db.fetchall()
                        ASIID = int(ASI[0])
                        session = list(sts[0])
                        print(f'Session {session[0]}...')
                        Proxy = session[8]
                        url = 'https://api.redgenius.top/IP'
                        pr_error = 0
                        try:
                            _ = await irequest(url, proxy=Proxy)
                        except ProxyError as e:
                            while True:
                                print('Change Proxy...')
                                pr_error += 1
                                if pr_error >= 3:
                                    pr_error = 0
                                    await send_request('SendMessage', {
                                        'chat_id': 609406239,
                                        'text': 'ProxyError:3'
                                    })
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
                        if pr_error > 0:
                            await send_request('SendMessage', {
                                'chat_id': 609406239,
                                'text': '✅ Connected.'
                            })
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
                        if aclient:
                            if await aclient.get_me():
                                if new:
                                    await aclient(UpdateProfileRequest(
                                        first_name=session[1]
                                    ))
                                    files = sorted(
                                        glob.glob(f'UB/{session[0]}/*'),
                                        key=os.path.getmtime,
                                        reverse=True
                                    )
                                    for i in files:
                                        file2 = await aclient.upload_file(i)
                                        await aclient(UploadProfilePhotoRequest(file=file2))
                                        await asyncio.sleep(1)
                                Accounts[ASIID] = (aclient, session)
                                print(f'Session {ASIID} Activated.')
                                break
                            else:
                                # Accounts[Act[0]] = (None, session)
                                error = True
                                print(f'Session {ASIID} Disabled.')
                        else:
                            # Accounts[Act[0]] = (None, session)
                            error = True
                            print(f'Session {ASIID} Disabled.')
                        if error:
                            print('Change Account...')
                            await db.execute(f"SELECT * FROM `SessionsB` WHERE `Hash` = %s ORDER BY RAND() LIMIT 1", ('Done',))
                            result = await db.fetchall()
                            if db.rowcount > 0:
                                new = list(result[0])
                                await db.execute(
                                    "UPDATE `Sessions` SET `Proxy` = %s, `SSession` = %s, `User` = %s WHERE `Id` = %s",
                                    (new[8], new[13], new[9], session[0])
                                )
                                await dbc.commit()
                                await db.execute('DELETE FROM `SessionsB` WHERE `Id` = %s', (new[0], ))
                                await dbc.commit()
                                await db.execute(f"SELECT * FROM `Sessions` WHERE `Id` = %s", (session[0],))
                                session = list((await db.fetchall())[0])
                                new = True
                            else:
                                await db.execute('DELETE FROM `History` WHERE `TID` = %s', (tid,))
                                await db.execute('DELETE FROM `Queue` WHERE `TID` = %s', (tid,))
                                await dbc.commit()
                                await send_request('SendMessage', {
                                    'chat_id': User,
                                    'text': '⚠️ Backup Account Error.'
                                })
                                return

                await db.execute('SELECT * FROM `Queue` WHERE `TID` = %s', (tid,))
                total_queue = await db.fetchall()
                la = 0
                for i in total_queue:
                    if stop_event.is_set():
                        continue
                    await db.execute('SELECT * FROM `Messages` WHERE `Id` = %s', (i[4],))
                    Mes = await db.fetchone()
                    aclient, session = Accounts[int(i[2])]
                    sid = Mes[7]
                    if la >= len(groups):
                        la = 0
                        await asyncio.sleep(Sleep)
                    la += 1
                    ct_url = Tools.normalize_link(i[3])
                    try:
                        if groups[i[3]] != '0':
                            entity = await aclient.get_entity(int(f'-100{groups[i[3]]}'))
                            join_status = {
                                "status": "ok",
                                "id": entity.id,
                            }
                        else:
                            raise BaseException
                    except BaseException as e:
                        print(193, e)
                        try:
                            try:
                                chat = await aclient.get_entity(f"t.me/joinchat/{ct_url}")
                                join_status = {
                                    "status": "ok",
                                    "id": chat.id,
                                }
                            except:
                                try:
                                    if ct_url[0] == '@':
                                        result = await aclient(JoinChannelRequest(ct_url))
                                    else:
                                        result = await aclient(ImportChatInviteRequest(ct_url))
                                except BaseException as e:
                                    print(210, e)
                                chat = await aclient.get_entity(f"t.me/joinchat/{ct_url}")
                                join_status = {
                                    "status": "ok",
                                    "id": chat.id,
                                }
                        except BaseException as e:
                            print(219, e)
                            await db.execute('DELETE FROM `Queue` WHERE `Id` = %s', (i[0],))
                            await dbc.commit()
                            continue
                    if join_status['status'] == "ok":
                        groups[i[3]] = join_status['id']
                        await db.execute('UPDATE `Tasks` SET `Peers` = %s WHERE `Id` = %s', (json.dumps(groups), Id))
                        await dbc.commit()
                        await db.execute('SELECT * FROM Messages WHERE `MID` = %s', (Mes[9],))
                        rp_raw = await db.fetchone()
                        rp = None
                        if rp_raw:
                            await db.execute('SELECT * FROM History WHERE `MID` = %s AND `Peer` = %s AND `TID` = %s', (
                                rp_raw[0],
                                join_status['id'],
                                tid
                            ))
                            rpd = await db.fetchone()
                            if rpd:
                                rp = int(rpd[3])
                            else:
                                rp = None
                        else:
                            rp = None
                        try:
                            if Mes[3] == 'Text':
                                res = await aclient.send_message(join_status['id'], Mes[4], reply_to=rp)
                            else:
                                res = await aclient.send_file(join_status['id'], Mes[5], caption=Mes[4], reply_to=rp)
                            await db.execute('DELETE FROM `Queue` WHERE `Id` = %s', (i[0],))
                            await dbc.commit()
                            await db.execute('INSERT INTO `History` VALUES (0, %s, %s, %s, %s)', (
                                Mes[0],
                                join_status['id'],
                                res.id,
                                tid
                            ))
                            await dbc.commit()
                            print(f'Message {Mes[0]} Sent.')
                        except:
                            print(244)
                            pass
                else:
                    await db.execute('DELETE FROM `History` WHERE `TID` = %s', (tid,))
                    await db.execute('DELETE FROM `Queue` WHERE `TID` = %s', (tid,))
                    await dbc.commit()
                    for group in groups:
                        gid = f'-100{groups[group]}'
                        # await send_request('setChatPermissions', {
                        #     'chat_id': gid,
                        #     'permissions': json.dumps({
                        #         'can_send_messages': False,
                        #         'can_send_photos': False,
                        #         'can_send_documents': False,
                        #     })
                        # })
                    await send_request('SendMessage', {'chat_id': User, 'text': f'✅ تسک {Name} تکمیل/متوقف شد.\n/close_{tid}'})
                for i in Accounts:
                    aclient, session = Accounts[i]
                    if aclient:
                        print(f'Session {i} disconnected.')
                        await aclient.disconnect()
        else:
            for S in Sessions:
                S = int(S)

                await db.execute(f"SELECT DISTINCT `SID` FROM `Queue` WHERE `TID` = %s", (tid,))
                Active_S = await db.fetchall()

                await db.execute(f"SELECT * FROM `Sessions` WHERE `Hash` = %s LIMIT 20 OFFSET {S * 20}", ('Done', ))
                sts = await db.fetchall()

                Accounts = {}
                for ASI in Active_S:
                    while True:
                        ASIID = int(ASI[0])
                        session = list(sts[ASIID])
                        print(f'Session {session[0]}...')
                        Proxy = session[8]
                        url = 'https://api.redgenius.top/IP'
                        pr_error = 0
                        try:
                            _ = await irequest(url, proxy=Proxy)
                        except ProxyError as e:
                            while True:
                                print('Change Proxy...')
                                pr_error += 1
                                if pr_error >= 3:
                                    pr_error = 0
                                    await send_request('SendMessage', {
                                        'chat_id': 609406239,
                                        'text': 'ProxyError:3'
                                    })
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
                        if pr_error > 0:
                            await send_request('SendMessage', {
                                'chat_id': 609406239,
                                'text': '✅ Connected.'
                            })
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
                        if aclient:
                            if await aclient.get_me():
                                Accounts[ASIID] = (aclient, session)
                                print(f'Session {ASIID} Activated.')
                                break
                            else:
                                # Accounts[Act[0]] = (None, session)
                                error = True
                                print(f'Session {ASIID} Disabled.')
                        else:
                            # Accounts[Act[0]] = (None, session)
                            error = True
                            print(f'Session {ASIID} Disabled.')
                        if error:
                            print('Change Account...')
                            await db.execute('UPDATE `Sessions` SET `Hash` = %s WHERE `Id` = %s', ('Error140', session[0]))
                            await dbc.commit()
                            await db.execute(f"SELECT * FROM `Sessions` WHERE `Hash` = %s ORDER BY `Id` DESC LIMIT 1", ('Done',))
                            new = list((await db.fetchall())[0])
                            await db.execute(f"SELECT * FROM `Sessions` WHERE `Id` = %s", (session[0],))
                            old = list((await db.fetchall())[0])
                            if new[0] > old[0]:
                                print(f'RV: {new[1]} - {session[1]}')
                                ex_old = old[1:] + [new[0]]
                                ex_new = new[1:] + [old[0]]
                                await db.execute(
                                    "UPDATE `Sessions` SET `Name` = %s, `API_ID` = %s, `API_Hash` = %s, `Phone` = %s, "
                                    "`Device_Model` = %s, `System_Version` = %s, `App_Version` = %s, "
                                    "`Proxy` = %s, `User` = %s, `Hash` = %s, `Status` = %s, `NID` = %s, `SSession` = %s "
                                    "WHERE `Id` = %s",
                                    ex_old
                                )
                                await db.execute(
                                    "UPDATE `Sessions` SET `Name` = %s, `API_ID` = %s, `API_Hash` = %s, `Phone` = %s, "
                                    "`Device_Model` = %s, `System_Version` = %s, `App_Version` = %s, "
                                    "`Proxy` = %s, `User` = %s, `Hash` = %s, `Status` = %s, `NID` = %s, `SSession` = %s "
                                    "WHERE `Id` = %s",
                                    ex_new
                                )
                                await dbc.commit()
                                await db.execute(f"SELECT * FROM `Sessions` WHERE `Id` = %s", (session[0],))
                                session = list((await db.fetchall())[0])
                            else:
                                break

                await db.execute('SELECT * FROM `Queue` WHERE `TID` = %s', (tid,))
                total_queue = await db.fetchall()
                la = 0
                for i in total_queue:
                    if stop_event.is_set():
                        continue
                    await db.execute('SELECT * FROM `Messages` WHERE `Id` = %s', (i[4],))
                    Mes = await db.fetchone()
                    aclient, session = Accounts[int(i[2])]
                    sid = Mes[7]
                    if la >= len(groups):
                        la = 0
                        await asyncio.sleep(Sleep)
                    la += 1
                    ct_url = Tools.normalize_link(i[3])
                    try:
                        if groups[i[3]] != '0':
                            entity = await aclient.get_entity(int(f'-100{groups[i[3]]}'))
                            join_status = {
                                "status": "ok",
                                "id": entity.id,
                            }
                        else:
                            raise BaseException
                    except BaseException as e:
                        print(193, e)
                        try:
                            try:
                                chat = await aclient.get_entity(f"t.me/joinchat/{ct_url}")
                                join_status = {
                                    "status": "ok",
                                    "id": chat.id,
                                }
                            except:
                                try:
                                    if ct_url[0] == '@':
                                        result = await aclient(JoinChannelRequest(ct_url))
                                    else:
                                        result = await aclient(ImportChatInviteRequest(ct_url))
                                except BaseException as e:
                                    print(210, e)
                                chat = await aclient.get_entity(f"t.me/joinchat/{ct_url}")
                                join_status = {
                                    "status": "ok",
                                    "id": chat.id,
                                }
                        except BaseException as e:
                            print(219, e)
                            await db.execute('DELETE FROM `Queue` WHERE `Id` = %s', (i[0], ))
                            await dbc.commit()
                            continue
                    if join_status['status'] == "ok":
                        groups[i[3]] = join_status['id']
                        await db.execute('UPDATE `Tasks` SET `Peers` = %s WHERE `Id` = %s', (json.dumps(groups), Id))
                        await dbc.commit()
                        await db.execute('SELECT * FROM Messages WHERE `MID` = %s', (Mes[9], ))
                        rp_raw = await db.fetchone()
                        rp = None
                        if rp_raw:
                            await db.execute('SELECT * FROM History WHERE `MID` = %s AND `Peer` = %s AND `TID` = %s', (
                                rp_raw[0],
                                join_status['id'],
                                tid
                            ))
                            rpd = await db.fetchone()
                            if rpd:
                                rp = int(rpd[3])
                            else:
                                rp = None
                        else:
                            rp = None
                        try:
                            if Mes[3] == 'Text':
                                res = await aclient.send_message(join_status['id'], Mes[4], reply_to=rp)
                            else:
                                res = await aclient.send_file(join_status['id'], Mes[5], caption=Mes[4], reply_to=rp)
                            await db.execute('DELETE FROM `Queue` WHERE `Id` = %s', (i[0],))
                            await dbc.commit()
                            await db.execute('INSERT INTO `History` VALUES (0, %s, %s, %s, %s)', (
                                Mes[0],
                                join_status['id'],
                                res.id,
                                tid
                            ))
                            await dbc.commit()
                            print(f'Message {Mes[0]} Sent.')
                        except:
                            print(244)
                            pass
                else:
                    await db.execute('DELETE FROM `History` WHERE `TID` = %s', (tid,))
                    await db.execute('DELETE FROM `Queue` WHERE `TID` = %s', (tid,))
                    await dbc.commit()
                    await send_request('SendMessage', {'chat_id': User, 'text': f'✅ تسک {Name} تکمیل/متوقف شد.\n/close_{tid}'})
                for i in Accounts:
                    aclient, session = Accounts[i]
                    if aclient:
                        print(f'Session {i} disconnected.')
                        await aclient.disconnect()

        await dbc.ensure_closed()


def run_in_thread(tid):
    asyncio.run(sub_run(tid))

async def run():
    st_t = []
    to_wait = []
    while True:
        dbc = await get_db_connection()
        async with dbc.cursor() as db:
            await db.execute('SELECT DISTINCT `TID` FROM `Queue`')
            tasks = await db.fetchall()
            for task in tasks:
                if task[0] not in st_t:
                    thread = threading.Thread(target=run_in_thread, args=(task[0], ))
                    thread.start()
                    to_wait.append(thread)
                    st_t.append(task[0])
            await dbc.ensure_closed()
        await asyncio.sleep(2)
        if os.path.exists('stop'):
            print("Stop file detected! Stopping...")
            stop_event.set()
            os.remove('stop')
            for prc in to_wait:
                prc.join()
            to_wait = []
            st_t = []
            stop_event.clear()
            print("Prc Stopped.")

asyncio.run(run())
