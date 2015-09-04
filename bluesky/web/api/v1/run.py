"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bsslib.web.lib.auth import b_auth

class BlueSkyRunScheduledJobs(Resource):

    def get(self):
        return ScheduledRuns(REDIS_URL=config.REDIS_URL,
            SKIP_FORM_VALIDATION=config.SKIP_FORM_VALIDATION).get()

    def post(self):
        wrapper = ScheduledRuns(REDIS_URL=config.REDIS_URL,
            SKIP_FORM_VALIDATION=config.SKIP_FORM_VALIDATION)
        wrapper.create(**request.get_json(force=True))
        return '', 200 # TODO: how to return truly empty response body

    def delete(self):
        wrapper = ScheduledRuns(REDIS_URL=config.REDIS_URL,
            SKIP_FORM_VALIDATION=config.SKIP_FORM_VALIDATION)
        wrapper.cancel(**request.form.to_dict())
        return '', 200 # TODO: how to return truly empty response body
