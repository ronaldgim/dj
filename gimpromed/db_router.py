class GimpromedRouter:
    def db_for_read(self, model, **hints):
        
        if model._meta.app_label == 'gimpromed_sql':
            return 'gimpromed_sql'
        
        elif model._meta.app_label == 'infimas_sql':
            return 'infimas_sql'
        
        elif model._meta.app_label == 'procesos_sercop':
            return 'procesos_sercop'
        
        elif model._meta.app_label == 'procesos':
            return 'procesos_sercop'
        
        elif model._meta.app_label == 'precios':
            return 'precios'

        return None

    def db_for_write(self, model, **hints):
        return None  # solo lectura

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False  # ninguna migración en DB externas