"""
Conversation states for registration process
"""

from telegram.ext import ConversationHandler

# Registration states
(
    STATE_START,
    STATE_WEIGHT,
    STATE_HEIGHT,
    STATE_GENDER,
    STATE_ACTIVITY,
    STATE_CITY
) = range(6)

# Edit profile states
(
    STATE_EDIT_WEIGHT,
    STATE_EDIT_HEIGHT,
    STATE_EDIT_CITY
) = range(6, 9)