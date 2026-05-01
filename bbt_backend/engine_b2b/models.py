import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


# ── Partner Profile ───────────────────────────────────────────────────────────

class PartnerProfile(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('suspended', 'Suspended'),
        ('inactive',  'Inactive'),
    ]
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(
                          'engine_meta.User', on_delete=models.CASCADE,
                          related_name='partner_profile')
    business_name   = models.CharField(max_length=255)
    business_photo   = models.ImageField(
        upload_to='profiles/partners/',
        null=True, blank=True,
        help_text='Partner photo shown in confirmed customer itinerary.'
    )
    commission_rate = models.FloatField(default=0.10)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    failure_count   = models.IntegerField(default=0)
    # Data exchange consent
    data_consent_given   = models.BooleanField(default=False)
    data_consent_version = models.CharField(max_length=20, blank=True, default='')
    data_consented_at    = models.DateTimeField(null=True, blank=True)
    data_consent_ip      = models.GenericIPAddressField(null=True, blank=True)
    # Receipt branding toggle
    show_bbt_branding_on_receipt = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_profiles'

    def __str__(self):
        return f'{self.business_name} ({self.user.email})'


# ── Staff ─────────────────────────────────────────────────────────────────────

class PartnerStaff(models.Model):
    ROLE_CHOICES = [
        ('manager',        'Manager'),
        ('receptionist',   'Receptionist'),
        ('housekeeper',    'Housekeeper'),
        ('driver',         'Driver'),
        ('guide_assistant','Guide Assistant'),
        ('cook',           'Cook'),
        ('security',       'Security'),
        ('mechanic',       'Mechanic'),
        ('other',          'Other'),
    ]
    STATUS_CHOICES = [
        ('active',     'Active'),
        ('on_leave',   'On Leave'),
        ('terminated', 'Terminated'),
    ]
    SALARY_CYCLE_CHOICES = [
        ('monthly',  'Monthly'),
        ('weekly',   'Weekly'),
        ('daily',    'Daily'),
        ('per_trip', 'Per Trip'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner          = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                         related_name='staff')
    name             = models.CharField(max_length=255)
    phone            = models.CharField(max_length=20)
    email            = models.EmailField(blank=True, default='')
    role             = models.CharField(max_length=30, choices=ROLE_CHOICES)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                        default='active')
    employment_start = models.DateField()
    employment_end   = models.DateField(null=True, blank=True)
    salary_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    salary_cycle     = models.CharField(max_length=20, choices=SALARY_CYCLE_CHOICES,
                                        default='monthly')
    # KYC
    is_kyc_verified  = models.BooleanField(default=False)
    kyc_verified_at  = models.DateTimeField(null=True, blank=True)
    aadhaar_hash     = models.CharField(max_length=64, blank=True, default='')
    # License (drivers, guides)
    has_license      = models.BooleanField(default=False)
    license_number   = models.CharField(max_length=100, blank=True, default='')
    license_expiry   = models.DateField(null=True, blank=True)
    license_photo    = models.CharField(max_length=500, blank=True, default='')
    # ID proof
    id_photo         = models.CharField(max_length=500, blank=True, default='')
    face_photo       = models.CharField(max_length=500, blank=True, default='')
    notes            = models.TextField(blank=True, default='')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_staff'

    def __str__(self):
        return f'{self.name} ({self.role}) — {self.partner.business_name}'


class StaffLeave(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff       = models.ForeignKey(PartnerStaff, on_delete=models.CASCADE,
                                    related_name='leaves')
    from_date   = models.DateField()
    to_date     = models.DateField()
    reason      = models.TextField(blank=True, default='')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField(max_length=255, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'staff_leaves'

    def __str__(self):
        return f'{self.staff.name} leave {self.from_date}–{self.to_date}'


class StaffSalaryRecord(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff        = models.ForeignKey(PartnerStaff, on_delete=models.CASCADE,
                                     related_name='salary_records')
    period_label = models.CharField(max_length=50)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on      = models.DateField()
    notes        = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'staff_salary_records'

    def __str__(self):
        return f'{self.staff.name} — {self.period_label} ₹{self.amount}'


# ── Guest Record ──────────────────────────────────────────────────────────────

class PartnerGuestRecord(models.Model):
    SOURCE_CHOICES = [
        ('bbt_booking', 'BBT Booking'),
        ('direct',      'Direct Booking'),
        ('walk_in',     'Walk-in'),
    ]
    STATUS_CHOICES = [
        ('expected',   'Expected'),
        ('checked_in', 'Checked In'),
        ('checked_out','Checked Out'),
        ('in_progress','In Progress'),
        ('completed',  'Completed'),
        ('no_show',    'No Show'),
        ('cancelled',  'Cancelled'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner         = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                        related_name='guest_records')
    source          = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default='expected')
    # BBT booking linkage — loose reference, no FK across engines
    bbt_booking_ref = models.CharField(max_length=100, blank=True, default='')
    bbt_user_id     = models.CharField(max_length=100, blank=True, default='')
    # Guest identity
    guest_name      = models.CharField(max_length=255)
    guest_phone     = models.CharField(max_length=20, blank=True, default='')
    guest_email     = models.EmailField(blank=True, default='')
    nationality     = models.CharField(max_length=100, default='Indian')
    aadhaar_hash    = models.CharField(max_length=64, blank=True, default='')
    # ID proof photos — walk-in only
    face_photo      = models.CharField(max_length=500, blank=True, default='')
    aadhaar_photo   = models.CharField(max_length=500, blank=True, default='')
    id_verified     = models.BooleanField(default=False)
    # Service window
    service_start   = models.DateTimeField(null=True, blank=True)
    service_end     = models.DateTimeField(null=True, blank=True)
    guest_count     = models.PositiveIntegerField(default=1)
    notes           = models.TextField(blank=True, default='')
    # Receipt
    receipt_sent    = models.BooleanField(default=False)
    receipt_sent_at = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_guest_records'
        ordering  = ['-created_at']

    def __str__(self):
        return f'{self.guest_name} @ {self.partner.business_name} [{self.source}]'


# ── Rooms ─────────────────────────────────────────────────────────────────────

class PartnerRoom(models.Model):
    STATUS_CHOICES = [
        ('available',   'Available'),
        ('occupied',    'Occupied'),
        ('cleaning',    'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('blocked',     'Blocked'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner     = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                    related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type   = models.CharField(max_length=100, blank=True, default='')
    floor       = models.CharField(max_length=20, blank=True, default='')
    capacity    = models.PositiveIntegerField(default=2)
    bed_config  = models.CharField(max_length=100, blank=True, default='')
    amenities   = models.JSONField(default=list)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                   default='available')
    notes       = models.TextField(blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label    = 'engine_b2b'
        db_table     = 'partner_rooms'
        unique_together = ('partner', 'room_number')

    def __str__(self):
        return f'Room {self.room_number} — {self.partner.business_name}'


class RoomAssignment(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room             = models.ForeignKey(PartnerRoom, on_delete=models.CASCADE,
                                         related_name='assignments')
    guest_record     = models.ForeignKey(PartnerGuestRecord, on_delete=models.CASCADE,
                                         related_name='room_assignments')
    check_in         = models.DateTimeField()
    check_out        = models.DateTimeField(null=True, blank=True)
    actual_check_in  = models.DateTimeField(null=True, blank=True)
    actual_check_out = models.DateTimeField(null=True, blank=True)
    notes            = models.TextField(blank=True, default='')
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'room_assignments'

    def __str__(self):
        return f'{self.room} ← {self.guest_record.guest_name}'


# ── Tasks ─────────────────────────────────────────────────────────────────────

class PartnerTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('housekeeping',  'Housekeeping'),
        ('maintenance',   'Maintenance'),
        ('laundry',       'Laundry'),
        ('restocking',    'Restocking'),
        ('vehicle_check', 'Vehicle Check'),
        ('gear_check',    'Gear Check'),
        ('other',         'Other'),
    ]
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('done',        'Done'),
        ('skipped',     'Skipped'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner      = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                     related_name='tasks')
    task_type    = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES)
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True, default='')
    priority     = models.CharField(max_length=10, choices=PRIORITY_CHOICES,
                                    default='medium')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to  = models.ForeignKey(PartnerStaff, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='tasks')
    linked_room  = models.ForeignKey(PartnerRoom, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='tasks')
    linked_guest = models.ForeignKey(PartnerGuestRecord, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='tasks')
    due_at       = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes        = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_tasks'
        ordering  = ['-created_at']

    def __str__(self):
        return f'{self.task_type} — {self.title} [{self.status}]'


# ── Vehicles ──────────────────────────────────────────────────────────────────

class PartnerVehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('hatchback',       'Hatchback'),
        ('sedan',           'Sedan'),
        ('suv',             'SUV'),
        ('innova',          'Innova / Crysta'),
        ('tempo_traveller', 'Tempo Traveller'),
        ('van',             'Van (Force/Eeco)'),
        ('mini_bus',        'Mini Bus'),
        ('bus',             'Bus'),
        ('bike',            'Bike'),
        ('other',           'Other'),
    ]
    STATUS_CHOICES = [
        ('available',   'Available'),
        ('in_use',      'In Use'),
        ('maintenance', 'Maintenance'),
        ('inactive',    'Inactive'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner          = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                         related_name='vehicles')
    vehicle_type     = models.CharField(max_length=30, choices=VEHICLE_TYPE_CHOICES)
    make             = models.CharField(max_length=100, blank=True, default='')
    model            = models.CharField(max_length=100, blank=True, default='')
    year             = models.PositiveIntegerField(null=True, blank=True)
    registration_no  = models.CharField(max_length=50, unique=True)
    capacity_persons = models.PositiveIntegerField(default=4)
    fuel_type        = models.CharField(max_length=20, blank=True, default='')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                        default='available')
    rc_photo         = models.CharField(max_length=500, blank=True, default='')
    insurance_photo  = models.CharField(max_length=500, blank=True, default='')
    insurance_expiry = models.DateField(null=True, blank=True)
    permit_photo     = models.CharField(max_length=500, blank=True, default='')
    permit_expiry    = models.DateField(null=True, blank=True)
    notes            = models.TextField(blank=True, default='')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_vehicles'

    def __str__(self):
        return (f'{self.registration_no} — '
                f'{self.vehicle_type} ({self.partner.business_name})')


class VehicleDriverLink(models.Model):
    """Links a driver (PartnerStaff role=driver) to a vehicle."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle    = models.ForeignKey(PartnerVehicle, on_delete=models.CASCADE,
                                   related_name='driver_links')
    driver     = models.ForeignKey(PartnerStaff, on_delete=models.CASCADE,
                                   related_name='vehicle_links')
    is_primary = models.BooleanField(default=True)
    from_date  = models.DateField()
    to_date    = models.DateField(null=True, blank=True)
    notes      = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'vehicle_driver_links'

    def __str__(self):
        return f'{self.driver.name} → {self.vehicle.registration_no}'


class VehicleTripRecord(models.Model):
    STATUS_CHOICES = [
        ('scheduled',  'Scheduled'),
        ('in_transit', 'In Transit'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle       = models.ForeignKey(PartnerVehicle, on_delete=models.CASCADE,
                                      related_name='trips')
    driver        = models.ForeignKey(PartnerStaff, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='trips')
    guest_record  = models.ForeignKey(PartnerGuestRecord, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='vehicle_trips')
    origin        = models.CharField(max_length=255)
    destination   = models.CharField(max_length=255)
    pickup_at     = models.DateTimeField()
    drop_at       = models.DateTimeField(null=True, blank=True)
    actual_pickup = models.DateTimeField(null=True, blank=True)
    actual_drop   = models.DateTimeField(null=True, blank=True)
    km_start      = models.FloatField(null=True, blank=True)
    km_end        = models.FloatField(null=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                     default='scheduled')
    # Loose BBT booking reference
    bbt_booking_ref = models.CharField(max_length=100, blank=True, default='')
    notes         = models.TextField(blank=True, default='')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'vehicle_trip_records'

    def __str__(self):
        return f'{self.origin}→{self.destination} [{self.status}]'


# ── Commodities / Tools / Gear ────────────────────────────────────────────────

class PartnerCommodity(models.Model):
    """
    Generic commodity/tool/gear for all partner types.
    Guides: personal trekking gear, ropes, medical kit.
    Activity providers: rafting gear, harnesses, climbing equipment.
    Vehicle rental: helmets, child seats, accessories.
    Hotels: linen sets, towels, equipment.
    """
    CONDITION_CHOICES = [
        ('new',     'New'),
        ('good',    'Good'),
        ('fair',    'Fair'),
        ('poor',    'Poor'),
        ('retired', 'Retired'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner      = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                     related_name='commodities')
    name         = models.CharField(max_length=255)
    category     = models.CharField(max_length=100, blank=True, default='')
    description  = models.TextField(blank=True, default='')
    quantity     = models.PositiveIntegerField(default=1)
    unit         = models.CharField(max_length=50, blank=True, default='')
    condition    = models.CharField(max_length=20, choices=CONDITION_CHOICES,
                                    default='good')
    serial_no    = models.CharField(max_length=100, blank=True, default='')
    purchase_date= models.DateField(null=True, blank=True)
    purchase_cost= models.DecimalField(max_digits=10, decimal_places=2,
                                       null=True, blank=True)
    # True = each unit tracked individually (e.g. helmets by serial)
    is_individual_tracked = models.BooleanField(default=False)
    notes        = models.TextField(blank=True, default='')
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'partner_commodities'

    def __str__(self):
        return f'{self.name} × {self.quantity} — {self.partner.business_name}'


class CommodityAssignment(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                           editable=False)
    commodity           = models.ForeignKey(PartnerCommodity, on_delete=models.CASCADE,
                                            related_name='assignments')
    guest_record        = models.ForeignKey(PartnerGuestRecord, null=True, blank=True,
                                            on_delete=models.SET_NULL,
                                            related_name='commodity_assignments')
    quantity            = models.PositiveIntegerField(default=1)
    assigned_at         = models.DateTimeField(auto_now_add=True)
    returned_at         = models.DateTimeField(null=True, blank=True)
    condition_on_return = models.CharField(max_length=20, blank=True, default='')
    notes               = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'commodity_assignments'

    def __str__(self):
        return f'{self.commodity.name} → {self.guest_record}'


# ── Closure Dates ─────────────────────────────────────────────────────────────

class PartnerClosureDate(models.Model):
    """
    Partner-defined closure dates.
    Feeds into L1 hard filter — activities from this partner
    are removed from the candidate pool on these dates.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner     = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                    related_name='closure_dates')
    date        = models.DateField()
    reason      = models.CharField(max_length=255, blank=True, default='')
    is_recurring_annually = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label    = 'engine_b2b'
        db_table     = 'partner_closure_dates'
        unique_together = ('partner', 'date')

    def __str__(self):
        return f'{self.partner.business_name} closed {self.date}'


# ── Activity Category Eligibility (platform-wide, admin-managed) ──────────────

class ActivityCategoryEligibility(models.Model):
    """
    Platform-level rule: which partner service types can offer
    each activity category, and whether the provider is also the guide.

    One record per activity category.
    Admin manages this — partners cannot edit it.

    coordinator_eligible = True means a BBT coordinator (internal employee)
    can be assigned to this activity. They are paid internally — no partner
    booking flow is involved.
    """
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

    id                     = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                              editable=False)
    activity_category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES,
                                              unique=True)
    # e.g. ['guide', 'misc_activity_provider']
    eligible_service_types = models.JSONField(default=list)
    # True = the activity provider IS also the guide (rafting, climbing, etc.)
    provider_is_guide      = models.BooleanField(default=False)
    # True = guide/provider must have a verified certification for this category
    requires_certification = models.BooleanField(default=False)
    certification_label    = models.CharField(max_length=255, blank=True, default='')
    # True = a BBT coordinator can be assigned as guide (internal resource)
    coordinator_eligible   = models.BooleanField(default=False)
    notes                  = models.TextField(blank=True, default='')
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'activity_category_eligibility'

    def __str__(self):
        return (f'{self.activity_category} → '
                f'{self.eligible_service_types} '
                f'[provider_is_guide={self.provider_is_guide}]')

    def is_partner_eligible(self, service_type: str) -> bool:
        return service_type in (self.eligible_service_types or [])


# ── Partner Activity Certification ────────────────────────────────────────────

class PartnerActivityCertification(models.Model):
    """
    A guide or misc_activity_provider's certification for a specific
    activity category. Required when ActivityCategoryEligibility
    .requires_certification = True.

    BBT admin verifies each cert before it becomes active.
    One record per partner per category.
    """
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                         editable=False)
    partner           = models.ForeignKey(PartnerProfile, on_delete=models.CASCADE,
                                          related_name='activity_certifications')
    activity_category = models.CharField(max_length=30)
    certification_name= models.CharField(max_length=255)
    issuing_body      = models.CharField(max_length=255, blank=True, default='')
    certified_on      = models.DateField(null=True, blank=True)
    expiry            = models.DateField(null=True, blank=True)
    certificate_photo = models.CharField(max_length=500, blank=True, default='')
    # Verification by BBT admin
    is_verified       = models.BooleanField(default=False)
    verified_by       = models.ForeignKey(
                            'engine_meta.User', null=True, blank=True,
                            on_delete=models.SET_NULL,
                            related_name='cert_verifications')
    verified_at       = models.DateTimeField(null=True, blank=True)
    rejection_reason  = models.TextField(blank=True, default='')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        app_label    = 'engine_b2b'
        db_table     = 'partner_activity_certifications'
        unique_together = ('partner', 'activity_category')

    def __str__(self):
        status = 'verified' if self.is_verified else 'pending'
        return (f'{self.partner.business_name} — '
                f'{self.activity_category} [{status}]')

    @property
    def is_active(self) -> bool:
        if not self.is_verified:
            return False
        if self.expiry:
            from django.utils import timezone
            return self.expiry >= timezone.now().date()
        return True


# ── Activity Service Assignment ───────────────────────────────────────────────

class ActivityServiceAssignment(models.Model):
    """
    Records who is delivering a specific activity node in a booking.

    Three configurations:
      1. Partner is provider AND guide
             provider_partner set, guide_partner None,
             coordinator_user None, provider_is_guide True

      2. Partner is provider, different partner is guide
             provider_partner set, guide_partner set,
             coordinator_user None, provider_is_guide False

      3. BBT coordinator is guide (internal — no partner flow)
             provider_partner set or None,
             coordinator_user set (FK to User with coordinator role),
             provider_is_guide False
             No booking line item created for coordinator —
             they are paid internally.
    """
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('in_progress','In Progress'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ]

    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                             editable=False)
    # Loose reference to engine_b2c.BookingLineItem — no FK across engines
    booking_line_item_ref = models.CharField(max_length=100, blank=True, default='')
    activity_category     = models.CharField(max_length=30)
    activity_name         = models.CharField(max_length=255, blank=True, default='')

    # Who provides the activity (logistics, equipment, etc.)
    provider_partner      = models.ForeignKey(
                                PartnerProfile, null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='provided_assignments')
    provider_is_guide     = models.BooleanField(default=False)

    # Separate guide partner (when provider != guide)
    guide_partner         = models.ForeignKey(
                                PartnerProfile, null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='guided_assignments')

    # BBT coordinator assigned as guide (internal employee)
    # FK to engine_meta.User — coordinator has role 'coordinator'
    coordinator_user      = models.ForeignKey(
                                'engine_meta.User', null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='coordinator_assignments')
    # Guide fee paid to coordinator internally (added to salary record)
    coordinator_guide_fee = models.DecimalField(max_digits=10, decimal_places=2,
                                                default=0)

    status                = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                             default='pending')
    scheduled_at          = models.DateTimeField(null=True, blank=True)
    completed_at          = models.DateTimeField(null=True, blank=True)
    notes                 = models.TextField(blank=True, default='')
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_b2b'
        db_table  = 'activity_service_assignments'

    def __str__(self):
        guide = (
            f'guide={self.guide_partner.business_name}'
            if self.guide_partner else
            f'coordinator={self.coordinator_user}'
            if self.coordinator_user else
            'provider_is_guide'
        )
        return (f'{self.activity_name} [{self.status}] '
                f'provider={self.provider_partner} {guide}')

    def clean(self):
        from django.core.exceptions import ValidationError
        # Must have at least a provider or coordinator
        if not self.provider_partner and not self.coordinator_user:
            raise ValidationError(
                'Assignment must have either a provider_partner '
                'or a coordinator_user.')
        # provider_is_guide and guide_partner are mutually exclusive
        if self.provider_is_guide and self.guide_partner:
            raise ValidationError(
                'provider_is_guide cannot be True when guide_partner is set.')