"""
Collab — group travel with individual payments.
Users link via username, share an itinerary, pay separately.
Real-time chat via Django Channels WebSocket.
"""
import uuid
from django.db import models


class CollabGroup(models.Model):
    STATUS_CHOICES = [
        ('forming',   'Forming'),
        ('confirmed', 'Confirmed'),
        ('travelling','Travelling'),
        ('completed', 'Completed'),
        ('disbanded', 'Disbanded'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    name            = models.CharField(max_length=255, blank=True, default='')
    # Creator
    created_by      = models.CharField(max_length=100)  # user_id loose ref
    created_by_name = models.CharField(max_length=255, blank=True, default='')

    # Shared itinerary context
    region_id       = models.CharField(max_length=100, blank=True, default='')
    trip_start_date = models.DateField(null=True, blank=True)
    trip_end_date   = models.DateField(null=True, blank=True)
    travel_style    = models.FloatField(default=0.5)
    season          = models.CharField(max_length=20, default='summer')

    # Discovery
    is_public       = models.BooleanField(default=False)

    # Brief note shown in search results ("Looking for 2 more trekkers")
    public_note     = models.CharField(max_length=255, blank=True, default='')

    # Max members the creator is willing to accept via discovery
    open_spots      = models.PositiveIntegerField(default=2)

    # Shared itinerary snapshot (agreed upon by all members)
    itinerary_snapshot = models.JSONField(default=dict)

    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default='forming')
    max_members     = models.PositiveIntegerField(default=10)
    notes           = models.TextField(blank=True, default='')
    is_public       = models.BooleanField(default=False)
    public_note     = models.CharField(max_length=255, blank=True, default='')
    open_spots      = models.PositiveIntegerField(default=2)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'collab_groups'
        ordering  = ['-created_at']

    def __str__(self):
        return f'Collab {self.id} [{self.status}] by {self.created_by_name}'

    @property
    def member_count(self):
        return self.members.filter(status='accepted').count()

    @property
    def chat_room_name(self):
        return f'collab_{str(self.id).replace("-", "_")}'


class CollabMember(models.Model):
    STATUS_CHOICES = [
        ('invited',  'Invited'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('removed',  'Removed'),
    ]
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    group           = models.ForeignKey(CollabGroup, on_delete=models.CASCADE,
                                        related_name='members')
    user_id         = models.CharField(max_length=100)
    username        = models.CharField(max_length=150)
    display_name    = models.CharField(max_length=255, blank=True, default='')
    role            = models.CharField(max_length=10, choices=ROLE_CHOICES,
                                       default='member')
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                       default='invited')
    # Individual booking for this member
    booking_id      = models.CharField(max_length=100, blank=True, default='')
    pickup_region   = models.CharField(max_length=100, blank=True, default='')
    pickup_city     = models.CharField(max_length=100, blank=True, default='')
    invited_at      = models.DateTimeField(auto_now_add=True)
    responded_at    = models.DateTimeField(null=True, blank=True)

    # Where this member is joining from (for transit/vehicle planning)
    pickup_region   = models.CharField(max_length=100, blank=True, default='')
    pickup_city     = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        app_label    = 'engine_b2c'
        db_table     = 'collab_members'
        unique_together = ('group', 'user_id')

    def __str__(self):
        return f'{self.username} in {self.group_id} [{self.status}]'


class CollabMessage(models.Model):
    """
    Persisted chat messages for a collab group.
    Real-time delivery via Django Channels.
    DB stores history for members who join late or reconnect.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text',    'Text'),
        ('system',  'System'),   # member joined/left, itinerary updated
        ('itinerary','Itinerary Update'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                   editable=False)
    group       = models.ForeignKey(CollabGroup, on_delete=models.CASCADE,
                                    related_name='messages')
    sender_id   = models.CharField(max_length=100)
    sender_name = models.CharField(max_length=255)
    message_type= models.CharField(max_length=15, choices=MESSAGE_TYPE_CHOICES,
                                   default='text')
    content     = models.TextField()
    metadata    = models.JSONField(default=dict)  # for itinerary updates
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'collab_messages'
        ordering  = ['created_at']

    def __str__(self):
        return f'{self.sender_name}: {self.content[:50]}'

    def to_dict(self):
        return {
            'id':           str(self.id),
            'sender_id':    self.sender_id,
            'sender_name':  self.sender_name,
            'message_type': self.message_type,
            'content':      self.content,
            'metadata':     self.metadata,
            'created_at':   self.created_at.isoformat(),
        }


