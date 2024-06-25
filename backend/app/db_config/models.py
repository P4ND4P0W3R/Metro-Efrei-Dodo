from tortoise import Model, fields

class Agency(Model):
    agency_id = fields.CharField(max_length=255, pk=True)
    agency_name = fields.CharField(max_length=255)
    agency_url = fields.CharField(max_length=255, null=True)
    agency_timezone = fields.CharField(max_length=255)
    agency_lang = fields.CharField(max_length=255, null=True)
    agency_phone = fields.CharField(max_length=255, null=True)
    agency_email = fields.CharField(max_length=255, null=True)
    agency_fare_url = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "agency"

class Route(Model):
    route_id = fields.CharField(max_length=255, pk=True)
    agency = fields.ForeignKeyField("models.Agency", related_name="routes")
    route_short_name = fields.CharField(max_length=255)
    route_long_name = fields.CharField(max_length=255)
    route_desc = fields.TextField(null=True)
    route_type = fields.IntField()
    route_url = fields.CharField(max_length=255, null=True)
    route_color = fields.CharField(max_length=255, null=True)
    route_text_color = fields.CharField(max_length=255, null=True)
    route_sort_order = fields.IntField(null=True)

    class Meta:
        table = "route"

class Calendar(Model):
    service_id = fields.CharField(max_length=255, pk=True)
    monday = fields.BooleanField()
    tuesday = fields.BooleanField()
    wednesday = fields.BooleanField()
    thursday = fields.BooleanField()
    friday = fields.BooleanField()
    saturday = fields.BooleanField()
    sunday = fields.BooleanField()
    start_date = fields.CharField(max_length=8)  # YYYYMMDD
    end_date = fields.CharField(max_length=8)    # YYYYMMDD

    class Meta:
        table = "calendar"

class CalendarDate(Model):
    service_id = fields.CharField(max_length=255)
    date = fields.CharField(max_length=8)   # YYYYMMDD
    exception_type = fields.IntField()

    class Meta:
        table = "calendar_dates"

class Trip(Model):
    trip_id = fields.CharField(max_length=255, pk=True)
    route = fields.ForeignKeyField("models.Route", related_name="trips")
    service = fields.ForeignKeyField("models.Calendar", related_name="trips")
    trip_headsign = fields.CharField(max_length=255)
    trip_short_name = fields.CharField(max_length=255, null=True)
    direction_id = fields.IntField()
    block_id = fields.CharField(max_length=255, null=True)
    shape_id = fields.CharField(max_length=255, null=True)
    wheelchair_accessible = fields.IntField()
    bikes_allowed = fields.IntField()

    class Meta:
        table = "trip"

class Stop(Model):
    stop_id = fields.CharField(max_length=255, pk=True)
    stop_code = fields.CharField(max_length=255, null=True)
    stop_name = fields.CharField(max_length=255)
    stop_desc = fields.TextField(null=True)
    stop_lon = fields.FloatField()
    stop_lat = fields.FloatField()
    zone_id = fields.IntField(null=True)
    stop_url = fields.CharField(max_length=255, null=True)
    location_type = fields.IntField()
    parent_station = fields.CharField(max_length=255, null=True)
    stop_timezone = fields.CharField(max_length=255)
    level_id = fields.CharField(max_length=255, null=True)
    wheelchair_boarding = fields.IntField()
    platform_code = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "stop"

class StopTime(Model):
    trip = fields.ForeignKeyField("models.Trip", related_name="stop_times")
    arrival_time = fields.CharField(max_length=8)  # HH:MM:SS
    departure_time = fields.CharField(max_length=8) # HH:MM:SS
    stop = fields.ForeignKeyField("models.Stop", related_name="stop_times")
    stop_sequence = fields.IntField()
    pickup_type = fields.IntField()
    drop_off_type = fields.IntField()
    local_zone_id = fields.CharField(max_length=255, null=True)
    stop_headsign = fields.CharField(max_length=255, null=True)
    timepoint = fields.IntField()

    class Meta:
        table = "stop_times"
        indexes = [
            ("trip_id", "stop_sequence"),
            ("trip_id",),
            ("stop_id",),
            ("stop_sequence",), 
        ]

class Transfer(Model):
    from_stop = fields.ForeignKeyField("models.Stop", related_name="from_transfers")
    to_stop = fields.ForeignKeyField("models.Stop", related_name="to_transfers")
    transfer_type = fields.IntField()
    min_transfer_time = fields.IntField()

    class Meta:
        table = "transfers"

class Pathway(Model):
    pathway_id = fields.CharField(max_length=255, pk=True)
    from_stop = fields.ForeignKeyField("models.Stop", related_name="from_pathways")
    to_stop = fields.ForeignKeyField("models.Stop", related_name="to_pathways")
    pathway_mode = fields.IntField()
    is_bidirectional = fields.BooleanField()
    length = fields.FloatField()
    traversal_time = fields.IntField()
    stair_count = fields.IntField(null=True)
    max_slope = fields.FloatField(null=True)
    min_width = fields.FloatField(null=True)
    signposted_as = fields.CharField(max_length=255, null=True)
    reversed_signposted_as = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "pathways"

class StopExtension(Model):
    object_id = fields.CharField(max_length=255)
    object_system = fields.CharField(max_length=255)
    object_code = fields.CharField(max_length=255)

    class Meta:
        table = "stop_extensions"

class TripStop(Model):
    trip = fields.ForeignKeyField("models.Trip", related_name="trip_stops", on_delete=fields.CASCADE)
    stop = fields.ForeignKeyField("models.Stop", related_name="trip_stops", on_delete=fields.CASCADE)
    stop_sequence = fields.IntField()

    class Meta:
        table = "trip_stop"
        indexes = [
            ("trip_id", "stop_id"), 
            ("stop_sequence",)
        ]
class RouteStop(Model):
    route = fields.ForeignKeyField("models.Route", related_name="route_stops", on_delete=fields.CASCADE)
    stop = fields.ForeignKeyField("models.Stop", related_name="route_stops", on_delete=fields.CASCADE)

    class Meta:
        table = "route_stop"
        indexes = [
            ("route_id", "stop_id")
        ]