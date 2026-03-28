import { http, HttpResponse } from "msw";

export const MOCK_SCHEDULES = [
  {
    id: 1,
    name: "April 2026",
    period_start: "2026-04-01",
    period_end: "2026-04-30",
    status: "Published",
    created_by: "admin",
    created_at: "2026-03-15T10:00:00Z",
    pos_count: 50,
    promoter_count: 54,
  },
  {
    id: 2,
    name: "May 2026",
    period_start: "2026-05-01",
    period_end: "2026-05-31",
    status: "Draft",
    created_by: "admin",
    created_at: "2026-03-20T09:00:00Z",
    pos_count: 30,
    promoter_count: 20,
  },
];

export const MOCK_POS = [
  { id: 1, cdb_code: "A001", name: "Kiosk Alpha", city: "Athens", priority: "Strategic" },
  { id: 2, cdb_code: "A002", name: "Kiosk Beta", city: "Thessaloniki", priority: "Prime" },
];

export const MOCK_PROMOTERS = [
  { id: 1, username: "alice", first_name: "Alice", last_name: "Smith", programme_type: "Permanent", team: "SOUTH TEAM" },
  { id: 2, username: "bob", first_name: "Bob", last_name: "Jones", programme_type: "Exclusive", team: "NORTH TEAM" },
];

export const MOCK_VISITS = [
  {
    id: 1,
    pos: { id: 1, cdb_code: "A001", name: "Kiosk Alpha", city: "Athens", priority: "Strategic" },
    promoter: { id: 1, username: "alice", first_name: "Alice", last_name: "Smith", programme_type: "Permanent", team: "SOUTH TEAM" },
    date: "2026-04-03",
    start_time: "09:00:00",
    end_time: "11:00:00",
    programme_type: "Permanent",
    week_label: "W1",
    action: "",
    comments: "Peak morning window.",
  },
];

export const handlers = [
  http.get("/api/schedules/", () => HttpResponse.json(MOCK_SCHEDULES)),
  http.post("/api/schedules/", () =>
    HttpResponse.json(
      {
        id: 3,
        name: "June 2026",
        period_start: "2026-06-01",
        period_end: "2026-06-30",
        status: "Draft",
        created_by: "admin",
        created_at: "2026-03-28T10:00:00Z",
        pos_count: 2,
        promoter_count: 2,
      },
      { status: 201 }
    )
  ),
  http.get("/api/schedules/:id", ({ params }) =>
    HttpResponse.json(
      MOCK_SCHEDULES.find((s) => s.id === Number(params.id)) ?? MOCK_SCHEDULES[0]
    )
  ),
  http.get("/api/schedules/:id/visits/", () => HttpResponse.json(MOCK_VISITS)),
  http.post("/api/schedules/:id/generate/", () =>
    HttpResponse.json({
      summary: "Generated 1 visit based on peak windows.",
      visits: MOCK_VISITS,
      usage: { prompt_tokens: 400, completion_tokens: 150, total_tokens: 550 },
      errors: [],
    })
  ),
  http.get("/api/pos/", () => HttpResponse.json(MOCK_POS)),
  http.get("/api/promoters/", () => HttpResponse.json(MOCK_PROMOTERS)),
  http.post("/api/auth/logout/", () => new HttpResponse(null, { status: 200 })),
];
