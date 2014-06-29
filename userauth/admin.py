from django.contrib import admin
from .models import GroupInvitation

class GroupInvitationAdmin(admin.ModelAdmin):
    def inviter(self):
        html = '<a href="/admin/auth/user/'+str(self.inviter.id)+'/">'+str(self.inviter)+'</a>'
        return html
    inviter.allow_tags = True

    def invitee(self):
        html = '<a href="/admin/auth/user/'+str(self.invitee.id)+'/">'+str(self.invitee)+'</a>'
        return html
    invitee.allow_tags = True

    list_display = ('group', inviter, invitee)
    search_fields = ('group', 'inviter__username', 'invitee__username')
    list_filter = ['group', 'inviter', 'invitee']


admin.site.register(GroupInvitation, GroupInvitationAdmin)
