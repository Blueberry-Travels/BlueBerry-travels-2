import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Region(models.Model):
    ZONE_CHOICES = [
        ('uttar',   'Uttar (North)'),
        ('poorab',  'Poorab (East)'),
        ('pashchim','Pashchim (West)'),
        ('dakshin', 'Dakshin (South)'),
        ('madhyam', 'Madhyam (Central)'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255)
    state       = models.CharField(max_length=100)
    zone        = models.CharField(max_length=20, choices=ZONE_CHOICES)
    description = models.TextField(blank=True, default='')
    image_url   = models.URLField(blank=True, default='')
    lat         = models.FloatField(null=True, blank=True)
    lng         = models.FloatField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    # Links to engine_meta.RegionConfig for bounding box + pipeline config
    region_code = models.CharField(max_length=3, blank=True, default='')

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'regions'
        ordering  = ['zone', 'name']

    def __str__(self):
        return f'{self.name} ({self.state})'

    @property
    def config(self):
        """Returns the linked RegionConfig for bounding box and pipeline params."""
        if not self.region_code:
            return None
        try:
            from engine_meta.models import RegionConfig
            return RegionConfig.objects.get(code=self.region_code)
        except Exception:
            return None


class Activity(models.Model):

    # ── Node type ────────────────────────────────────────────────────────
    NODE_TYPE_CHOICES = [
        ('activity', 'Activity'),        # standard bookable activity
        ('filler',   'Filler'),          # admin-registered gap filler
        ('transit',  'Transit'),         # auto-inserted by pipeline
    ]

    # ── Category — must match the 14 canonical categories in the RF ──────
    CATEGORY_CHOICES = [
        ('adventure_sports', 'Adventure Sports'),
        ('camping',          'Camping'),
        ('cultural',         'Cultural'),
        ('food',             'Food'),
        ('heritage',         'Heritage'),
        ('hobbyist',         'Hobbyist'),
        ('meditation',       'Meditation'),
        ('photography',      'Photography'),
        ('rafting',          'Rafting'),
        ('rest',             'Rest'),
        ('transit',          'Transit'),
        ('trekking',         'Trekking'),
        ('water_sports',     'Water Sports'),
        ('wildlife',         'Wildlife'),
    ]

    TONE_CHOICES = [
        ('yin',  'Yin / Chill'),
        ('both', 'Both'),
        ('yang', 'Yang / Adventure'),
    ]

    RISK_TIER_CHOICES = [
        ('casual',   'Casual'),      # risk_level 0.00–0.20
        ('moderate', 'Moderate'),    # risk_level 0.20–0.40
        ('high',     'High'),        # risk_level 0.40–0.65
        ('extreme',  'Extreme'),     # risk_level 0.65–1.00  → triggers NOC
    ]

    # ── Identity ─────────────────────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    region      = models.ForeignKey(
                      Region, on_delete=models.PROTECT, related_name='activities')
    node_type   = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES,
                                   default='activity')
    name        = models.CharField(max_length=255)
    short_desc  = models.CharField(max_length=500, blank=True, default='')
    description = models.TextField(blank=True, default='')

    # ── Space — vector dims [43][44][34] ─────────────────────────────────
    lat          = models.FloatField(null=True, blank=True)   # GPS latitude
    lng          = models.FloatField(null=True, blank=True)   # GPS longitude
    altitude_m   = models.IntegerField(default=0)             # metres ASL → dim [34]

    # ── Category and tone — vector dims [0:13][27] ───────────────────────
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    tone        = models.CharField(max_length=10, choices=TONE_CHOICES, default='both')

    # ── Effort and duration — vector dims [28][29] ───────────────────────
    effort_score      = models.FloatField(default=0.50)   # 0.0–1.0
    duration_hrs      = models.FloatField(default=1.0)

    # ── Reward scores (admin set, used by RF as training targets) ────────
    reward_score      = models.FloatField(default=0.75)   # base predicted reward
    reward_score_base = models.FloatField(default=0.75)   # floor (off-season)
    reward_score_max  = models.FloatField(default=0.75)   # ceiling (peak season)

    # ── Recovery and significance ─────────────────────────────────────────
    recovery_coeff    = models.FloatField(default=0.0)    # how much recovery needed after
    significance_score= models.FloatField(default=0.50)  # once_in_lifetime proxy

    # ── Risk — vector dim [33] + NOC trigger ─────────────────────────────
    risk_tier         = models.CharField(max_length=20, choices=RISK_TIER_CHOICES,
                                         default='casual')
    noc_required      = models.BooleanField(default=False)
    min_age             = models.PositiveIntegerField(default=0)
    fitness_note      = models.CharField(max_length=500, blank=True, default='')

    # ── Weather — vector dims [31][32] ───────────────────────────────────
    # Seasonal availability as JSON: {"summer": {"score": 0.85, "bias": 0.35}, ...}
    seasonal_availability = models.JSONField(default=dict)

    # ── Time — vector dims [30][37] ──────────────────────────────────────
    is_fixed_route          = models.BooleanField(default=False)
    time_of_day_sensitivity = models.BooleanField(default=False)
    is_shiftable_anytime    = models.BooleanField(default=False)

    # Optimal time window — e.g. {"start": "18:45", "end": "19:30"}
    # time_window_width = (end - start) / 1440.0 for vector dim [37]
    preferred_time_windows  = models.JSONField(default=list)

    # Buffer and allowance
    buffer_before_mins  = models.IntegerField(default=15)
    buffer_after_mins   = models.IntegerField(default=15)
    allowance_time_mins = models.IntegerField(default=30)

    # Time exceptions — {"closed": ["Tuesday"], "lunar_close": ["Ekadashi"]}
    has_time_exception  = models.BooleanField(default=False)
    exception_start_time= models.TimeField(null=True, blank=True)
    time_exception_detail = models.JSONField(default=dict)

    # ── Calendar — L1 hard filter inputs ─────────────────────────────────
    # operating_months: [1..12] — months when available
    operating_months    = ArrayField(models.IntegerField(), default=list, blank=True)

    # functional_days: [1..7] — days of week when open (1=Mon, 7=Sun)
    # e.g. [1,2,4,5,6] = closed Wed and Sun
    functional_days     = ArrayField(models.IntegerField(), default=list, blank=True)

    # operating_hours: {"Mon": {"open": "09:00", "close": "17:00"}, ...}
    operating_hours     = models.JSONField(default=dict)

    # holidays: specific dates or named holidays when closed
    holidays            = models.JSONField(default=list)

    # ── Tools — vector dim [35][36] ──────────────────────────────────────
    # tools: ["trekking poles", "waterproof jacket"]
    tools               = ArrayField(models.CharField(max_length=100),
                                     default=list, blank=True)
    gear_class          = models.IntegerField(default=0)   # 0/1/2/3
    permit_required     = models.BooleanField(default=False)
    permit_type         = models.CharField(max_length=100, blank=True, default='')
    guide_mandatory     = models.BooleanField(default=False)

    # ── Dietary support ───────────────────────────────────────────────────
    dietary_support     = ArrayField(models.CharField(max_length=50),
                                     default=list, blank=True)

    # ── Pricing ───────────────────────────────────────────────────────────
    price_from          = models.DecimalField(max_digits=10, decimal_places=2,
                                              default=0)

    # ── Pipeline flags ────────────────────────────────────────────────────
    is_filler           = models.BooleanField(default=False)
    content_approved    = models.BooleanField(default=False)
    is_active           = models.BooleanField(default=True)

    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'activities'
        ordering  = ['region', 'category', 'name']

    def __str__(self):
        return f'{self.name} [{self.category}] — {self.region.name}'

    # ── Derived properties used by feature_extractor ─────────────────────

    def get_seasonal(self, season: str) -> dict:
        """Returns {"score": float, "bias": float} for the given season."""
        default = {'score': 0.75, 'bias': 0.20}
        return self.seasonal_availability.get(season, default)

    def weather_score(self, season: str) -> float:
        return self.get_seasonal(season)['score']

    def weather_bias(self, season: str) -> float:
        return self.get_seasonal(season)['bias']

    def risk_level(self) -> float:
        """Maps risk_tier to float 0.0–1.0 for vector dim [33]."""
        return {
            'casual':   0.10,
            'moderate': 0.35,
            'high':     0.55,
            'extreme':  0.80,
        }.get(self.risk_tier, 0.10)

    def gear_class_norm(self) -> float:
        """Normalises gear_class 0–3 to 0.0–1.0 for vector dim [35]."""
        return self.gear_class / 3.0

    def altitude_norm(self) -> float:
        """Normalises altitude_m to 0.0–1.0 for vector dim [34]."""
        return min(self.altitude_m / 6000.0, 1.0)

    def time_window_width(self) -> float:
        """
        Computes time window width as fraction of day for vector dim [37].
        Uses first entry in preferred_time_windows if present.
        Fixed-time activities with a narrow window score close to 0.03 (45 min).
        Fully flexible = 1.0.
        """
        if not self.preferred_time_windows:
            return 1.0
        try:
            window = self.preferred_time_windows[0]
            start  = window.get('start', '00:00')
            end    = window.get('end',   '23:59')
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            width_min = (eh * 60 + em) - (sh * 60 + sm)
            return max(0.0, min(width_min / 1440.0, 1.0))
        except Exception:
            return 1.0

    def is_available_on(self, date) -> bool:
        """
        L1 hard filter helper.
        Returns False if date falls outside operating_months,
        functional_days, or is in holidays.
        """
        if self.operating_months and date.month not in self.operating_months:
            return False
        if self.functional_days and date.isoweekday() not in self.functional_days:
            return False
        date_str = date.strftime('%Y-%m-%d')
        if date_str in (self.holidays or []):
            return False
        return True

    def noc_auto_flag(self) -> bool:
        """Returns True if this activity should trigger the NOC checkbox."""
        return self.risk_tier in ('high', 'extreme') or self.altitude_m >= 4000


# ── Phase 5 — Booking Layer ───────────────────────────────────────────────────

class Booking(models.Model):
    """
    Master booking record. One Razorpay order per booking.
    A booking contains one or more BookingLineItems (one per activity/service).
    """
    STATUS_CHOICES = [
        ('draft',                'Draft'),
        ('pending_payment',      'Pending Payment'),
        ('pending_confirmation', 'Pending Confirmation'),
        ('confirmed',            'Confirmed'),
        ('in_progress',          'In Progress'),
        ('completed',            'Completed'),
        ('cancelled',            'Cancelled'),
        ('refunded',             'Refunded'),
        ('partially_refunded',   'Partially Refunded'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                            editable=False)
    # User — loose ref to engine_meta.User (no FK across engines)
    user_id              = models.CharField(max_length=100)
    user_email           = models.EmailField()
    user_name            = models.CharField(max_length=255)
    user_phone           = models.CharField(max_length=20, blank=True, default='')

    # Guest booking (not logged in)
    guest_token          = models.CharField(max_length=255, blank=True, default='')

    # Trip context
    region               = models.ForeignKey(Region, on_delete=models.PROTECT,
                                             related_name='bookings')
    travel_style         = models.FloatField(default=0.5)
    trip_start_date      = models.DateField()
    trip_end_date        = models.DateField()
    season               = models.CharField(max_length=20, default='summer')
    total_guests         = models.PositiveIntegerField(default=1)

    # Payment
    razorpay_order_id    = models.CharField(max_length=100, blank=True, default='')
    razorpay_payment_id  = models.CharField(max_length=100, blank=True, default='')
    razorpay_signature   = models.CharField(max_length=255, blank=True, default='')
    currency             = models.CharField(max_length=3, default='INR')
    total_amount         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_amount      = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status               = models.CharField(max_length=30, choices=STATUS_CHOICES,
                                            default='draft')
    # Itinerary snapshot — the full pipeline output stored at booking time
    itinerary_snapshot   = models.JSONField(default=dict)

    # Collab
    is_collab            = models.BooleanField(default=False)
    collab_group_id      = models.CharField(max_length=100, blank=True, default='')

    notes                = models.TextField(blank=True, default='')
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'bookings'
        ordering  = ['-created_at']

    def __str__(self):
        return f'Booking {self.id} — {self.user_email} [{self.status}]'

    @property
    def is_fully_confirmed(self):
        return all(
            li.status == 'confirmed'
            for li in self.line_items.filter(requires_confirmation=True)
        )


class BookingLineItem(models.Model):
    """
    One service within a booking.
    source_type determines which external API or internal partner handles it.
    """
    STATUS_CHOICES = [
        ('pending',              'Pending'),
        ('pending_confirmation', 'Pending Partner Confirmation'),
        ('confirmed',            'Confirmed'),
        ('rejected',             'Rejected'),
        ('cancelled',            'Cancelled'),
        ('refund_initiated',     'Refund Initiated'),
        ('refunded',             'Refunded'),
        ('completed',            'Completed'),
    ]
    SOURCE_CHOICES = [
        ('internal',     'Internal Partner'),
        ('redbus',       'RedBus'),
        ('abhibus',      'AbhiBus'),
        ('irctc',        'IRCTC'),
        ('bookingcom',   'Booking.com'),
        ('bms',          'BookMyShow API'),
        ('bms_redirect', 'BookMyShow Deep Link'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                            editable=False)
    booking              = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                             related_name='line_items')
    source_type          = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    # Activity reference (loose — activity may be external)
    activity_id          = models.CharField(max_length=100, blank=True, default='')
    activity_name        = models.CharField(max_length=255)
    activity_category    = models.CharField(max_length=30, blank=True, default='')
    scheduled_date       = models.DateField(null=True, blank=True)
    scheduled_time       = models.TimeField(null=True, blank=True)

    # Internal partner (source_type='internal')
    # Loose ref to engine_b2b.PartnerProfile
    partner_id           = models.CharField(max_length=100, blank=True, default='')
    partner_name         = models.CharField(max_length=255, blank=True, default='')

    # Confirmation
    requires_confirmation= models.BooleanField(default=True)
    confirmation_deadline= models.DateTimeField(null=True, blank=True)
    confirmed_at         = models.DateTimeField(null=True, blank=True)
    rejected_at          = models.DateTimeField(null=True, blank=True)
    rejection_reason     = models.TextField(blank=True, default='')

    # Pricing
    unit_price           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity             = models.PositiveIntegerField(default=1)
    subtotal             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate      = models.FloatField(default=0.10)
    commission_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    partner_payout       = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Refund
    refund_amount        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razorpay_refund_id   = models.CharField(max_length=100, blank=True, default='')
    refunded_at          = models.DateTimeField(null=True, blank=True)

    status               = models.CharField(max_length=30, choices=STATUS_CHOICES,
                                            default='pending')

    # NOC
    noc_accepted         = models.BooleanField(default=False)
    noc_accepted_at      = models.DateTimeField(null=True, blank=True)

    # Filler flag — user can remove before finalising
    is_filler            = models.BooleanField(default=False)
    user_confirmed_filler= models.BooleanField(default=False)

    notes                = models.TextField(blank=True, default='')
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'booking_line_items'
        ordering  = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return (f'{self.activity_name} [{self.source_type}] '
                f'— {self.status}')

    def save(self, *args, **kwargs):
        self.subtotal        = self.unit_price * self.quantity
        self.commission_amount = self.subtotal * self.commission_rate
        self.partner_payout  = self.subtotal - self.commission_amount
        super().save(*args, **kwargs)


class ExternalTicket(models.Model):
    """
    Stores the raw API response and parsed ticket data
    for all external bookings: bus, train, hotel, event.
    """
    PROVIDER_CHOICES = [
        ('redbus',     'RedBus'),
        ('abhibus',    'AbhiBus'),
        ('irctc',      'IRCTC'),
        ('bookingcom', 'Booking.com'),
        ('bms',        'BookMyShow'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    line_item       = models.OneToOneField(BookingLineItem, on_delete=models.CASCADE,
                                           related_name='external_ticket')
    provider        = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    pnr             = models.CharField(max_length=100, blank=True, default='')
    ticket_url      = models.URLField(blank=True, default='')
    raw_response    = models.JSONField(default=dict)
    booked_at       = models.DateTimeField(auto_now_add=True)
    expires_at      = models.DateTimeField(null=True, blank=True)
    is_cancelled    = models.BooleanField(default=False)
    cancelled_at    = models.DateTimeField(null=True, blank=True)
    cancellation_ref= models.CharField(max_length=100, blank=True, default='')

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'external_tickets'

    def __str__(self):
        return f'{self.provider} PNR:{self.pnr} — {self.line_item}'


class BusPassenger(models.Model):
    """Passenger details for bus and train line items."""
    GENDER_CHOICES = [('M','Male'),('F','Female'),('O','Other')]
    ID_TYPE_CHOICES = [
        ('aadhaar',  'Aadhaar'),
        ('pan',      'PAN'),
        ('passport', 'Passport'),
        ('dl',       'Driving License'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_item   = models.ForeignKey(BookingLineItem, on_delete=models.CASCADE,
                                    related_name='passengers')
    name        = models.CharField(max_length=255)
    age         = models.PositiveIntegerField()
    gender      = models.CharField(max_length=1, choices=GENDER_CHOICES)
    seat_number = models.CharField(max_length=20, blank=True, default='')
    # ID — mandatory for IRCTC
    id_type     = models.CharField(max_length=20, choices=ID_TYPE_CHOICES,
                                   blank=True, default='')
    id_number   = models.CharField(max_length=100, blank=True, default='')
    # Store hash only — never raw Aadhaar
    id_hash     = models.CharField(max_length=64, blank=True, default='')
    is_primary  = models.BooleanField(default=False)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'bus_passengers'

    def __str__(self):
        return f'{self.name} (seat {self.seat_number})'


class StayLineItemDetail(models.Model):
    """Extra detail for stay bookings — platform or Booking.com."""
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    line_item       = models.OneToOneField(BookingLineItem, on_delete=models.CASCADE,
                                           related_name='stay_detail')
    hotel_name      = models.CharField(max_length=255, blank=True, default='')
    hotel_id        = models.CharField(max_length=100, blank=True, default='')
    room_type       = models.CharField(max_length=100, blank=True, default='')
    room_id         = models.CharField(max_length=100, blank=True, default='')
    check_in        = models.DateField()
    check_out       = models.DateField()
    nights          = models.PositiveIntegerField(default=1)
    rooms_booked    = models.PositiveIntegerField(default=1)
    adults          = models.PositiveIntegerField(default=2)
    meal_plan       = models.CharField(max_length=50, blank=True, default='')
    # Booking.com specific
    powered_by_label= models.CharField(max_length=50, blank=True, default='')
    booking_url     = models.URLField(blank=True, default='')
    instant_confirm = models.BooleanField(default=False)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'stay_line_item_details'

    def __str__(self):
        return (f'{self.hotel_name} {self.check_in}→{self.check_out} '
                f'({self.nights}n)')


class EventLineItemDetail(models.Model):
    """
    Extra detail for event bookings.
    source='bms_redirect' — only deep_link stored, no ticket data.
    source='bms'          — full ticket data from BMS API.
    """
    SOURCE_CHOICES = [
        ('bms',          'BookMyShow API'),
        ('bms_redirect', 'BookMyShow Deep Link'),
        ('platform',     'Platform Event'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    line_item       = models.OneToOneField(BookingLineItem, on_delete=models.CASCADE,
                                           related_name='event_detail')
    source          = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    event_name      = models.CharField(max_length=255)
    event_id        = models.CharField(max_length=100, blank=True, default='')
    venue_name      = models.CharField(max_length=255, blank=True, default='')
    venue_address   = models.TextField(blank=True, default='')
    event_date      = models.DateField()
    event_time      = models.TimeField(null=True, blank=True)
    # BMS redirect
    deep_link       = models.URLField(blank=True, default='')
    # BMS API
    seat_category   = models.CharField(max_length=100, blank=True, default='')
    seat_numbers    = models.JSONField(default=list)
    bms_booking_id  = models.CharField(max_length=100, blank=True, default='')
    powered_by_label= models.CharField(max_length=50, blank=True, default='')

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'event_line_item_details'

    def __str__(self):
        return f'{self.event_name} @ {self.venue_name} [{self.source}]'


class ExternalAPICredential(models.Model):
    """
    Per-provider API credentials for external transport/ticket APIs.
    Superseded by ThirdPartyAPIConfig in engine_meta —
    this table is kept for historical audit of credential rotations.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                   editable=False)
    provider    = models.CharField(max_length=30)
    label       = models.CharField(max_length=100)
    rotated_at  = models.DateTimeField(auto_now_add=True)
    rotated_by  = models.CharField(max_length=255, blank=True, default='')
    note        = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'external_api_credentials'

    def __str__(self):
        return f'{self.provider} — rotated {self.rotated_at:%Y-%m-%d}'

# ── Collab imports ────────────────────────────────────────────────────────────
# Collab models live in engine_b2c/collab_models.py
# Imported here so Django discovers them for migrations.
from engine_b2c.collab_models import CollabGroup, CollabMember, CollabMessage


# ── Trip Buffer ───────────────────────────────────────────────────────────────

class TripBuffer(models.Model):
    """
    Per-booking buffer account.
    Funded by customer via Razorpay at booking creation.
    Used for Booking.com hotel advances only.
    Blueberry holds the funds and forwards manually.
    """
    STATUS_CHOICES = [
        ('unfunded',  'Unfunded'),
        ('funded',    'Funded'),
        ('partially_used', 'Partially Used'),
        ('exhausted', 'Exhausted'),
        ('refunded',  'Refunded'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                            editable=False)
    booking              = models.OneToOneField(Booking, on_delete=models.CASCADE,
                                                related_name='trip_buffer')
    # Amount customer loaded into buffer
    loaded_amount        = models.DecimalField(max_digits=10, decimal_places=2,
                                               default=0)
    # Amount spent on advances so far
    used_amount          = models.DecimalField(max_digits=10, decimal_places=2,
                                               default=0)
    # Razorpay refs for the buffer top-up payment
    razorpay_order_id    = models.CharField(max_length=100, blank=True, default='')
    razorpay_payment_id  = models.CharField(max_length=100, blank=True, default='')
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                            default='unfunded')
    funded_at            = models.DateTimeField(null=True, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'trip_buffers'

    def __str__(self):
        return (f'Buffer for {self.booking_id} — '
                f'loaded={self.loaded_amount} used={self.used_amount}')

    @property
    def available(self):
        return self.loaded_amount - self.used_amount

    def deduct(self, amount):
        """Deduct advance from buffer. Raises if insufficient."""
        if amount > self.available:
            raise ValueError(
                f'Insufficient buffer: available={self.available} '
                f'requested={amount}')
        self.used_amount += amount
        if self.used_amount >= self.loaded_amount:
            self.status = 'exhausted'
        else:
            self.status = 'partially_used'
        self.save(update_fields=['used_amount', 'status', 'updated_at'])


class AdvancePaymentRequest(models.Model):
    """
    Created by coordinator for a Booking.com hotel that demands advance.
    If no coordinator, customer is prompted to contact hotel directly.
    Customer pays via Razorpay link generated by system.
    Blueberry deducts from trip buffer and forwards manually.
    """
    STATUS_CHOICES = [
        ('pending',        'Pending Customer Payment'),
        ('paid',           'Paid by Customer'),
        ('forwarded',      'Forwarded to Hotel'),
        ('confirmed',      'Hotel Confirmed'),
        ('cancelled',      'Cancelled'),
    ]
    SOURCE_CHOICES = [
        ('coordinator',    'Coordinator Created'),
        ('customer_self',  'Customer Self-Service'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                            editable=False)
    booking              = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                             related_name='advance_requests')
    # The Booking.com line item this advance is for
    line_item            = models.ForeignKey(BookingLineItem, on_delete=models.CASCADE,
                                             related_name='advance_requests')
    source               = models.CharField(max_length=20, choices=SOURCE_CHOICES,
                                            default='coordinator')
    # Coordinator who created this (loose ref)
    coordinator_id       = models.CharField(max_length=100, blank=True, default='')
    coordinator_name     = models.CharField(max_length=255, blank=True, default='')

    # Hotel details (from Booking.com line item or coordinator input)
    hotel_name           = models.CharField(max_length=255)
    advance_amount       = models.DecimalField(max_digits=10, decimal_places=2)
    currency             = models.CharField(max_length=3, default='INR')
    reason               = models.TextField(blank=True, default='')

    # Payment
    razorpay_order_id    = models.CharField(max_length=100, blank=True, default='')
    razorpay_payment_id  = models.CharField(max_length=100, blank=True, default='')
    paid_at              = models.DateTimeField(null=True, blank=True)

    # Forwarding to hotel
    forwarded_at         = models.DateTimeField(null=True, blank=True)
    forwarded_by         = models.CharField(max_length=255, blank=True, default='')
    forwarding_note      = models.TextField(blank=True, default='')

    status               = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                            default='pending')

    # Customer message shown on dashboard
    customer_message     = models.TextField(
        default='Please pay the advance to confirm your hotel booking.')
    no_coordinator       = models.BooleanField(default=False)

    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'advance_payment_requests'
        ordering  = ['-created_at']

    def __str__(self):
        return (f'Advance {self.advance_amount} for {self.hotel_name} '
                f'[{self.status}]')


# ── Notifications ─────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        # Booking
        ('booking_confirmed',         'Booking Confirmed'),
        ('booking_rejected',          'Booking Rejected'),
        ('booking_cancelled',         'Booking Cancelled'),
        ('booking_completed',         'Booking Completed'),
        # Partner
        ('partner_confirmed',         'Partner Confirmed Activity'),
        ('partner_rejected',          'Partner Rejected Activity'),
        ('partner_new_booking',       'New Booking (Partner)'),
        # Payment
        ('payment_success',           'Payment Successful'),
        ('refund_initiated',          'Refund Initiated'),
        ('refund_completed',          'Refund Completed'),
        ('advance_requested',         'Advance Payment Requested'),
        ('advance_paid',              'Advance Paid'),
        # Collab
        ('collab_invite',             'Collab Invite Received'),
        ('collab_member_joined',      'Member Joined Your Group'),
        ('collab_member_left',        'Member Left Your Group'),
        ('collab_itinerary_updated',  'Group Itinerary Updated'),
        # System
        ('disruption_alert',          'Travel Disruption Alert'),
        ('force_majeure',             'Force Majeure — Booking Cancelled'),
        ('system',                    'System Message'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    # Recipient — loose ref to engine_meta.User
    user_id         = models.CharField(max_length=100, db_index=True)

    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title           = models.CharField(max_length=255)
    body            = models.TextField()

    # Grouping — links notification to a trip/booking
    booking_id      = models.CharField(max_length=100, blank=True, default='',
                                       db_index=True)
    # Optional deep-link for frontend routing
    action_url      = models.CharField(max_length=500, blank=True, default='')
    # Extra structured data for frontend rendering
    metadata        = models.JSONField(default=dict)

    is_read         = models.BooleanField(default=False, db_index=True)
    read_at         = models.DateTimeField(null=True, blank=True)

    # Delivery channels
    sent_whatsapp   = models.BooleanField(default=False)
    sent_email      = models.BooleanField(default=False)
    sent_push       = models.BooleanField(default=False)

    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'notifications'
        ordering  = ['-created_at']

    def __str__(self):
        return f'[{self.notification_type}] → {self.user_id}: {self.title}'

    def to_dict(self):
        return {
            'id':                str(self.id),
            'type':              self.notification_type,
            'title':             self.title,
            'body':              self.body,
            'booking_id':        self.booking_id,
            'action_url':        self.action_url,
            'metadata':          self.metadata,
            'is_read':           self.is_read,
            'created_at':        self.created_at.isoformat(),
        }

# ── Room Availability ─────────────────────────────────────────────────────────

class RoomAvailability(models.Model):
    """
    Per-date room stock for platform hotels.
    Written by engine_b2b when partner registers rooms.
    Decremented on booking, incremented on cancellation.
    Partner can manually block dates via PartnerClosureDate.

    Used by bookingcom.py should_use_bookingcom() to decide
    whether platform hotels cover the requested dates.
    If available > 0 for any platform room on all requested dates
    → use platform. Otherwise → Booking.com fallback.
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                     editable=False)
    # Loose refs — no FK across engines
    partner_id    = models.CharField(max_length=100, db_index=True)
    room_id       = models.CharField(max_length=100, db_index=True)
    region        = models.ForeignKey(Region, on_delete=models.CASCADE,
                                      related_name='room_availability')
    date          = models.DateField(db_index=True)
    total_rooms   = models.PositiveIntegerField(default=1)
    booked_rooms  = models.PositiveIntegerField(default=0)
    blocked_rooms = models.PositiveIntegerField(default=0)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        app_label    = 'engine_b2c'
        db_table     = 'room_availability'
        unique_together = ('partner_id', 'room_id', 'date')
        ordering     = ['date']

    def __str__(self):
        return (f'Room {self.room_id} on {self.date} — '
                f'avail={self.available}/{self.total_rooms}')

    @property
    def available(self) -> int:
        return max(0, self.total_rooms - self.booked_rooms - self.blocked_rooms)

    def book(self, count: int = 1):
        """Decrement available stock on booking."""
        if count > self.available:
            raise ValueError(
                f'Insufficient rooms: available={self.available} requested={count}')
        self.booked_rooms += count
        self.save(update_fields=['booked_rooms', 'updated_at'])

    def release(self, count: int = 1):
        """Increment available stock on cancellation."""
        self.booked_rooms = max(0, self.booked_rooms - count)
        self.save(update_fields=['booked_rooms', 'updated_at'])

    def block(self, count: int = 1):
        """Partner manually blocks rooms for a date."""
        self.blocked_rooms += count
        self.save(update_fields=['blocked_rooms', 'updated_at'])

    def unblock(self, count: int = 1):
        self.blocked_rooms = max(0, self.blocked_rooms - count)
        self.save(update_fields=['blocked_rooms', 'updated_at'])

    @classmethod
    def is_available_for_region(
        cls,
        region_id: str,
        checkin:   str,
        checkout:  str,
    ) -> bool:
        """
        Returns True if at least one platform room is available
        across ALL dates in the checkin→checkout range.
        Called by bookingcom.py should_use_bookingcom().
        """
        from datetime import date, timedelta
        try:
            y1, m1, d1 = map(int, checkin.split('-'))
            y2, m2, d2 = map(int, checkout.split('-'))
            start = date(y1, m1, d1)
            end   = date(y2, m2, d2)
        except Exception:
            return False

        dates = []
        current = start
        while current < end:
            dates.append(current)
            current += timedelta(days=1)

        if not dates:
            return False

        # For each date, check if any platform room has availability
        for d in dates:
            has_avail = cls.objects.filter(
                region_id=region_id,
                date=d,
                total_rooms__gt=0,
            ).extra(
                where=['total_rooms - booked_rooms - blocked_rooms > 0']
            ).exists()
            if not has_avail:
                return False
        return True


# ── Promo Vouchers ────────────────────────────────────────────────────────────

class PromoVoucher(models.Model):
    """
    Platform-wide promotional vouchers.
    Applied at checkout before Razorpay order creation.
    Applied to entire booking total, not per activity.
    Admin creates, system auto-generates code as prefix + random suffix.
    Reset cycle is IST (Asia/Kolkata) midnight.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage',    'Percentage (%)'),
        ('fixed_amount',  'Fixed Amount (₹)'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                           editable=False)
    # Code — admin sets prefix, system appends 4-char suffix on save
    code_prefix         = models.CharField(max_length=20)
    code                = models.CharField(max_length=30, unique=True,
                                           blank=True, db_index=True)

    description         = models.CharField(max_length=255, blank=True, default='')
    discount_type       = models.CharField(max_length=15,
                                           choices=DISCOUNT_TYPE_CHOICES,
                                           default='percentage')
    discount_value      = models.DecimalField(max_digits=8, decimal_places=2)
    # Cap for percentage discounts (0 = no cap)
    max_discount_amount = models.DecimalField(max_digits=8, decimal_places=2,
                                              default=0)
    min_booking_amount  = models.DecimalField(max_digits=8, decimal_places=2,
                                              default=0)

    # Validity window
    valid_from          = models.DateTimeField()
    valid_until         = models.DateTimeField()

    # Usage limits
    usage_limit_per_day = models.PositiveIntegerField(default=0)  # 0 = unlimited
    total_usage_limit   = models.PositiveIntegerField(default=0)  # 0 = unlimited
    total_used          = models.PositiveIntegerField(default=0)
    used_today          = models.PositiveIntegerField(default=0)
    # Date of last IST reset (YYYY-MM-DD string)
    last_reset_date     = models.CharField(max_length=10, blank=True, default='')

    # Region restriction (empty = all regions)
    restricted_regions  = models.JSONField(default=list)

    is_active           = models.BooleanField(default=True)
    created_by          = models.CharField(max_length=100, blank=True, default='')
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'promo_vouchers'
        ordering  = ['-created_at']

    def __str__(self):
        return f'{self.code} — {self.discount_type} {self.discount_value}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self) -> str:
        import random
        import string
        chars  = string.ascii_uppercase + string.digits
        suffix = ''.join(random.choices(chars, k=4))
        prefix = self.code_prefix.upper().strip().replace(' ', '')
        return f'{prefix}-{suffix}'

    def _ist_today(self) -> str:
        """Returns today's date string in IST."""
        from django.utils import timezone
        import zoneinfo
        ist  = zoneinfo.ZoneInfo('Asia/Kolkata')
        now  = timezone.now().astimezone(ist)
        return now.strftime('%Y-%m-%d')

    def _reset_daily_if_needed(self):
        """Resets used_today counter at IST midnight."""
        today = self._ist_today()
        if self.last_reset_date != today:
            self.used_today      = 0
            self.last_reset_date = today
            self.save(update_fields=['used_today', 'last_reset_date', 'updated_at'])

    def validate(self, booking_total: float,
                 region_id: str = '') -> tuple:
        """
        Validates the voucher for a given booking.
        Returns (is_valid: bool, error_message: str, discount_amount: float)
        """
        from django.utils import timezone

        self._reset_daily_if_needed()

        if not self.is_active:
            return False, 'Voucher is not active.', 0.0

        now = timezone.now()
        if now < self.valid_from:
            return False, 'Voucher is not yet valid.', 0.0
        if now > self.valid_until:
            return False, 'Voucher has expired.', 0.0

        if self.min_booking_amount and booking_total < float(self.min_booking_amount):
            return False, (
                f'Minimum booking amount of ₹{self.min_booking_amount:.0f} required.'), 0.0

        if self.total_usage_limit and self.total_used >= self.total_usage_limit:
            return False, 'Voucher usage limit reached.', 0.0

        if self.usage_limit_per_day and self.used_today >= self.usage_limit_per_day:
            return False, 'Daily usage limit reached. Try again tomorrow.', 0.0

        if self.restricted_regions and region_id:
            if str(region_id) not in [str(r) for r in self.restricted_regions]:
                return False, 'Voucher not valid for this region.', 0.0

        # Calculate discount
        discount = self._calculate_discount(booking_total)
        return True, '', discount

    def _calculate_discount(self, booking_total: float) -> float:
        if self.discount_type == 'percentage':
            discount = booking_total * float(self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, float(self.max_discount_amount))
        else:
            discount = float(self.discount_value)
        return round(min(discount, booking_total), 2)

    def redeem(self):
        """Increments usage counters after successful payment."""
        self._reset_daily_if_needed()
        self.total_used += 1
        self.used_today += 1
        self.save(update_fields=['total_used', 'used_today', 'updated_at'])


class VoucherRedemption(models.Model):
    """Audit trail of every voucher redemption."""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                    editable=False)
    voucher      = models.ForeignKey(PromoVoucher, on_delete=models.PROTECT,
                                     related_name='redemptions')
    booking      = models.ForeignKey(Booking, on_delete=models.PROTECT,
                                     related_name='voucher_redemptions')
    user_id      = models.CharField(max_length=100)
    booking_total_before = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied     = models.DecimalField(max_digits=10, decimal_places=2)
    booking_total_after  = models.DecimalField(max_digits=10, decimal_places=2)
    redeemed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'voucher_redemptions'

    def __str__(self):
        return f'{self.voucher.code} → booking {self.booking_id} (-₹{self.discount_applied})'


# ── AI Coordinator Placeholder ────────────────────────────────────────────────

class CoordinatorSession(models.Model):
    """
    One chat session between a user and the AI coordinator.
    Collected for future training analysis.
    Collection pauses when storage quota hits 90%.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    user_id         = models.CharField(max_length=100, db_index=True)
    booking_id      = models.CharField(max_length=100, blank=True, default='')
    channel         = models.CharField(max_length=10, default='app',
                                       choices=[('app','In-App'),('whatsapp','WhatsApp')])
    started_at      = models.DateTimeField(auto_now_add=True)
    ended_at        = models.DateTimeField(null=True, blank=True)
    was_escalated   = models.BooleanField(default=False)
    escalation_reason = models.CharField(max_length=255, blank=True, default='maintenance')

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'coordinator_sessions'
        ordering  = ['-started_at']

    def __str__(self):
        return f'Session {self.id} [{self.channel}] — {self.user_id}'


class CoordinatorMessage(models.Model):
    """
    Individual messages within a session.
    Stored for future classifier training.
    """
    SENDER_CHOICES = [('user','User'),('bot','Bot'),('coordinator','Coordinator')]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                   editable=False)
    session     = models.ForeignKey(CoordinatorSession, on_delete=models.CASCADE,
                                    related_name='messages')
    sender      = models.CharField(max_length=15, choices=SENDER_CHOICES)
    text        = models.TextField()
    intent_hint = models.CharField(max_length=100, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2c'
        db_table  = 'coordinator_messages'
        ordering  = ['created_at']

    def __str__(self):
        return f'[{self.sender}] {self.text[:60]}'
