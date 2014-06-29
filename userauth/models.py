from django.db import models
from django.contrib.auth.models import User, Group

# -----------------------------------------------------------------------------
# GROUP INVITATIONS MODEL
# -----------------------------------------------------------------------------
class GroupInvitation(models.Model):
    group = models.ForeignKey(to=Group, verbose_name=u'Gruppe', related_name=u'group_invites')
    inviter = models.ForeignKey(to=User, verbose_name=u'Einlader', related_name=u'group_inviter')
    invitee = models.ForeignKey(to=User, verbose_name=u'Eingeladener', related_name=u'group_invitees')

    class Meta:
        verbose_name = u'Einladung'
        verbose_name_plural = u'Einladungen'

    def __unicode__(self):
        return '[' + self.group.name + '] ' + self.inviter.username + ' - ' + self.invitee.username

    @classmethod
    def create(cls, group, inviter, invitee):
        invite = cls(group=group, inviter=inviter, invitee=invitee)
        # do something with the book
        return invite
