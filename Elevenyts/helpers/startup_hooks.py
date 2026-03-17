# Elevenyts/helpers/startup_hooks.py

from pyrogram.errors import UserAlreadyParticipant
import logging

from Elevenyts import app, logger  # app global hai __init__.py se

async def precheck_channels():
    """
    Bot start hone se pehle important channels join kar leta hai.
    """
    targets = ["@elevenyts", "@elevenytschats"]  # yaha apne channels daal dena ya config se load kar sakte ho

    for chan in targets:
        try:
            await app.join_chat(chan)
            logger.info(f"✓ Successfully joined {chan}")
        except UserAlreadyParticipant:
            logger.info(f"↻ Already a member of {chan}")
        except Exception as e:
            logger.warning(f"✗ Failed to join {chan}: {str(e)}")
