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
