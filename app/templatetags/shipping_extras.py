import math

from django import template

register = template.Library()

STATUS_BADGE = {
    'BOOKED': 'bg-slate-500/15 text-slate-300 border-slate-500/25',
    'PICKED_UP': 'bg-sky-500/15 text-sky-300 border-sky-500/25',
    'IN_TRANSIT': 'bg-amber-500/15 text-amber-300 border-amber-500/25',
    'CUSTOMS': 'bg-violet-500/15 text-violet-300 border-violet-500/25',
    'OUT_FOR_DELIVERY': 'bg-cyan-500/15 text-cyan-300 border-cyan-500/25',
    'DELIVERED': 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
    'DELAYED': 'bg-red-500/15 text-red-300 border-red-500/25',
    'CANCELLED': 'bg-white/5 text-white/40 border-white/10',

    'UNPAID': 'bg-red-500/15 text-red-300 border-red-500/25',
    'PAID': 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
    'REFUNDED': 'bg-slate-500/15 text-slate-300 border-slate-500/25',

    'OPEN': 'bg-amber-500/15 text-amber-300 border-amber-500/25',
    'IN_PROGRESS': 'bg-sky-500/15 text-sky-300 border-sky-500/25',
    'WAITING_CUSTOMER': 'bg-violet-500/15 text-violet-300 border-violet-500/25',
    'RESOLVED': 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
    'CLOSED': 'bg-white/5 text-white/40 border-white/10',

    'LOW': 'bg-white/5 text-white/50 border-white/10',
    'MEDIUM': 'bg-sky-500/15 text-sky-300 border-sky-500/25',
    'HIGH': 'bg-amber-500/15 text-amber-300 border-amber-500/25',
    'URGENT': 'bg-red-500/15 text-red-300 border-red-500/25',
}

STATUS_ICON = {
    'BOOKED': 'fa-clipboard-check',
    'PICKED_UP': 'fa-box',
    'IN_TRANSIT': 'fa-truck-fast',
    'CUSTOMS': 'fa-passport',
    'OUT_FOR_DELIVERY': 'fa-truck',
    'DELIVERED': 'fa-circle-check',
    'DELAYED': 'fa-triangle-exclamation',
    'CANCELLED': 'fa-xmark',
}

SERVICE_ICON = {
    'EXPRESS': 'fa-plane',
    'STANDARD': 'fa-truck',
    'SEA': 'fa-ship',
    'ROAD': 'fa-truck-moving',
}

STAGE_ORDER = ['BOOKED', 'PICKED_UP', 'IN_TRANSIT', 'CUSTOMS', 'OUT_FOR_DELIVERY', 'DELIVERED']
STAGE_LABELS = {
    'BOOKED': 'Booked',
    'PICKED_UP': 'Picked Up',
    'IN_TRANSIT': 'In Transit',
    'CUSTOMS': 'Customs',
    'OUT_FOR_DELIVERY': 'Out for Delivery',
    'DELIVERED': 'Delivered',
}


@register.filter
def status_badge(value):
    return STATUS_BADGE.get(value, 'bg-white/5 text-white/50 border-white/10')


@register.filter
def status_icon(value):
    return STATUS_ICON.get(value, 'fa-circle')


@register.filter
def service_icon(value):
    return SERVICE_ICON.get(value, 'fa-box')


@register.filter
def stage_states(shipment):
    """Returns the 6 canonical stages annotated with completed/current/upcoming
    for the vertical shipment stepper. Empty list for cancelled shipments —
    those get their own banner instead of a stepper."""
    if shipment.status == 'CANCELLED':
        return []

    try:
        current_index = STAGE_ORDER.index(shipment.status)
    except ValueError:
        current_index = -1

    stages = []
    for i, key in enumerate(STAGE_ORDER):
        if key == shipment.status:
            state = 'completed' if key == 'DELIVERED' else 'current'
        elif i < current_index:
            state = 'completed'
        else:
            state = 'upcoming'
        stages.append({'key': key, 'label': STAGE_LABELS[key], 'icon': STATUS_ICON[key], 'state': state})
    return stages


@register.simple_tag
def route_map_data(shipment):
    """Lays out shipment.route_points along a gentle flight-path curve for
    the animated route-map diagram. There's no real geocoding in this app
    (see route_points' docstring), so this is a stylized arc rather than
    literal coordinates — each hop bows upward like a flight path, and
    waypoints alternate above/below the baseline so labels never collide."""
    points = shipment.route_points
    n = len(points)
    if n < 2:
        return None

    width, height = 1000, 240
    margin_x = 70
    baseline = height * 0.6
    wave_amp = 50
    arc_bow = 40

    coords = []
    for i, point in enumerate(points):
        t = i / (n - 1)
        x = margin_x + t * (width - 2 * margin_x)
        if i == 0 or i == n - 1:
            y = baseline
        else:
            y = baseline + wave_amp * math.sin(i * math.pi / 2)
        coords.append({
            **point,
            'x': round(x, 1), 'y': round(y, 1),
            'x_pct': round(x / width * 100, 2), 'y_pct': round(y / height * 100, 2),
            'label_below': y >= baseline,
            'is_first': i == 0,
            'is_last': i == n - 1,
        })

    path_d = f"M{coords[0]['x']},{coords[0]['y']}"
    for i in range(1, len(coords)):
        x0, y0 = coords[i - 1]['x'], coords[i - 1]['y']
        x1, y1 = coords[i]['x'], coords[i]['y']
        cy = min(y0, y1) - arc_bow
        cx0 = x0 + (x1 - x0) * 0.35
        cx1 = x0 + (x1 - x0) * 0.65
        path_d += f" C{cx0},{cy} {cx1},{cy} {x1},{y1}"

    current = next((c for c in coords if c['current']), None) if shipment.is_active else None

    return {
        'points': coords,
        'path': path_d,
        'width': width,
        'height': height,
        'current': current,
    }
