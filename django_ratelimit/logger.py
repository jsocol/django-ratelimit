import logging


class RatelimitLogger:

    def __init__(self, name='', level=logging.WARNING,
                 msg_format="Ratelimit: {route} {group} \
{key} {rate} {method}"):
        self.logger_name = name
        self.msg_format = msg_format
        self.level = level

    def log_ratelimit(self, request, group, key, rate,
                      method) -> None:
        logging.getLogger(self.logger_name).log(
            level=self.level,
            msg=self.msg_format
            .format(route=request.resolver_match.route,
                    group=group, key=key, rate=rate, method=method))
