/**
 * Lightweight API client for the Docket backend.
 * Uses typed paths from openapi-typescript generated docket.ts.
 * All requests include X-User-Id header (dev auth stub).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Dev auth: user id injected from env or default. */
const DEV_USER_ID =
  process.env.NEXT_PUBLIC_DEV_USER_ID ?? "user-attorney";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": DEV_USER_ID,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Events ───────────────────────────────────────────────────────────────────

export async function listEvents(
  matterId: string,
  params?: {
    limit?: number;
    offset?: number;
    kind?: "hearing" | "deadline";
    status?: string;
  }
) {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  if (params?.kind) q.set("kind", params.kind);
  if (params?.status) q.set("status", params.status);
  const qs = q.toString() ? `?${q.toString()}` : "";
  return apiFetch<{
    items: import("../types/docket").components["schemas"]["EventResponse"][];
    total: number;
  }>(`/api/v1/matters/${matterId}/docket/events${qs}`);
}

export async function getEvent(matterId: string, eventId: string) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventDetailResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}`);
}

export async function createEvent(
  matterId: string,
  data: import("../types/docket").components["schemas"]["EventCreate"]
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventResponse"]
  >(`/api/v1/matters/${matterId}/docket/events`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateEvent(
  matterId: string,
  eventId: string,
  data: import("../types/docket").components["schemas"]["EventUpdate"]
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function rescheduleEvent(
  matterId: string,
  eventId: string,
  data: import("../types/docket").components["schemas"]["RescheduleRequest"]
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["RescheduleResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/reschedule`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function postponeEvent(
  matterId: string,
  eventId: string,
  reason: string
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/postpone`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function cancelEvent(
  matterId: string,
  eventId: string,
  reason: string
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function verifyDeadline(
  matterId: string,
  eventId: string,
  notes?: string
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/verify`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export async function exportIcs(
  matterId: string,
  eventId?: string,
  redact = false
): Promise<string> {
  const url = eventId
    ? `/api/v1/matters/${matterId}/docket/events/${eventId}/export.ics?redact=${redact}`
    : `/api/v1/matters/${matterId}/docket/export.ics?redact=${redact}`;

  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "X-User-Id": DEV_USER_ID },
  });
  if (!res.ok) throw new Error(`ICS export failed: ${res.status}`);
  return res.text();
}

// ─── Reminders ────────────────────────────────────────────────────────────────

export async function listReminders(matterId: string, eventId: string) {
  return apiFetch<
    import("../types/docket").components["schemas"]["ReminderResponse"][]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/reminders`);
}

export async function createReminder(
  matterId: string,
  eventId: string,
  data: import("../types/docket").components["schemas"]["ReminderCreate"]
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["ReminderResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/reminders`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateReminderAction(
  matterId: string,
  eventId: string,
  reminderId: string,
  action: import("../types/docket").components["schemas"]["ReminderActionRequest"]
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["ReminderResponse"]
  >(
    `/api/v1/matters/${matterId}/docket/events/${eventId}/reminders/${reminderId}`,
    {
      method: "PATCH",
      body: JSON.stringify(action),
    }
  );
}

// ─── Agenda ───────────────────────────────────────────────────────────────────

export async function getAgenda(
  matterId: string,
  fromDate: string,
  toDate: string
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["AgendaResponse"]
  >(
    `/api/v1/matters/${matterId}/docket/agenda?from=${encodeURIComponent(fromDate)}&to=${encodeURIComponent(toDate)}`
  );
}

// ─── Notifications ────────────────────────────────────────────────────────────

export async function listNotifications(params?: {
  matter_id?: string;
  unread_only?: boolean;
  limit?: number;
  offset?: number;
}) {
  const q = new URLSearchParams();
  if (params?.matter_id) q.set("matter_id", params.matter_id);
  if (params?.unread_only) q.set("unread_only", "true");
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const qs = q.toString() ? `?${q.toString()}` : "";
  return apiFetch<{
    items: import("../types/docket").components["schemas"]["NotificationResponse"][];
    total: number;
  }>(`/api/v1/notifications${qs}`);
}

export async function markNotificationRead(notificationId: string) {
  return apiFetch<
    import("../types/docket").components["schemas"]["NotificationResponse"]
  >(`/api/v1/notifications/${notificationId}/read`, { method: "POST" });
}

export async function markAllNotificationsRead(matterId?: string) {
  return apiFetch<{ updated_count: number }>(`/api/v1/notifications/read-all`, {
    method: "POST",
    body: JSON.stringify(matterId ? { matter_id: matterId } : {}),
  });
}

// ─── Attached Documents ────────────────────────────────────────────────────────

export async function uploadDocument(
  matterId: string,
  eventId: string,
  formData: FormData
) {
  const res = await fetch(
    `${API_BASE}/api/v1/matters/${matterId}/docket/events/${eventId}/documents`,
    {
      method: "POST",
      headers: {
        "X-User-Id": DEV_USER_ID,
      },
      body: formData,
    }
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<
    import("../types/docket").components["schemas"]["AttachedDocumentResponse"]
  >;
}

export async function updateDocumentReview(
  matterId: string,
  eventId: string,
  docId: string,
  reviewStatus: string
) {
  return apiFetch<
    import("../types/docket").components["schemas"]["AttachedDocumentResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/documents/${docId}`, {
    method: "PATCH",
    body: JSON.stringify({ review_status: reviewStatus }),
  });
}

export async function deleteDocument(
  matterId: string,
  eventId: string,
  docId: string
) {
  return apiFetch<{ message?: string }>(
    `/api/v1/matters/${matterId}/docket/events/${eventId}/documents/${docId}`,
    {
      method: "DELETE",
    }
  );
}

export function getDocumentDownloadUrl(
  matterId: string,
  eventId: string,
  docId: string,
  version?: number
) {
  const v = version ? `?version=${version}` : "";
  return `${API_BASE}/api/v1/matters/${matterId}/docket/events/${eventId}/documents/${docId}/download${v}`;
}

// ─── History & Audit ──────────────────────────────────────────────────────────

export async function getEventHistory(matterId: string, eventId: string) {
  return apiFetch<
    import("../types/docket").components["schemas"]["EventHistoryResponse"]
  >(`/api/v1/matters/${matterId}/docket/events/${eventId}/history`);
}

