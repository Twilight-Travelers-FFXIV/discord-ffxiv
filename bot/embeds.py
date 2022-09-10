"""Embed Definitions"""


# Helper function to generate embeds
from typing import List


def _embed_activity(activities: List[List[str]]):
    """Flattens out activity list to formatted embed value

    Args:
        activities (List[List[str]]): First level list is rows, second level is activities by emoji shortcut.

    Returns:
        Expanded activity ready for use as embedding value.
    """
    return "\n".join(
        [
            "<:space:975856889466351626>".join(
                [
                    f"{activity} {emoji_activity_map.get(activity)}"
                    for activity in activities_row
                ]
            )
            for activities_row in activities
        ]
    )


# All possible events:
emoji_activity_map = {
    ":racehorse:": "Pony farm (lv50)",
    ":bird:": "Bird farm (lv60)",
    ":wolf:": "Wolf farm (lv70)",
    ":dragon_face:": "Dragon farm (lvl80)",
    "<:Purplecrystal:973233130758606848>": "||The Dark Inside EX||",
    ":crystal_ball:": "||The Mothercrystal EX||",
    ":satellite:": "||The Final Day EX||",
    ":ladder:": "Binding coils of Bahamut (lvl50)",
    ":office:": "Alexander Raid (lvl60)",
    ":trackball:": "Omega Raid (lvl70)",
    ":earth_americas:": "Eden Raid (lvl80)",
    ":volcano:": "The Unending Coil of Bahamut (Ultimate)",
    ":ringed_planet:": "Alexander (Savage)",
    ":imp:": "Omega Raid (Savage)",
    ":dvd:": "Eden (Savage)",
    "<:ffxivmapfate:975863641402400788>": "FATE FARMING (lvl80)",
    "<:ffxivmapbluemage:973233132079816724>": "BLUE MAGE (Spells)",
    "<:ffxivinhunts:973233132188868698>": "A⋆- S⋆ Rank Hunting (lvl90)",
    "<:ffxivmissionicon:973233132130140170>": "Bozjan Southern Front (lvl80)",
    "<:ffxivintreasurehunt:973233132063035482>": "Treasure hunt (lvl90)",
    ":moneybag:": "Treasure hunt (lvl60,70,80)",
}

day_map = {
    ":red_square:": "Friday",
    ":yellow_square:": "Saturday",
    ":white_large_square:": "Sunday",
}

raid_activity_poll = {
    "before_embed": "<:ffxivautoleft:973233131811377232> **TWILIGHT TRAVELERS RAID ACTIVITY VOTING POLL** "
    "<:ffxivautoright:973233131849130004> <:fffxivmapfight:973233131480035389> @everyone\n"
    "This VOTE is open for all our FC-members to choose their preference for the next FC-Raid/Trial activity.\n"
    "You can vote for your desired activity by clicking on one of the below emoji's to vote. (multiple voting is "
    "allowed)\n Remember that this is not the sign-up form yet, that will be posted when voting ends, every Wednesday.",
    "after_embed": "<:hand:973233132369215568>**The FC's activity will be held on Friday, Saturday or Sunday. For now, "
    "we will only organize one activity a week. This can be upscaled to 2 per week if we see that there "
    "is a lot of interest in FC activities.**\n\n Please specify your preferred day: \n:red_square: Friday, "
    "\n:yellow_square: Saturday, \n:white_large_square: Sunday",
    "embeds": [
        {
            "color": 1752220,
            "footer": {
                "text": "Please vote on this message for any of the above activities."
            },
            "fields": [
                {
                    "name": "**__ARR/HW/SB/SHB FARMS <:ffxivintrial:973233132415385710>__**",
                    "value": _embed_activity(
                        [[":racehorse:", ":bird:"], [":wolf:", ":dragon_face:"]]
                    ),
                },
                {
                    "name": "**__ENDWALKER FARMS (lvl90) :milky_way:__**",
                    "value": _embed_activity(
                        [
                            ["<:Purplecrystal:973233130758606848>", ":crystal_ball:"],
                            [":satellite:"],
                        ]
                    ),
                },
            ],
        },
        {
            "color": 1752220,
            "footer": {
                "text": "Please vote on this message for any of the above activities."
            },
            "fields": [
                {
                    "name": "**__RAIDS <:ffxivinraids:973233131639423037>__**",
                    "value": _embed_activity(
                        [[":ladder:", ":office:"], [":trackball:", ":earth_americas:"]]
                    ),
                },
                {
                    "name": "**__SAVAGE/ULTIMATE/UNREAL CONTENT <:ffxivinhighendraids:973233131828154378>__**",
                    "value": _embed_activity(
                        [[":volcano:", ":ringed_planet:"], [":imp:", ":dvd:"]]
                    ),
                },
                {
                    "name": "**__EXTRA'S <:ffxivstoryicon:975863482429898803>__**",
                    "value": _embed_activity(
                        [
                            [
                                "<:ffxivmapfate:975863641402400788>",
                                "<:ffxivmapbluemage:973233132079816724>",
                            ],
                            [
                                "<:ffxivinhunts:973233132188868698>",
                                "<:ffxivmissionicon:973233132130140170>",
                            ],
                            [
                                "<:ffxivintreasurehunt:973233132063035482>",
                                ":moneybag:",
                            ],
                        ]
                    ),
                },
            ],
        },
    ],
}

ROLES_REACTIONS = [
    "<:ffxivRole_dps:926749125737844737>",
    "<:ffxivRole_healer:926749125733679135>",
    "<:ffxivRole_tank:926749126153084988>",
]

VOICE_REACTIONS = [":mute:", ":loud_sound:"]

RAID_VOTE_RESULT = """**ACTIVITY VOTE: {}** @everyone
The Twilight Travelers ACTIVITY this week will be {}
 This is the official sign-up form, so please react with the specified emoji below this post.

 <:ffxivRole_dps:926749125737844737> I will join as a DPS.
 <:ffxivRole_healer:926749125733679135> I will join as a Healer.
 <:ffxivRole_tank:926749126153084988> I will join as a Tank. 
 __(multiple voting is allowed)__ 
 
 If you want to join the voice chat for this event, please vote with :loud_sound:; If not, please react with :mute:.

__**When:**__  The farm will commence on {} at 18:00ST - 20:00ST (servertime).
  <:hand:973233132369215568> At {}
__**Info:**__  Be sure to unlock all the required duties.
__**Raid Leader:**__ <@{}>"""

SIGNUP_RESULT = """**Signup results**

{}
"""

event_types = {
    "raids": raid_activity_poll,
    # What other types of events would we want to schedule?
}
