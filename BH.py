import os
from telethon.errors.rpcerrorlist import BadRequestError, SessionPasswordNeededError, RPCError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon import errors
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.account import GetPasswordRequest
import asyncio
import json
import traceback
import socks
import Tools


def create_client(name, api_id, api_hash, device_model, system_version, app_version, proxy_str=None, ssession=None):
    try:
        proxy = None
        if proxy_str:
            server, port, username, password = Tools.extract_proxy_info(proxy_str)
            proxy = (socks.SOCKS5, server, int(port), True, str(username), str(password))

        client = TelegramClient(
            StringSession(ssession) if ssession else f'Sessions/{name}',
            api_id,
            api_hash,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version,
            proxy=proxy
        )

        return client

    except Exception as e:
        print(f"[40] Error connecting client {name}: {e}")
        raise


async def connect_client(name, api_id, api_hash, device_model, system_version, app_version, proxy_str, ssession=None):
    client = create_client(
        name,
        api_id,
        api_hash,
        device_model,
        system_version,
        app_version,
        proxy_str,
        ssession
    )
    if client is False:
        raise "proxy error"
    else:
        try:
            if client.is_connected():
                return client
            else:
                await client.connect()
                return client
        except Exception as e:
            print(f"[-] Can't connect to {name}: {e}")
            return False

async def login(
        api_id,
        api_hash,
        name: str,
        phone: str,
        device_model: str,
        system_version: str,
        app_version: str,
        proxy_str: str = None,
        code: str = None,
        hash_code: str = None,
        password: str = None,
        sssid = None,
        photo = True
):
    client = await connect_client(name, api_id, api_hash, device_model, system_version, app_version, proxy_str, None)
    to_return = {"status": "nan"}
    if client:
        try:
            if not code:
                h_code = await client.send_code_request(phone)
                to_return = {"status": "code", "hash_code": h_code.phone_code_hash}
            if code and hash_code:
                await client.sign_in(phone=phone, code=code, phone_code_hash=hash_code)
                info = await client.get_me()
                if photo:
                    os.makedirs(f'UB/{sssid}', exist_ok=True)
                    cou = 0
                    async for photo in client.iter_profile_photos('me', limit=3):
                        cou += 1
                        file = await client.download_media(photo)
                        tdir = f'UB/{sssid}/{cou}{os.path.splitext(file)[1]}'
                        try:
                            os.remove(tdir)
                        except:
                            pass
                        os.rename(file, tdir)
                full_name = f"{info.first_name or ''} {info.last_name or ''}".strip()
                to_return = {"status": "ok", "id": info.id, "name": full_name, "Session": StringSession.save(client.session)}
        except BadRequestError as e:
            to_return = {"status": "error", "message": e}
        except SessionPasswordNeededError:
            if password:
                try:
                    await client.sign_in(password=password)
                    info = await client.get_me()
                    if photo:
                        os.makedirs(f'UB/{sssid}', exist_ok=True)
                        cou = 0
                        async for photo in client.iter_profile_photos('me', limit=3):
                            cou += 1
                            file = await client.download_media(photo)
                            tdir = f'UB/{sssid}/{cou}{os.path.splitext(file)[1]}'
                            try:
                                os.remove(tdir)
                            except:
                                pass
                            os.rename(file, tdir)
                    full_name = f"{info.first_name or ''} {info.last_name or ''}".strip()
                    to_return = {"status": "ok", "id": info.id, "name": full_name, "Session": StringSession.save(client.session)}
                except Exception as e:
                    to_return = {"status": "error", "message": e}
            else:
                to_return = {"status": "password"}
        except RPCError as e:
            to_return = {"status": "error", "message": e}
        except Exception as e:
            to_return = {"status": "error", "message": e}
        finally:
            await client.disconnect()
    return to_return

