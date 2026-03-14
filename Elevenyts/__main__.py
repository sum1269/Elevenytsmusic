import asyncio
import importlib
import sys
import os
from aiohttp import web  # Add aiohttp to requirements.txt

from pyrogram import idle

# Raise the file descriptor limit on Linux to avoid "[Errno 24] Too many open files"
# when serving many groups concurrently (each audio stream + ffmpeg probe opens FDs).
if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass

from Elevenyts import (tune, app, config, db,
                   logger, stop, userbot, yt)
from Elevenyts.plugins import all_modules


# Simple HTTP server for Render health checks
async def health_check(request):
    return web.Response(text="OK", status=200)


async def start_http_server():
    """Start a simple HTTP server on the port specified by Render"""
    port = int(os.environ.get("PORT", 8080))  # Render sets PORT env variable
    app_web = web.Application()
    app_web.router.add_get("/", health_check)
    app_web.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)  # Bind to all interfaces
    await site.start()
    logger.info(f"🌐 HTTP server started on port {port} for Render health checks")
    return runner


async def main():
    http_runner = None
    try:
        # Step 0: Start HTTP server for Render (must be first)
        http_runner = await start_http_server()
        
        # Step 1: Connect to MongoDB database
        await db.connect()
        
        # Step 2: Start the main bot client
        await app.boot()
        
        # Step 3: Start assistant/userbot clients (for joining voice chats)
        await userbot.boot()
        
        # Step 4: Initialize voice call handler
        await tune.boot()

        # Step 5: Load all plugin modules (commands like /play, /pause, etc.)
        for module in all_modules:
            try:
                importlib.import_module(f"Elevenyts.plugins.{module}")
            except Exception as e:
                logger.error(f"Failed to load plugin {module}: {e}", exc_info=True)
        logger.info(f"🔌 Loaded {len(all_modules)} plugin modules.")

        # Step 6: Download YouTube cookies if URLs are provided (for age-restricted videos)
        if config.COOKIES_URL:
            try:
                await yt.save_cookies(config.COOKIES_URL)
            except Exception as e:
                logger.error(f"Failed to download cookies: {e}")

        # Step 7: Load sudo users and blacklisted users from database
        sudoers = await db.get_sudoers()
        app.sudoers.update(sudoers)  # Add sudo users to set
        app.sudo_filter.update(sudoers)  # Add sudo users to filter
        app.bl_users.update(await db.get_blacklisted())  # Add blacklisted users to filter
        logger.info(f"👑 Loaded {len(app.sudoers)} sudo users.")
        logger.info("\n🎉 Bot started successfully! Ready to play music! 🎵\n")

        # Step 8: Keep the bot running (press Ctrl+C to stop)
        try:
            await idle()
        except KeyboardInterrupt:
            logger.info("Received stop signal...")
        except Exception as e:
            logger.error(f"Error during idle: {e}", exc_info=True)
        
        # Step 9: Cleanup and shutdown when bot is stopped
        await stop()
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        raise
    finally:
        # Cleanup HTTP server
        if http_runner:
            await http_runner.cleanup()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except SystemExit as e:
        logger.error(f"Bot exited with system error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error caused bot to stop: {e}", exc_info=True)
        # Don't raise - allow clean shutdown
    finally:
        # Ensure cleanup happens
        try:
            if loop.is_running():
                loop.stop()
        except:
            pass
