class KYCRouter:
    KYC_APP = 'kyc'

    def db_for_read(self, model, **hints):
        return 'kyc' if model._meta.app_label == self.KYC_APP else 'default'

    def db_for_write(self, model, **hints):
        return 'kyc' if model._meta.app_label == self.KYC_APP else 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == self.KYC_APP or obj2._meta.app_label == self.KYC_APP:
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.KYC_APP:
            return db == 'kyc'
        return db == 'default'