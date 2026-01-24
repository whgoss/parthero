from django.contrib import admin
from core.models.music import (
    Piece,
    Part,
    PartAsset,
    PartInstrument,
    MusicianInstrument,
    Instrument,
)
from core.models.organizations import Organization, Musician
from core.models.users import User, UserOrganization

admin.site.register(Instrument)
admin.site.register(Musician)
admin.site.register(MusicianInstrument)
admin.site.register(Organization)
admin.site.register(Piece)
admin.site.register(Part)
admin.site.register(PartAsset)
admin.site.register(PartInstrument)
admin.site.register(User)
admin.site.register(UserOrganization)
