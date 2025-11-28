from django.contrib import admin
from core.models.music import Piece, Part, Musician, Section, MusicianSection
from core.models.organizations import Organization
from core.models.users import User, UserOrganization

admin.site.register(Musician)
admin.site.register(MusicianSection)
admin.site.register(Organization)
admin.site.register(Part)
admin.site.register(Piece)
admin.site.register(Section)
admin.site.register(User)
admin.site.register(UserOrganization)
