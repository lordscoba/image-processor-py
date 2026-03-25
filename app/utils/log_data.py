import geoip2.database

from app.utils.profiler import profile_performance

reader = geoip2.database.Reader("app/geo/GeoLite2-Country.mmdb")

@profile_performance
def get_country_from_ip(ip: str) -> str:
    try:
        response = reader.country(ip)

        name = response.country.name
        code = response.country.iso_code

        if name:
            return name
        if code:
            return code

        return "Unknown"

    except Exception:
        return "Unknown"
def get_real_ip(request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host
