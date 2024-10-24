import enum
from typing import Optional

from pydantic import BaseModel, Field


class PlexWebhookEventType(enum.Enum):
    MEDIA_ADDED = "library.new"
    ON_DECK = "library.on.deck"
    PLAY = "media.play"
    PAUSE = "media.pause"
    STOP = "media.stop"
    RESUME = "media.resume"
    SCROBBLE = "media.scrobble"
    RATE = "media.rate"
    DATABASE_BACKUP = "admin.database.backup"
    DATABASE_CORRUPTED = "admin.database.corrupted"
    NEW_ADMIN_DEVICE = "device.new"
    SHARED_PLAYBACK_STARTED = "playback.started"


class PlexWebhookMetadataType(enum.Enum):
    MOVIE = "movie"


class Account(BaseModel):
    id: Optional[int] = None
    thumb: Optional[str] = None
    title: Optional[str] = None


class Server(BaseModel):
    title: Optional[str] = None
    uuid: Optional[str] = None


class Player(BaseModel):
    local: bool
    publicAddress: Optional[str] = None
    title: Optional[str] = None
    uuid: Optional[str] = None


class Metadata(BaseModel):
    librarySectionType: Optional[str] = None
    ratingKey: Optional[str] = None
    key: Optional[str] = None
    parentRatingKey: Optional[str] = None
    grandparentRatingKey: Optional[str] = None
    guid: Optional[str] = None
    librarySectionID: int
    type: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    grandparentKey: Optional[str] = None
    parentKey: Optional[str] = None
    grandparentTitle: Optional[str] = None
    parentTitle: Optional[str] = None
    summary: Optional[str] = None
    index: Optional[int] = None
    parentIndex: Optional[int] = None
    ratingCount: Optional[int] = None
    thumb: Optional[str] = None
    art: Optional[str] = None
    parentThumb: Optional[str] = None
    grandparentThumb: Optional[str] = None
    grandparentArt: Optional[str] = None
    addedAt: Optional[int] = None
    updatedAt: Optional[int] = None


class PlexWebhook(BaseModel):
    event: Optional[str] = None
    user: bool
    owner: bool
    account: Optional[Account] = Field(None, alias="Account")
    server: Optional[Server] = Field(None, alias="Server")
    player: Optional[Player] = Field(None, alias="Player")
    metadata: Optional[Metadata] = Field(None, alias="Metadata")

    @property
    def event_type(self) -> PlexWebhookEventType:
        return PlexWebhookEventType(self.event)
