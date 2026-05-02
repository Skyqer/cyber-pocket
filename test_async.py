import asyncio
import os

async def run():
    npm_path = os.path.expandvars(r'%APPDATA%\npm\gemini.cmd')
    safe_prompt = "Hello\n\nWorld"
    try:
        p = await asyncio.create_subprocess_exec(
            npm_path, '-p', safe_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await p.communicate()
        print("Success")
    except Exception as e:
        print(f"EXCEPTION: {repr(e)}")

asyncio.run(run())
