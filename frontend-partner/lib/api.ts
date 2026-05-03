export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/partner`
    : 'http://localhost:8000/api/v1/partner';

export async function login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, login_context: 'partner' })
    });
    
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        throw new Error(data.message || data.detail || 'Login failed');
    }
    
    if (typeof window !== 'undefined' && data.access) {
        localStorage.setItem('partner_access_token', data.access);
        if (data.refresh) localStorage.setItem('partner_refresh_token', data.refresh);
    }
    return data;
}

export function logout() {
    localStorage.removeItem('partner_access_token');
    localStorage.removeItem('partner_refresh_token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('partner_access_token') : null;
    
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');
    
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }
    
    const res = await fetch(`${API_BASE}${url}`, { 
        ...options, 
        headers 
    });
    
    const data = await res.json().catch(() => ({}));

    if (res.status === 401) {
        if (typeof window !== 'undefined') logout();
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        throw new Error(data.detail || data.error || `API error: ${res.status}`);
    }
    
    return data;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export async function fetchDashboardStats() {
    return fetchWithAuth('/dashboard/');
}

// ─── Bookings ─────────────────────────────────────────────────────────────────

export async function fetchBookings() {
    return fetchWithAuth('/bookings/');
}

export async function updateBookingStatus(bookingId: string, status: 'confirmed' | 'rejected') {
    return fetchWithAuth(`/bookings/${bookingId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
    });
}

// ─── Notifications ────────────────────────────────────────────────────────────

export async function fetchNotifications() {
    return fetchWithAuth('/notifications/');
}

// ─── Availability ─────────────────────────────────────────────────────────────

export async function fetchAvailability() {
    return fetchWithAuth('/availability/');
}

export async function updateAvailability(date: string, status: string) {
    return fetchWithAuth('/availability/', {
        method: 'POST',
        body: JSON.stringify({ date, status })
    });
}

// ─── Payouts / Earnings ───────────────────────────────────────────────────────

export async function fetchPayouts() {
    return fetchWithAuth('/payouts/');
}

// ─── Services / Inventory ─────────────────────────────────────────────────────

export async function fetchServices() {
    return fetchWithAuth('/services/');
}

export async function createService(data: Record<string, unknown>) {
    return fetchWithAuth('/services/', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function updateService(serviceId: string, data: Record<string, unknown>) {
    return fetchWithAuth(`/services/${serviceId}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
    });
}
