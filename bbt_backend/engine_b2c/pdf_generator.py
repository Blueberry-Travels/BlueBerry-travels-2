"""
PDF Generator for Blueberry Travel Platform.
Uses WeasyPrint (HTML/CSS → PDF).

Two document types:
  1. Trip Itinerary  — full booking, draft or confirmed
  2. Partner Voucher — single line item, sent to each partner

Entry points:
  generate_itinerary_pdf(booking_id, mode='confirmed') → bytes
  generate_partner_voucher_pdf(line_item_id)           → bytes

Both return raw PDF bytes. Caller decides delivery (email / download).
"""

import base64
import logging
import urllib.request
from datetime import date, timedelta
from io import BytesIO

logger = logging.getLogger(__name__)


# ── Colour tokens (matches the visual sample) ─────────────────────────────────
DARK_GREEN  = '#1a3a2a'
MID_GREEN   = '#2d5a3d'
ACCENT      = '#4a8c5c'
LIGHT_GREEN = '#c8e6c4'
PALE_GREEN  = '#f0f7ec'
BORDER      = '#a8d5a0'
TEXT_MAIN   = '#1a3a2a'
TEXT_MUTED  = '#6a8a6e'
TEXT_LIGHT  = '#8aaa88'
AMBER_BG    = '#fef9ec'
AMBER_TEXT  = '#8a6a1a'
AMBER_BORDER= '#e8d090'
WHITE       = '#ffffff'
OFF_WHITE   = '#f7f5f0'


# ── Base CSS shared by both document types ────────────────────────────────────
BASE_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Inter:wght@300;400;500&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

@page {{
    size: A4;
    margin: 0;
}}

body {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: {TEXT_MAIN};
    background: {WHITE};
    line-height: 1.5;
}}

.serif {{ font-family: 'Playfair Display', serif; }}

.page {{
    width: 210mm;
    min-height: 297mm;
    background: {WHITE};
    position: relative;
}}

/* ── Watermark (draft only) ── */
.watermark {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-family: 'Playfair Display', serif;
    font-size: 72px;
    font-weight: 400;
    color: rgba(220, 60, 60, 0.12);
    letter-spacing: 12px;
    white-space: nowrap;
    z-index: 1000;
    pointer-events: none;
}}

/* ── Header ── */
.header {{
    background: {DARK_GREEN};
    padding: 0;
    position: relative;
    overflow: hidden;
}}

.header-hero {{
    width: 100%;
    height: 140px;
    object-fit: cover;
    display: block;
    opacity: 0.55;
}}

.header-hero-placeholder {{
    width: 100%;
    height: 140px;
    background: {MID_GREEN};
}}

.header-overlay {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px 28px 18px;
    background: linear-gradient(transparent, rgba(26,58,42,0.95));
}}

.header-top {{
    background: {DARK_GREEN};
    padding: 16px 28px 0;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.brand-leaf {{
    width: 22px;
    height: 22px;
    background: {ACCENT};
    border-radius: 50% 50% 50% 0;
    transform: rotate(-45deg);
    flex-shrink: 0;
}}

.brand-name {{
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    color: {LIGHT_GREEN};
    font-style: italic;
}}

.brand-sub {{
    font-size: 8px;
    color: #6a9e7a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 1px;
}}

.booking-ref {{
    text-align: right;
}}

.booking-ref .ref {{
    font-size: 12px;
    font-weight: 500;
    color: {LIGHT_GREEN};
    letter-spacing: 1px;
}}

.booking-ref .ref-label {{
    font-size: 8px;
    color: #6a9e7a;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

.booking-ref .ref-date {{
    font-size: 9px;
    color: #6a9e7a;
    margin-top: 2px;
}}

.trip-title {{
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    color: #e8f5e2;
    margin-bottom: 4px;
}}

.trip-dates {{
    font-size: 10px;
    color: #8aba8f;
    margin-bottom: 10px;
}}

.trip-meta {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}

.meta-pill {{
    background: rgba(74,140,92,0.3);
    border: 0.5px solid rgba(74,140,92,0.5);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 9px;
    color: #a8d5a0;
}}

.meta-pill-confirmed {{
    background: rgba(74,140,92,0.45);
    border-color: {ACCENT};
    color: {LIGHT_GREEN};
}}

.divider-gradient {{
    height: 3px;
    background: linear-gradient(90deg, {ACCENT}, {LIGHT_GREEN}, {ACCENT});
}}

/* ── Body ── */
.body {{
    padding: 20px 28px;
}}

.section-label {{
    font-size: 8px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {ACCENT};
    font-weight: 500;
    margin: 0 0 10px;
    padding-bottom: 5px;
    border-bottom: 0.5px solid {BORDER};
}}

/* ── Day header ── */
.day-header {{
    background: {PALE_GREEN};
    border-left: 3px solid {ACCENT};
    padding: 8px 14px;
    margin: 18px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 5px 5px 0;
}}

.day-title {{
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    color: {TEXT_MAIN};
}}

.day-date {{
    font-size: 9px;
    color: {TEXT_MUTED};
}}

/* ── Activity node ── */
.node {{
    display: flex;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 0.5px solid #eaf2e6;
    align-items: flex-start;
}}

.node:last-child {{
    border-bottom: none;
}}

.node-filler {{
    opacity: 0.6;
}}

.node-time {{
    font-size: 10px;
    color: {ACCENT};
    font-weight: 500;
    min-width: 38px;
    padding-top: 2px;
    flex-shrink: 0;
}}

.node-thumb {{
    width: 48px;
    height: 38px;
    object-fit: cover;
    border-radius: 5px;
    flex-shrink: 0;
}}

.node-thumb-placeholder {{
    width: 48px;
    height: 38px;
    background: {PALE_GREEN};
    border-radius: 5px;
    flex-shrink: 0;
    border: 0.5px solid {BORDER};
}}

.node-body {{
    flex: 1;
}}

.node-name {{
    font-size: 12px;
    font-weight: 500;
    color: {TEXT_MAIN};
    margin-bottom: 2px;
}}

.node-desc {{
    font-size: 10px;
    color: {TEXT_MUTED};
    margin-bottom: 5px;
    line-height: 1.45;
}}

.node-meta {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 4px;
}}

.badge {{
    font-size: 9px;
    padding: 2px 7px;
    border-radius: 10px;
}}

.badge-confirmed {{ background: #e8f5e2; color: #2d6e3a; border: 0.5px solid {BORDER}; }}
.badge-pending   {{ background: {AMBER_BG}; color: {AMBER_TEXT}; border: 0.5px solid {AMBER_BORDER}; }}
.badge-filler    {{ background: #f5f5f0; color: #8a8a7a; border: 0.5px solid #d4d4c8; }}
.badge-transit   {{ background: #f0f4f8; color: #5a7a8a; border: 0.5px solid #b8ccd8; }}

.node-duration {{
    font-size: 9px;
    color: {TEXT_LIGHT};
}}

.partner-row {{
    display: flex;
    gap: 8px;
    align-items: center;
    margin-top: 4px;
}}

.partner-name  {{ font-size: 10px; color: {ACCENT}; font-weight: 500; }}
.partner-phone {{ font-size: 10px; color: {TEXT_MUTED}; }}

.noc-note {{
    font-size: 9px;
    color: {AMBER_TEXT};
    background: {AMBER_BG};
    border: 0.5px solid {AMBER_BORDER};
    border-radius: 4px;
    padding: 2px 7px;
    margin-top: 3px;
    display: inline-block;
}}

/* ── Transit node ── */
.transit-row {{
    display: flex;
    gap: 10px;
    align-items: stretch;
    padding: 8px 0 8px 50px;
}}

.transit-spine {{
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 20px;
    flex-shrink: 0;
}}

.transit-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {ACCENT};
    flex-shrink: 0;
}}

.transit-line-v {{
    width: 1px;
    flex: 1;
    background: repeating-linear-gradient(
        to bottom,
        {BORDER} 0,
        {BORDER} 4px,
        transparent 4px,
        transparent 8px
    );
    margin: 2px 0;
}}

.transit-card {{
    flex: 1;
    background: #f5f9f4;
    border: 0.5px solid {BORDER};
    border-radius: 6px;
    padding: 8px 12px;
}}

.transit-from-to {{
    font-size: 10px;
    color: {TEXT_MAIN};
    font-weight: 500;
}}

.transit-from-to span {{
    color: {TEXT_MUTED};
    font-weight: 400;
}}

.transit-mode-row {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 4px 0;
}}

.transit-arrow {{
    color: {ACCENT};
    font-size: 12px;
}}

.transit-mode {{
    font-size: 10px;
    color: {ACCENT};
    font-weight: 500;
}}

.transit-details {{
    font-size: 9px;
    color: {TEXT_MUTED};
}}

/* ── Stay card ── */
.stay-card {{
    background: {PALE_GREEN};
    border: 0.5px solid {BORDER};
    border-radius: 8px;
    overflow: hidden;
    margin: 14px 0;
}}

.stay-photo {{
    width: 100%;
    height: 90px;
    object-fit: cover;
    display: block;
}}

.stay-photo-placeholder {{
    width: 100%;
    height: 60px;
    background: {MID_GREEN};
    opacity: 0.4;
}}

.stay-body {{
    padding: 12px 14px;
}}

.stay-hotel {{
    font-size: 13px;
    font-weight: 500;
    font-family: 'Playfair Display', serif;
    color: {TEXT_MAIN};
    margin-bottom: 3px;
}}

.stay-sub {{
    font-size: 9px;
    color: {TEXT_MUTED};
    margin-bottom: 10px;
}}

.stay-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
}}

.stay-field label {{
    font-size: 8px;
    color: {ACCENT};
    letter-spacing: 0.5px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 2px;
}}

.stay-field span {{
    font-size: 10px;
    color: {TEXT_MAIN};
    font-weight: 500;
}}

.powered-by {{
    font-size: 8px;
    color: {TEXT_MUTED};
    margin-top: 8px;
    font-style: italic;
}}

/* ── Amount row ── */
.amount-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: {PALE_GREEN};
    border-radius: 7px;
    padding: 10px 14px;
    margin: 14px 0 0;
    border: 0.5px solid {BORDER};
}}

.amount-label {{
    font-size: 10px;
    color: {TEXT_MUTED};
}}

.amount-sub {{
    font-size: 9px;
    color: {TEXT_LIGHT};
    margin-top: 2px;
}}

.amount-value {{
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    color: {TEXT_MAIN};
}}

/* ── Info box ── */
.info-box {{
    background: {PALE_GREEN};
    border: 0.5px solid {BORDER};
    border-radius: 7px;
    padding: 12px 14px;
    margin: 14px 0 0;
}}

.info-row {{
    display: flex;
    gap: 6px;
    margin: 3px 0;
    font-size: 10px;
    color: #4a6a50;
}}

.info-dot {{
    color: {ACCENT};
    font-weight: 500;
    flex-shrink: 0;
}}

/* ── Footer ── */
.footer {{
    background: {DARK_GREEN};
    padding: 12px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 24px;
}}

.footer-text {{
    font-size: 9px;
    color: #6a9e7a;
}}

.footer-page {{
    font-size: 9px;
    color: {ACCENT};
}}

/* ── Partner Voucher specific ── */
.voucher-header {{
    background: {DARK_GREEN};
    padding: 20px 28px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}}

.voucher-title {{
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    color: {LIGHT_GREEN};
    margin-top: 10px;
    font-style: italic;
}}

.voucher-sub {{
    font-size: 9px;
    color: #8aba8f;
    margin-top: 3px;
}}

.voucher-card {{
    border: 2px solid {ACCENT};
    border-radius: 10px;
    overflow: hidden;
    margin: 16px 0;
}}

.voucher-card-header {{
    background: {ACCENT};
    padding: 10px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.voucher-card-title {{
    font-family: 'Playfair Display', serif;
    font-size: 14px;
    color: {WHITE};
}}

.voucher-card-ref {{
    font-size: 10px;
    color: {LIGHT_GREEN};
    letter-spacing: 1px;
}}

.voucher-card-body {{
    padding: 14px 16px;
    background: {WHITE};
}}

.voucher-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}}

.voucher-field label {{
    font-size: 8px;
    color: {ACCENT};
    letter-spacing: 1px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 3px;
}}

.voucher-field span {{
    font-size: 12px;
    color: {TEXT_MAIN};
    font-weight: 500;
}}

.voucher-guests {{
    background: {PALE_GREEN};
    border: 0.5px solid {BORDER};
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 10px;
}}

.voucher-guests-title {{
    font-size: 9px;
    color: {ACCENT};
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

.voucher-guest-row {{
    font-size: 10px;
    color: {TEXT_MAIN};
    padding: 2px 0;
    border-bottom: 0.5px solid {BORDER};
}}

.voucher-guest-row:last-child {{
    border-bottom: none;
}}

.voucher-noc-box {{
    background: {AMBER_BG};
    border: 0.5px solid {AMBER_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 10px;
    font-size: 10px;
    color: {AMBER_TEXT};
}}

.voucher-payout {{
    background: {MID_GREEN};
    border-radius: 6px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
}}

.voucher-payout-label {{
    font-size: 9px;
    color: {LIGHT_GREEN};
}}

.voucher-payout-value {{
    font-family: 'Playfair Display', serif;
    font-size: 16px;
    color: {WHITE};
}}

.voucher-instructions {{
    margin-top: 14px;
    font-size: 10px;
    color: {TEXT_MUTED};
    line-height: 1.6;
    border-top: 0.5px solid {BORDER};
    padding-top: 10px;
}}
"""


# ── Image fetching ────────────────────────────────────────────────────────────

def _img_to_base64(url: str) -> str:
    """Fetches image URL and returns base64 data URI. Returns '' on failure."""
    if not url:
        return ''
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Blueberry/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            data = resp.read()
        b64 = base64.b64encode(data).decode()
        return f'data:{content_type};base64,{b64}'
    except Exception as e:
        logger.debug(f'Image fetch failed for {url}: {e}')
        return ''


def _img_tag(url: str, css_class: str, alt: str = '') -> str:
    """Returns <img> tag with base64 src, or placeholder div."""
    src = _img_to_base64(url)
    if src:
        return f'<img src="{src}" class="{css_class}" alt="{alt}">'
    return f'<div class="{css_class}-placeholder"></div>'


# ── Date helpers ──────────────────────────────────────────────────────────────

def _fmt_date(d) -> str:
    if not d:
        return ''
    if isinstance(d, str):
        return d
    return d.strftime('%d %b %Y')


def _fmt_date_long(d) -> str:
    if not d:
        return ''
    if isinstance(d, str):
        return d
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return f'{days[d.weekday()]}, {d.strftime("%d %b %Y")}'


def _fmt_time(t) -> str:
    if not t:
        return ''
    if isinstance(t, str):
        return t[:5]
    return t.strftime('%H:%M')


def _currency_symbol(currency: str) -> str:
    return {'INR': '₹', 'EUR': '€', 'USD': '$'}.get(currency, currency)


# ── Node rendering ────────────────────────────────────────────────────────────

def _render_transit_node(node: dict) -> str:
    """
    Renders a transit node with full journey context:
    From → [mode · duration · distance] → To
    """
    origin      = node.get('origin', node.get('from_name', 'Departure point'))
    destination = node.get('destination', node.get('to_name', 'Arrival point'))
    mode        = node.get('transport_mode', 'Cab').capitalize()
    duration    = node.get('duration_mins', 0)
    distance    = node.get('distance_km', '')

    dur_str = ''
    if duration:
        if duration >= 60:
            h = int(duration // 60)
            m = int(duration % 60)
            dur_str = f'{h}h {m}min' if m else f'{h}h'
        else:
            dur_str = f'{int(duration)} min'

    details_parts = []
    if dur_str:
        details_parts.append(dur_str)
    if distance:
        details_parts.append(f'{distance:.0f} km' if isinstance(distance, float) else f'{distance} km')
    details = ' · '.join(details_parts)

    return f'''
    <div class="transit-row">
      <div class="transit-spine">
        <div class="transit-dot"></div>
        <div class="transit-line-v"></div>
        <div class="transit-dot"></div>
      </div>
      <div class="transit-card">
        <div class="transit-from-to">
          <span>From:</span> {_esc(origin)}
        </div>
        <div class="transit-mode-row">
          <span class="transit-arrow">↓</span>
          <span class="transit-mode">{_esc(mode)}</span>
          <span class="transit-details">{_esc(details)}</span>
        </div>
        <div class="transit-from-to">
          <span>To:</span> {_esc(destination)}
        </div>
      </div>
    </div>'''


def _render_activity_node(node: dict, is_confirmed: bool) -> str:
    name        = node.get('activity_name', '')
    desc        = node.get('description', node.get('short_desc', ''))
    time_str    = node.get('slot_time', node.get('scheduled_time', ''))
    duration    = node.get('duration_hrs', '')
    status      = node.get('status', 'pending')
    is_filler   = node.get('is_filler', False)
    noc         = node.get('noc_required', False)
    noc_date    = node.get('noc_accepted_at', '')
    photo_url   = node.get('photo_url', '')
    partner_name= node.get('partner_name', '')
    partner_phone=node.get('partner_phone', '')

    # Badge
    if is_filler:
        badge = '<span class="badge badge-filler">Optional</span>'
    elif status == 'confirmed':
        badge = '<span class="badge badge-confirmed">✓ Confirmed</span>'
    else:
        badge = '<span class="badge badge-pending">Pending</span>'

    # Duration display
    dur_str = ''
    if duration:
        try:
            h = float(duration)
            dur_str = f'{h:.1f} hrs'.rstrip('0').rstrip('.')
            if '.0 hrs' in dur_str:
                dur_str = dur_str.replace('.0 hrs', ' hrs')
        except Exception:
            dur_str = str(duration)

    # Partner info (only on confirmed doc, only non-filler)
    partner_html = ''
    if is_confirmed and partner_name and not is_filler:
        phone_html = f'<span class="partner-phone">&nbsp;·&nbsp; {_esc(partner_phone)}</span>' if partner_phone else ''
        partner_html = f'''
        <div class="partner-row">
          <span class="partner-name">{_esc(partner_name)}</span>
          {phone_html}
        </div>'''

    # NOC note
    noc_html = ''
    if noc:
        noc_html = f'<div class="noc-note">⚠ High-risk activity — NOC accepted {_esc(str(noc_date)[:10])}</div>'

    # Thumbnail
    thumb = _img_tag(photo_url, 'node-thumb', name) if photo_url else '<div class="node-thumb-placeholder"></div>'

    filler_class = ' node-filler' if is_filler else ''

    return f'''
    <div class="node{filler_class}">
      <div class="node-time">{_esc(_fmt_time(time_str))}</div>
      {thumb}
      <div class="node-body">
        <div class="node-name">{_esc(name)}</div>
        <div class="node-desc">{_esc(desc)}</div>
        <div class="node-meta">
          {badge}
          <span class="node-duration">{dur_str}</span>
        </div>
        {noc_html}
        {partner_html}
      </div>
    </div>'''


# ── Full Itinerary HTML ───────────────────────────────────────────────────────

def _build_itinerary_html(booking, nodes_by_day: dict, mode: str) -> str:
    is_confirmed = (mode == 'confirmed')
    watermark    = '<div class="watermark">DRAFT</div>' if not is_confirmed else ''

    # Header hero image
    hero = _img_tag(
        getattr(booking.region, 'image_url', ''),
        'header-hero', booking.region.name)

    # Status pill
    status_pill = (
        '<span class="meta-pill meta-pill-confirmed">✓ Confirmed</span>'
        if is_confirmed else
        '<span class="meta-pill" style="background:rgba(200,80,80,0.25);border-color:rgba(200,80,80,0.5);color:#f0a0a0;">Draft — not confirmed</span>'
    )

    # Style label
    style_val   = booking.travel_style
    style_label = (
        'Yin / Chill' if style_val <= 0.25 else
        'Mostly Chill' if style_val <= 0.4 else
        'Mixed' if style_val <= 0.6 else
        'Mostly Adventure' if style_val <= 0.85 else
        'Yang / Adventure'
    )

    sym = _currency_symbol(booking.currency)

    nights = (booking.trip_end_date - booking.trip_start_date).days

    # Days HTML
    days_html = ''
    for day_num in sorted(nodes_by_day.keys()):
        day_date = booking.trip_start_date + timedelta(days=day_num - 1)
        nodes    = nodes_by_day[day_num]
        nodes_html = ''
        for node in nodes:
            if node.get('is_transit'):
                nodes_html += _render_transit_node(node)
            else:
                nodes_html += _render_activity_node(node, is_confirmed)
        days_html += f'''
        <div class="day-header">
          <span class="day-title">Day {day_num}</span>
          <span class="day-date">{_fmt_date_long(day_date)}</span>
        </div>
        {nodes_html}'''

    # Stays HTML
    stays_html = _build_stays_section(booking, is_confirmed)

    # Amount
    providers_html = _build_providers_section(booking, is_confirmed)
    amount_html = ''
    if is_confirmed:
        amount_html = f'''
        <div class="amount-row">
          <div>
            <div class="amount-label">Total paid</div>
            <div class="amount-sub">Includes all confirmed activities &amp; stays</div>
          </div>
          <div class="amount-value">{sym} {booking.total_amount:,.0f}</div>
        </div>'''

    # Service providers section
    # Info box
    noc_activities = _get_noc_list(booking)
    noc_html = ''
    if noc_activities:
        noc_html = f'<div class="info-row"><span class="info-dot">●</span><span>NOC accepted for: {_esc(", ".join(noc_activities))}</span></div>'

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{BASE_CSS}</style>
</head>
<body>
<div class="page">
  {watermark}

  <div class="header">
    <div class="header-top">
      <div class="brand">
        <div class="brand-leaf"></div>
        <div>
          <div class="brand-name">Blueberry</div>
          <div class="brand-sub">Travels</div>
        </div>
      </div>
      <div class="booking-ref">
        <div class="ref-label">Booking ref</div>
        <div class="ref">BBT-{str(booking.id)[:6].upper()}</div>
        <div class="ref-date">{_fmt_date(date.today())} · {"CONFIRMED" if is_confirmed else "DRAFT"}</div>
      </div>
    </div>
    {hero}
    <div class="header-overlay">
      <div class="trip-title">{_esc(booking.region.name)} — {_esc(_trip_subtitle(booking))}</div>
      <div class="trip-dates">{_fmt_date(booking.trip_start_date)} → {_fmt_date(booking.trip_end_date)} · {nights} night{"s" if nights != 1 else ""}</div>
      <div class="trip-meta">
        <span class="meta-pill">{_esc(booking.user_name)}</span>
        <span class="meta-pill">{booking.total_guests} guest{"s" if booking.total_guests != 1 else ""}</span>
        <span class="meta-pill">{style_label}</span>
        <span class="meta-pill">{booking.season.capitalize()}</span>
        {status_pill}
      </div>
    </div>
  </div>

  <div class="divider-gradient"></div>

  <div class="body">
    <div class="section-label">Day-by-day itinerary</div>
    {days_html}

    {stays_html}

    {providers_html}

    {amount_html}

    <div class="info-box" style="margin-top:16px;">
      <div class="section-label" style="margin-bottom:8px;">Important information</div>
      <div class="info-row"><span class="info-dot">●</span><span>Blueberry support: +91 80000 00000 · tech@blueberrytravels.co</span></div>
      <div class="info-row"><span class="info-dot">●</span><span>Carry this document on your trip. Partners may verify against their records.</span></div>
      {noc_html}
      <div class="info-row"><span class="info-dot">●</span><span>This document is not a substitute for travel insurance.</span></div>
      {"" if is_confirmed else '<div class="info-row"><span class="info-dot">●</span><span style="color:#c04040;">This is a DRAFT. Booking is not confirmed until all partners accept.</span></div>'}
    </div>
  </div>

  <div class="footer">
    <div>
      <div class="footer-text">www.blueberrytravels.co · tech@blueberrytravels.co</div>
      <div class="footer-text" style="margin-top:2px;">Generated {_fmt_date(date.today())}</div>
    </div>
    <div class="footer-page">Page 1 of 1</div>
  </div>

</div>
</body>
</html>'''


def _build_stays_section(booking, is_confirmed: bool) -> str:
    try:
        stays = booking.line_items.filter(
            source_type__in=['internal', 'bookingcom']
        ).exclude(stay_detail=None)
        if not stays.exists():
            return ''
    except Exception:
        return ''

    html = '<div style="margin-top:20px;"><div class="section-label">Accommodation</div>'
    for li in stays:
        try:
            sd = li.stay_detail
        except Exception:
            continue
        photo = _img_tag(
            getattr(sd, 'photo_url', ''), 'stay-photo', sd.hotel_name)
        powered = f'<div class="powered-by">{_esc(sd.powered_by_label)}</div>' if getattr(sd, 'powered_by_label', '') else ''
        phone   = ''
        if is_confirmed and li.partner_phone if hasattr(li, 'partner_phone') else '':
            phone = f'<div class="stay-field"><label>Contact</label><span>{li.partner_phone}</span></div>'
        html += f'''
        <div class="stay-card">
          {photo}
          <div class="stay-body">
            <div class="stay-hotel">{_esc(sd.hotel_name)}</div>
            <div class="stay-sub">{_esc(sd.room_type)} · {_esc(sd.meal_plan)} · Conf: {_esc(li.partner_id[:8].upper())}</div>
            <div class="stay-grid">
              <div class="stay-field"><label>Check-in</label><span>{_fmt_date(sd.check_in)} · 14:00</span></div>
              <div class="stay-field"><label>Check-out</label><span>{_fmt_date(sd.check_out)} · 11:00</span></div>
              <div class="stay-field"><label>Nights</label><span>{sd.nights}</span></div>
              <div class="stay-field"><label>Rooms</label><span>{sd.rooms_booked}</span></div>
              <div class="stay-field"><label>Adults</label><span>{sd.adults}</span></div>
              {phone}
            </div>
            {powered}
          </div>
        </div>'''
    html += '</div>'
    return html


# ── Partner Voucher HTML ──────────────────────────────────────────────────────

def _build_voucher_html(line_item, booking) -> str:
    sym         = _currency_symbol(booking.currency)
    ref         = f'BBT-{str(booking.id)[:6].upper()}-{str(line_item.id)[:4].upper()}'
    style_val   = booking.travel_style
    style_label = 'Yin/Chill' if style_val <= 0.4 else 'Mixed' if style_val <= 0.6 else 'Yang/Adventure'
    noc_html    = ''
    if line_item.noc_accepted:
        noc_html = f'''
        <div class="voucher-noc-box">
          ⚠ NOC accepted by customer on {str(line_item.noc_accepted_at)[:10] if line_item.noc_accepted_at else "N/A"}.
          Customer has confirmed physical fitness and accepts responsibility for this high-risk activity.
        </div>'''

    passengers_html = ''
    try:
        pax = line_item.passengers.all()
        if pax.exists():
            rows = ''.join(
                f'<div class="voucher-guest-row">{_esc(p.name)} · Age {p.age} · {p.get_gender_display()} · Seat {_esc(p.seat_number)}</div>'
                for p in pax
            )
            passengers_html = f'''
            <div class="voucher-guests">
              <div class="voucher-guests-title">Passengers</div>
              {rows}
            </div>'''
    except Exception:
        pass

    transit_html = ''
    try:
        vt = line_item.vehicle_trips.first()
        if vt:
            transit_html = f'''
            <div class="voucher-guests" style="margin-top:10px;">
              <div class="voucher-guests-title">Route</div>
              <div class="voucher-guest-row">From: {_esc(vt.origin)}</div>
              <div class="voucher-guest-row">To: {_esc(vt.destination)}</div>
              <div class="voucher-guest-row">Pickup: {_fmt_time(vt.pickup_at)}</div>
              {"<div class='voucher-guest-row'>Driver: "+_esc(vt.driver.name)+"</div>" if vt.driver else ""}
            </div>'''
    except Exception:
        pass

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{BASE_CSS}</style>
</head>
<body>
<div class="page">

  <div class="voucher-header">
    <div>
      <div class="brand" style="margin-bottom:8px;">
        <div class="brand-leaf"></div>
        <div>
          <div class="brand-name">Blueberry</div>
          <div class="brand-sub">Travels</div>
        </div>
      </div>
      <div class="voucher-title">Partner Service Voucher</div>
      <div class="voucher-sub">Present this to the customer on the day of service</div>
    </div>
    <div class="booking-ref">
      <div class="ref-label">Voucher ref</div>
      <div class="ref">{ref}</div>
      <div class="ref-date">{_fmt_date(date.today())}</div>
    </div>
  </div>

  <div class="divider-gradient"></div>

  <div class="body">

    <div class="section-label">Service details</div>

    <div class="voucher-card">
      <div class="voucher-card-header">
        <span class="voucher-card-title">{_esc(line_item.activity_name)}</span>
        <span class="voucher-card-ref">✓ CONFIRMED</span>
      </div>
      <div class="voucher-card-body">
        <div class="voucher-grid">
          <div class="voucher-field">
            <label>Customer</label>
            <span>{_esc(booking.user_name)}</span>
          </div>
          <div class="voucher-field">
            <label>Guests</label>
            <span>{line_item.quantity}</span>
          </div>
          <div class="voucher-field">
            <label>Date</label>
            <span>{_fmt_date(line_item.scheduled_date)}</span>
          </div>
          <div class="voucher-field">
            <label>Time</label>
            <span>{_fmt_time(line_item.scheduled_time) or "As arranged"}</span>
          </div>
          <div class="voucher-field">
            <label>Category</label>
            <span>{_esc(line_item.activity_category.replace("_", " ").title())}</span>
          </div>
          <div class="voucher-field">
            <label>Travel style</label>
            <span>{style_label}</span>
          </div>
        </div>
        {passengers_html}
        {transit_html}
        {noc_html}
        <div class="voucher-payout">
          <div>
            <div class="voucher-payout-label">Your payout (post-service)</div>
            <div style="font-size:8px;color:#8aba8f;margin-top:2px;">Transferred by Blueberry within 24h of service completion</div>
          </div>
          <div class="voucher-payout-value">{sym} {line_item.partner_payout:,.0f}</div>
        </div>
        ' + _build_customer_identity_block(booking) + '

        <div class="voucher-instructions">
          <strong>Instructions:</strong><br>
          1. Verify customer identity against booking name before starting service.<br>
          2. Mark service as completed in your Blueberry partner dashboard after delivery.<br>
          3. For any issues on the day, contact Blueberry ops: +91 80000 00000.
        </div>
      </div>
    </div>

    <div class="info-box">
      <div class="section-label" style="margin-bottom:8px;">Customer contact</div>
      <div class="info-row"><span class="info-dot">●</span><span>{_esc(booking.user_name)} · {_esc(booking.user_phone)}</span></div>
      <div class="info-row"><span class="info-dot">●</span><span>Booking ref: BBT-{str(booking.id)[:6].upper()}</span></div>
    </div>

  </div>

  <div class="footer">
    <div>
      <div class="footer-text">www.blueberrytravels.co · tech@blueberrytravels.co</div>
      <div class="footer-text" style="margin-top:2px;">Generated {_fmt_date(date.today())}</div>
    </div>
    <div class="footer-page">Partner copy — do not share with other customers</div>
  </div>

</div>
</body>
</html>'''


# ── HTML → PDF ────────────────────────────────────────────────────────────────

def _html_to_pdf(html: str) -> bytes:
    try:
        from weasyprint import HTML, CSS
        pdf = HTML(string=html).write_pdf()
        return pdf
    except Exception as e:
        logger.error(f'WeasyPrint conversion failed: {e}')
        raise


# ── Public entry points ───────────────────────────────────────────────────────

def generate_itinerary_pdf(booking_id: str, mode: str = 'confirmed') -> bytes:
    """
    mode: 'confirmed' | 'draft'
    Returns raw PDF bytes.
    """
    from engine_b2c.models import Booking

    booking = Booking.objects.select_related('region').prefetch_related(
        'line_items', 'line_items__stay_detail',
        'line_items__passengers',
    ).get(id=booking_id)

    nodes_by_day = _build_nodes_by_day(booking)
    html         = _build_itinerary_html(booking, nodes_by_day, mode)
    return _html_to_pdf(html)


def generate_partner_voucher_pdf(line_item_id: str) -> bytes:
    """
    Generates a single-service voucher PDF for the partner.
    Includes customer profile photo for identity verification.
    Returns raw PDF bytes.
    """
    from engine_b2c.models import BookingLineItem

    li      = BookingLineItem.objects.select_related('booking__region').get(
        id=line_item_id)
    html    = _build_voucher_html(li, li.booking)

    # Inject customer identity block before instructions section
    identity_html = _build_customer_identity_block(li.booking)
    html = html.replace(
        '<div class="voucher-instructions">',
        identity_html + '\n        <div class="voucher-instructions">',
        1
    )
    return _html_to_pdf(html)


def generate_all_vouchers(booking_id: str) -> dict:
    """
    Generates voucher PDFs for every confirmed internal line item.
    Returns {line_item_id: pdf_bytes} dict.
    """
    from engine_b2c.models import Booking

    booking = Booking.objects.prefetch_related('line_items').get(id=booking_id)
    result  = {}
    for li in booking.line_items.filter(
            source_type='internal', status='confirmed'):
        try:
            result[str(li.id)] = generate_partner_voucher_pdf(str(li.id))
        except Exception as e:
            logger.error(f'Voucher generation failed for {li.id}: {e}')
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_nodes_by_day(booking) -> dict:
    """Groups booking line items into {day_number: [node_dicts]}."""
    from collections import defaultdict
    days = defaultdict(list)

    snapshot = booking.itinerary_snapshot or {}
    snap_nodes = snapshot.get('nodes', [])

    if snap_nodes:
        for n in snap_nodes:
            day = n.get('day', 1)
            days[day].append(n)
    else:
        for li in booking.line_items.order_by('scheduled_date', 'scheduled_time'):
            if not li.scheduled_date:
                continue
            delta = (li.scheduled_date - booking.trip_start_date).days + 1
            days[delta].append({
                'activity_name':   li.activity_name,
                'activity_category':li.activity_category,
                'slot_time':       str(li.scheduled_time) if li.scheduled_time else '',
                'duration_hrs':    '',
                'description':     '',
                'status':          li.status,
                'is_filler':       li.is_filler,
                'is_transit':      False,
                'noc_required':    li.noc_accepted,
                'noc_accepted_at': str(li.noc_accepted_at) if li.noc_accepted_at else '',
                'partner_name':    li.partner_name,
                'partner_phone':   '',
                'photo_url':       '',
            })
    return dict(days)


def _get_noc_list(booking) -> list:
    return [
        li.activity_name
        for li in booking.line_items.filter(noc_accepted=True)
    ]


def _trip_subtitle(booking) -> str:
    cats = list(
        booking.line_items.values_list('activity_category', flat=True).distinct()
    )
    if not cats:
        return 'Trip'
    nice = [c.replace('_', ' ').title() for c in cats[:2]]
    return ' & '.join(nice)


def _esc(text: str) -> str:
    """HTML-escape a string."""
    if not text:
        return ''
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

# ── Customer Service Ticket ───────────────────────────────────────────────────

TICKET_CSS = f"""
{BASE_CSS}

@page {{
    size: A6 landscape;
    margin: 0;
}}

.ticket-page {{
    width: 148mm;
    height: 105mm;
    background: {WHITE};
    display: flex;
    flex-direction: column;
    overflow: hidden;
}}

.ticket-left {{
    background: {DARK_GREEN};
    width: 30mm;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px;
    flex-shrink: 0;
}}

.ticket-brand {{
    font-family: 'Playfair Display', serif;
    font-size: 11px;
    color: {LIGHT_GREEN};
    font-style: italic;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    letter-spacing: 2px;
}}

.ticket-wrap {{
    display: flex;
    flex-direction: row;
    height: 100%;
}}

.ticket-right {{
    flex: 1;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.ticket-activity {{
    font-family: 'Playfair Display', serif;
    font-size: 14px;
    color: {TEXT_MAIN};
    margin-bottom: 4px;
}}

.ticket-ref {{
    font-size: 9px;
    color: {ACCENT};
    letter-spacing: 1px;
    font-weight: 500;
    margin-bottom: 8px;
}}

.ticket-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 8px;
}}

.ticket-field label {{
    font-size: 7px;
    color: {TEXT_MUTED};
    letter-spacing: 1px;
    text-transform: uppercase;
    display: block;
}}

.ticket-field span {{
    font-size: 11px;
    color: {TEXT_MAIN};
    font-weight: 500;
}}

.ticket-provider {{
    background: {PALE_GREEN};
    border: 0.5px solid {BORDER};
    border-radius: 5px;
    padding: 6px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.ticket-provider-name {{
    font-size: 10px;
    color: {ACCENT};
    font-weight: 500;
}}

.ticket-provider-phone {{
    font-size: 10px;
    color: {TEXT_MUTED};
}}

.ticket-confirmed {{
    font-size: 8px;
    color: #2d6e3a;
    background: #e8f5e2;
    border: 0.5px solid {BORDER};
    border-radius: 10px;
    padding: 2px 8px;
}}

.ticket-perforated {{
    border-left: 2px dashed {BORDER};
    margin: 0 2px;
    height: 100%;
    flex-shrink: 0;
}}
"""


def _build_ticket_html(line_item, booking) -> str:
    ref      = f'BBT-{str(booking.id)[:6].upper()}-{str(line_item.id)[:4].upper()}'
    sym      = _currency_symbol(booking.currency)

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{TICKET_CSS}</style>
</head>
<body>
<div class="ticket-page">
  <div class="ticket-wrap">

    <div class="ticket-left">
      <div class="ticket-brand">Blueberry Travels</div>
    </div>

    <div class="ticket-perforated"></div>

    <div class="ticket-right">

      <div>
        <div class="ticket-ref">{_esc(ref)}</div>
        <div class="ticket-activity">{_esc(line_item.activity_name)}</div>
      </div>

      <div class="ticket-grid">
        <div class="ticket-field">
          <label>Date</label>
          <span>{_fmt_date(line_item.scheduled_date)}</span>
        </div>
        <div class="ticket-field">
          <label>Time</label>
          <span>{_fmt_time(line_item.scheduled_time) or "As arranged"}</span>
        </div>
        <div class="ticket-field">
          <label>Guests</label>
          <span>{line_item.quantity}</span>
        </div>
        <div class="ticket-field">
          <label>Category</label>
          <span>{_esc(line_item.activity_category.replace("_"," ").title())}</span>
        </div>
      </div>

      <div class="ticket-provider">
        <div>
          <div class="ticket-provider-name">{_esc(line_item.partner_name)}</div>
          <div style="font-size:8px;color:{TEXT_MUTED};">Service provider</div>
        </div>
        <div style="text-align:right;">
          <div class="ticket-confirmed">&#10003; Confirmed</div>
        </div>
      </div>

    </div>

  </div>
</div>
</body>
</html>'''


def generate_customer_tickets_pdf(booking_id: str) -> bytes:
    """
    Generates a single PDF containing one A6-landscape ticket
    per confirmed line item. Customer carries this.
    Returns raw PDF bytes.
    """
    from engine_b2c.models import Booking
    from weasyprint import HTML, CSS

    booking = Booking.objects.select_related('region').prefetch_related(
        'line_items').get(id=booking_id)

    # One HTML page per ticket — WeasyPrint handles page breaks
    tickets_html = ''
    for li in booking.line_items.filter(
            status='confirmed', is_filler=False).order_by(
            'scheduled_date', 'scheduled_time'):
        if li.source_type == 'internal' and li.partner_name:
            tickets_html += _build_ticket_html(li, booking)

    if not tickets_html:
        # Fallback — single blank page
        tickets_html = '<html><body><p>No confirmed activities.</p></body></html>'

    return HTML(string=tickets_html).write_pdf()


# ── Service Providers Section ─────────────────────────────────────────────────

def _build_providers_section(booking, is_confirmed: bool,
                              request_obj=None) -> str:
    """
    Builds the "Your service providers" section at the end of the
    confirmed itinerary PDF.
    Shows: partner business photo, name, phone, activity name.
    Only shown on confirmed document — not on draft.
    """
    if not is_confirmed:
        return ''

    try:
        from engine_b2b.models import PartnerProfile

        # Collect unique confirmed internal partners
        seen = set()
        providers = []
        for li in booking.line_items.filter(
                source_type='internal',
                status='confirmed',
                is_filler=False):
            if not li.partner_id or li.partner_id in seen:
                continue
            seen.add(li.partner_id)
            try:
                partner = PartnerProfile.objects.get(id=li.partner_id)
                photo_url = ''
                if partner.business_photo:
                    photo_url = partner.business_photo.url
                    # Make absolute if needed
                    if not photo_url.startswith('http'):
                        photo_url = f'http://localhost:8000{photo_url}'
                providers.append({
                    'name':           partner.business_name,
                    'phone':          partner.user.mobile or '',
                    'activity_name':  li.activity_name,
                    'photo_url':      photo_url,
                })
            except PartnerProfile.DoesNotExist:
                providers.append({
                    'name':          li.partner_name,
                    'phone':         '',
                    'activity_name': li.activity_name,
                    'photo_url':     '',
                })

        if not providers:
            return ''

        rows_html = ''
        for p in providers:
            photo_html = _img_tag(p['photo_url'], 'node-thumb', p['name']) \
                if p['photo_url'] else \
                '<div class="node-thumb-placeholder"></div>'
            rows_html += f'''
            <div class="node" style="padding:10px 0;border-bottom:0.5px solid #eaf2e6;">
              {photo_html}
              <div class="node-body">
                <div class="node-name">{_esc(p["name"])}</div>
                <div class="node-desc">{_esc(p["activity_name"])}</div>
                <div class="partner-row">
                  <span class="partner-phone">{_esc(p["phone"])}</span>
                </div>
              </div>
            </div>'''

        return f'''
        <div style="margin-top:20px;">
          <div class="section-label">Your service providers</div>
          {rows_html}
        </div>'''

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Providers section failed: {e}')
        return ''


# ── Customer Photo on Partner Confirmation Slip ───────────────────────────────

def _get_customer_photo_b64(booking) -> str:
    """
    Fetches the customer's profile photo as base64 for embedding
    in the partner confirmation slip.
    Returns '' if no photo or fetch fails.
    Privacy: only embedded in partner slip, never in customer PDF.
    """
    try:
        from engine_meta.models import User
        user = User.objects.get(id=booking.user_id)
        if not user.profile_photo:
            return ''
        photo_url = user.profile_photo.url
        if not photo_url.startswith('http'):
            photo_url = f'http://localhost:8000{photo_url}'
        return _img_to_base64(photo_url)
    except Exception:
        return ''


def _build_customer_identity_block(booking) -> str:
    """
    Builds the customer identity block shown on partner confirmation slip.
    Shows: profile photo + name + phone.
    Purpose: partner verifies "this person matches the booking."
    """
    photo_b64 = _get_customer_photo_b64(booking)

    if photo_b64:
        photo_html = f'''
        <img src="{photo_b64}"
             style="width:64px;height:64px;border-radius:50%;
                    object-fit:cover;border:2px solid {ACCENT};
                    flex-shrink:0;"
             alt="Customer photo">'''
    else:
        photo_html = f'''
        <div style="width:64px;height:64px;border-radius:50%;
                    background:{PALE_GREEN};border:2px solid {BORDER};
                    flex-shrink:0;display:flex;align-items:center;
                    justify-content:center;font-size:22px;">
          👤
        </div>'''

    return f'''
    <div style="margin-top:14px;">
      <div class="section-label">Customer to verify</div>
      <div style="display:flex;gap:14px;align-items:center;
                  background:{PALE_GREEN};border:0.5px solid {BORDER};
                  border-radius:8px;padding:12px 14px;">
        {photo_html}
        <div>
          <div style="font-size:13px;font-weight:500;
                      color:{TEXT_MAIN};">{_esc(booking.user_name)}</div>
          <div style="font-size:11px;color:{TEXT_MUTED};
                      margin-top:2px;">{_esc(booking.user_phone)}</div>
          <div style="font-size:10px;color:{ACCENT};margin-top:4px;">
            Verify this person matches the booking before starting service.
          </div>
        </div>
      </div>
    </div>'''
