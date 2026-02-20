class GimpromedRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'gimpromed_sql':
            return 'gimpromed_sql'
        elif model._meta.app_label == 'infimas_sql':
            return 'infimas_sql'
        elif model._meta.app_label == 'procesos_sercop':
            return 'procesos_sercop'
        elif model._meta.app_label == 'precios':
            return 'precios'
        return None

    def db_for_write(self, model, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Bloquear SOLO bases externas
        if db in ['gimpromed_sql', 'infimas_sql', 'procesos_sercop', 'precios']:
            return False

        # Permitir en la BD principal
        return True
