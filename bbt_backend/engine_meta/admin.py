from django.contrib import admin
from engine_meta.models import (
    User, PartnerService, EngineConfig, RegionConfig,
    DietaryMode, AdminAction, ScoringModel, ScoringTrainingSample
)

admin.site.register(User)
admin.site.register(PartnerService)
admin.site.register(EngineConfig)
admin.site.register(RegionConfig)
admin.site.register(DietaryMode)
admin.site.register(AdminAction)
admin.site.register(ScoringModel)
admin.site.register(ScoringTrainingSample)