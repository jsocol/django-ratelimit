.. _recipe-per-user:

===================
Per-User Ratelimits
===================

One common business strategy includes adjusting rate limits for
different types of users, or even different individual users for
enterprise sales. With :ref:`callable rates <rates-callable>` it is
possible to implement per-user or per-group rate limits. Here is one
example of how to implement per-user rates.


A ``Ratelimit`` model
=====================

This example leverages the database to store per-user rate limits. Keep
in mind the additional load this may place on your application's
database—which may very well be the resource you intend to protect.
Consider caching these types of queries.

.. code-block:: python

    # myapp/models.py
    class Ratelimit(models.Model):
        group = models.CharField(db_index=True)
        user = models.ForeignKey(null=True)  # One option for "default"
        rate = models.CharField()

        @classmethod
        def get(cls, group, user=None):
            # use cache if possible
            try:
                return cls.objects.get(group=group, user=user)
            except cls.DoesNotExist:
                return cls.objects.get(group=group, user=None)

    # myapp/ratelimits.py
    from myapp.models import Ratelimit
    def per_user(group, request):
        if request.user.is_authenticated:
            return Ratelimit.get(group, request.user)
        return Ratelimit.get(group)

    # myapp/views.py
    @login_required
    @ratelimit(group='search', key='user',
               rate='myapp.ratelimits.per_user')
    def search_view(request):
        # ...

It would be important to consider how to handle defaults, cases where
the rate is not defined in the database, or the group is new, etc. It
would also be important to consider the performance impact of executing
such a query as part of the rate limiting process and consider how to
store this data.
