# class GimpromedRouter:
#     route_app_labels = {'gimpromed'}

#     def db_for_read(self, model, **hints):
#         if model._meta.app_label in self.route_app_labels:
#             return 'gimpromed_sql'
#         return None

#     def db_for_write(self, model, **hints):
#         return None  # nunca escribir

#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         if app_label in self.route_app_labels:
#             return False
#         return None


class GimpromedRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'gimpromed':
            return 'gimpromed_sql'
        elif model._meta.app_label == 'precios':
            return 'precios'
        elif model._meta.app_label == 'infimas':
            return 'infimas_sql'
        elif model._meta.app_label == 'procesos':
            return 'procesos_sercop'
        return None

    def db_for_write(self, model, **hints):
        return None  # solo lectura

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False  # ninguna migración en DB externas