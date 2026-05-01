from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    profile_photo = models.ImageField(
        upload_to='profiles/customers/',
        null=True, blank=True,
        help_text='Customer profile photo for partner ID verification.'
    )
    mobile = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nationality = models.CharField(max_length=100, default='Indian')
    roles = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    guest_token = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    class Meta:
        app_label = 'engine_meta'
        db_table = 'users'

    def __str__(self):
        return f'{self.email} ({self.roles})'


class PartnerService(models.Model):
    SERVICE_TYPES = [
        ('hotel', 'Hotel'),
        ('guide', 'Guide'),
        ('cab', 'Cab'),
        ('transport', 'Transport'),
        ('vehicle_rental', 'Vehicle Rental'),
        ('misc_activity_provider', 'Misc Activity Provider'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES)
    license_document = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_count = models.IntegerField(default=0)
    push_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'engine_meta'
        db_table = 'partner_services'
        unique_together = ('user', 'service_type')

    def __str__(self):
        return f'{self.user.email} - {self.service_type}'

class EngineConfig(models.Model):
    id = models.IntegerField(primary_key=True, default=1)

    # ── Push score weights (must sum to 1.0) ────────────────────────────
    w_reward  = models.FloatField(default=0.400)
    w_arc     = models.FloatField(default=0.250)
    w_novelty = models.FloatField(default=0.200)
    w_weather = models.FloatField(default=0.150)

    # ── Graph pipeline ───────────────────────────────────────────────────
    path_efficiency_floor = models.FloatField(default=0.650)
    engine_shortlist_n    = models.IntegerField(default=5)
    yang_buffer_threshold = models.FloatField(default=0.500)
    beam_width            = models.IntegerField(default=50)
    annealing_timeout_s   = models.IntegerField(default=30)
    transit_threshold_min = models.IntegerField(default=45)

    # ── Day structure ────────────────────────────────────────────────────
    day_start_time    = models.TimeField(default='07:00')
    rest_trigger_time = models.TimeField(default='18:00')
    dinner_as_node    = models.BooleanField(default=False)

    # ── Risk and safety ──────────────────────────────────────────────────
    high_risk_threshold    = models.FloatField(default=0.700)
    noc_risk_threshold     = models.FloatField(default=0.650)
    noc_altitude_threshold = models.IntegerField(default=4000)

    # ── Random Forest hyperparameters ────────────────────────────────────
    rf_n_trees          = models.IntegerField(default=100)
    rf_max_depth        = models.IntegerField(default=10)
    rf_min_samples_leaf = models.IntegerField(default=5)

    # ── AI Coordinator ──────────────────────────────────────────────────────
    is_coordinator_active     = models.BooleanField(default=False)
    coordinator_offline_msg   = models.CharField(
        max_length=500,
        default='Our AI assistant is currently under maintenance. '
                'A coordinator will reach out to you shortly if needed.'
    )
    coordinator_storage_quota_mb = models.PositiveIntegerField(default=500)

    # ── Filler rate target ───────────────────────────────────────────────
    filler_rate_min = models.FloatField(default=0.100)
    filler_rate_max = models.FloatField(default=0.180)

    # ── Resourcing ───────────────────────────────────────────────────────
    default_guides_per_vehicle     = models.IntegerField(default=1)
    default_coordinators_per_group = models.IntegerField(default=1)

    # ── Pricing ──────────────────────────────────────────────────────────
    assistance_tier_fees = models.JSONField(default=dict)
    coverage_floor       = models.JSONField(default=dict)
    custom_coefficients  = models.JSONField(default=dict)

    # ── External API toggles ─────────────────────────────────────────────
    bookingcom_enabled   = models.BooleanField(default=True)
    bookingcom_api_key   = models.CharField(max_length=255, blank=True, default='')
    bookingcom_affiliate = models.CharField(max_length=100, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'engine_meta'
        db_table  = 'engine_config'

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)
        try:
            from blueberry_backend.communications import invalidate_engine_config_cache
            invalidate_engine_config_cache()
        except Exception:
            pass

    def __str__(self):
        return f'EngineConfig w={self.w_reward}/{self.w_arc}/{self.w_novelty}/{self.w_weather}'


class RegionConfig(models.Model):
    REGION_CHOICES = [
        ('GHW', 'Garhwal'),
        ('KMN', 'Kumaon'),
        ('HPS', 'HP Spiti/Manali'),
        ('HSD', 'HP Shimla/Kinnaur'),
        ('LDK', 'Ladakh/Kashmir'),
        ('RAJ', 'Rajasthan'),
        ('PNJ', 'Punjab'),
        ('HRY', 'Haryana'),
        ('ASM', 'Assam'),
        ('MEG', 'Meghalaya'),
        ('ARP', 'Arunachal'),
        ('SKM', 'Sikkim'),
        ('NEM', 'NE Mixed'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code           = models.CharField(max_length=3, choices=REGION_CHOICES,
                                      unique=True, null=True, blank=True)
    name           = models.CharField(max_length=255)
    coverage_floor      = models.JSONField(default=dict)
    required_categories = models.JSONField(default=list)
    default_season      = models.CharField(max_length=20, default='summer')
    is_active           = models.BooleanField(default=True)

    # Bounding box — normalises GPS into [0,1] for feature vector dims [43][44]
    lat_min = models.FloatField(null=True, blank=True)
    lat_max = models.FloatField(null=True, blank=True)
    lon_min = models.FloatField(null=True, blank=True)
    lon_max = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_meta'
        db_table  = 'region_config'

    def __str__(self):
        return f'{self.code or ""} — {self.name}'

    @property
    def lat_range(self):
        if self.lat_min is not None and self.lat_max is not None:
            return self.lat_max - self.lat_min
        return None

    @property
    def lon_range(self):
        if self.lon_min is not None and self.lon_max is not None:
            return self.lon_max - self.lon_min
        return None

    def normalise_lat(self, lat: float) -> float:
        r = self.lat_range
        return ((lat - self.lat_min) / r) if r else 0.5

    def normalise_lon(self, lon: float) -> float:
        r = self.lon_range
        return ((lon - self.lon_min) / r) if r else 0.5

class DietaryMode(models.Model):
    MODES = [
        ('no_restriction', 'No Restriction'),
        ('vegetarian', 'Vegetarian'),
        ('non_pungent', 'Non Pungent'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enum_value = models.CharField(max_length=30, choices=MODES, unique=True)
    canonical_text = models.TextField()

    class Meta:
        app_label = 'engine_meta'
        db_table = 'dietary_modes'

    def __str__(self):
        return self.enum_value


class AdminAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='actions')
    action_type = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=255)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'engine_meta'
        db_table = 'admin_actions'

    def delete(self, *args, **kwargs):
        raise Exception('AdminAction records are append-only.')

    def __str__(self):
        return f'{self.actor.email} - {self.action_type} at {self.timestamp}'


class ScoringModel(models.Model):
    SCORE_TYPES = [
        ('effort_score',       'Effort Score'),
        ('reward_score',       'Reward Score'),
        ('recovery_coeff',     'Recovery Coefficient'),
        ('significance_score', 'Significance Score'),
        ('tone',               'Tone Classification'),
        ('is_filler',          'Is Filler Classification'),
        ('quality_score',      'Quality Score'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score_type = models.CharField(max_length=30, choices=SCORE_TYPES, unique=True)
    model_json = models.TextField(default='{}')
    is_trained = models.BooleanField(default=False)
    training_samples = models.IntegerField(default=0)
    last_trained_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_meta'
        db_table = 'scoring_models'

    def __str__(self):
        return f'{self.score_type} (trained={self.is_trained})'


class ScoringTrainingSample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    features = models.JSONField()
    effort_score = models.FloatField(null=True, blank=True)
    reward_score = models.FloatField(null=True, blank=True)
    recovery_coeff = models.FloatField(null=True, blank=True)
    significance_score = models.FloatField(null=True, blank=True)
    tone = models.CharField(max_length=10, null=True, blank=True)
    is_filler_label = models.CharField(max_length=10, null=True, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'engine_meta'
        db_table = 'scoring_training_samples'

    def __str__(self):
        return f'TrainingSample {self.id}'


class ThirdPartyAPIConfig(models.Model):
    """
    Singleton-per-provider config for all external APIs.
    Admin pastes credentials here. Engine reads from here.
    Cache-invalidated on every save.

    One record per API_KEY. Admin creates records, never deletes —
    just toggles is_active or updates credentials.
    """
    API_CHOICES = [
        # Payment
        ('razorpay',     'Razorpay'),
        # Transport
        ('redbus',       'RedBus'),
        ('abhibus',      'AbhiBus'),
        ('irctc',        'IRCTC (Train)'),
        # Stays
        ('bookingcom',   'Booking.com'),
        # KYC
        ('uidai',        'UIDAI Aadhaar'),
        ('mrz',          'MRZ Passport Scanner'),
        # Future
        ('whatsapp',     'WhatsApp Business API'),
        ('osrm',         'OSRM Routing (self-hosted)'),
    ]
    STATUS_CHOICES = [
        ('unconfigured', 'Unconfigured'),
        ('configured',   'Configured'),
        ('live',         'Live'),
        ('error',        'Error'),
        ('coming_soon',  'Coming Soon'),
        ('disabled',     'Disabled'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    api_key         = models.CharField(max_length=50, choices=API_CHOICES,
                                       unique=True)
    display_name    = models.CharField(max_length=100)
    is_active       = models.BooleanField(default=False)
    is_coming_soon  = models.BooleanField(default=False)
    coming_soon_note= models.CharField(max_length=255, blank=True, default='')

    # Credentials — all encrypted at rest in production
    # Store as JSON: {"key": "...", "secret": "...", "affiliate": "..."}
    # Field names depend on provider — admin sees labels in admin.py
    credentials     = models.JSONField(default=dict)

    # Runtime status — written by health check tasks, not admin
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default='unconfigured')
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error      = models.TextField(blank=True, default='')

    # Metadata
    docs_url        = models.URLField(blank=True, default='')
    internal_notes  = models.TextField(blank=True, default='')
    updated_at      = models.DateTimeField(auto_now=True)
    updated_by      = models.ForeignKey(
                          'User', null=True, blank=True,
                          on_delete=models.SET_NULL,
                          related_name='api_config_edits')

    class Meta:
        app_label    = 'engine_meta'
        db_table     = 'third_party_api_configs'
        verbose_name = 'Third-Party API Config'
        verbose_name_plural = 'Third-Party API Configs'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate cache for this API
        try:
            from django.core.cache import cache
            cache.delete(f'api_config:{self.api_key}')
        except Exception:
            pass

    def get_credential(self, key: str, default=''):
        """Safe credential accessor."""
        return (self.credentials or {}).get(key, default)

    @classmethod
    def get(cls, api_key: str):
        """Returns config or None. Uses cache."""
        from django.core.cache import cache
        cache_key = f'api_config:{api_key}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            obj = cls.objects.get(api_key=api_key)
            cache.set(cache_key, obj, timeout=300)
            return obj
        except cls.DoesNotExist:
            return None

    @classmethod
    def is_enabled(cls, api_key: str) -> bool:
        obj = cls.get(api_key)
        return obj is not None and obj.is_active and not obj.is_coming_soon

    def __str__(self):
        return f'{self.display_name} [{self.status}]'