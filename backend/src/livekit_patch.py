"""
Monkey-patch for livekit-rtc 1.1.2 local_track_subscribed KeyError.

livekit-rtc 1.1.2 has a race condition where a local_track_subscribed
event can arrive after the track has been unpublished, causing a
KeyError on track_publications[sid]. This patch uses .get() with a
guard check instead of direct dict access.

Import this module before any LiveKit agents code runs.
"""

import logging

from livekit.rtc import room as _room_module

_original_on_room_event = _room_module.Room._on_room_event


def _patched_on_room_event(self, event):
    which = event.WhichOneof("message")
    if which == "local_track_subscribed":
        sid = event.local_track_subscribed.track_sid
        lpublication = self.local_participant.track_publications.get(sid)
        if lpublication is None:
            logging.getLogger("livekit.rtc").debug(
                "local_track_subscribed for untracked SID %s (race)", sid
            )
            return
        if not lpublication._first_subscription.done():
            lpublication._first_subscription.set_result(None)
        self.emit("local_track_subscribed", lpublication.track)
        return
    if which == "local_track_unpublished":
        sid = event.local_track_unpublished.publication_sid
        lpublication = self.local_participant.track_publications.get(sid)
        if lpublication is None:
            logging.getLogger("livekit.rtc").debug(
                "local_track_unpublished for untracked SID %s (race)", sid
            )
            return
        self.emit("local_track_unpublished", lpublication)
        return
    return _original_on_room_event(self, event)


_room_module.Room._on_room_event = _patched_on_room_event
