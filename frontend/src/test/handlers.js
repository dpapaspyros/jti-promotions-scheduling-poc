import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/hello/", () => {
    return HttpResponse.json({ message: "Hello, world!" });
  }),
  http.post("/api/auth/logout/", () => {
    return new HttpResponse(null, { status: 200 });
  }),
];
