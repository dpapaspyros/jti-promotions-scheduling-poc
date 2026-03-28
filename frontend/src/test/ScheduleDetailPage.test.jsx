import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@mui/material";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import {
  beforeAll,
  afterAll,
  afterEach,
  describe,
  it,
  expect,
  beforeEach,
} from "vitest";
import { AuthProvider } from "../context/AuthContext";
import ProtectedRoute from "../components/ProtectedRoute";
import ScheduleDetailPage from "../pages/ScheduleDetailPage";
import muiTheme from "../muiTheme";
import { handlers, MOCK_VISITS } from "./handlers";

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderDetailPage(id = "1") {
  return render(
    <ThemeProvider theme={muiTheme}>
      <AuthProvider>
        <MemoryRouter initialEntries={[`/schedules/${id}`]}>
          <Routes>
            <Route
              path="/schedules/:id"
              element={
                <ProtectedRoute>
                  <ScheduleDetailPage />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div data-testid="login-page" />} />
            <Route path="/" element={<div data-testid="home-page" />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

describe("ScheduleDetailPage", () => {
  beforeEach(() => {
    localStorage.setItem("jti_access", "fake-access-token");
    localStorage.setItem("jti_refresh", "fake-refresh-token");
    localStorage.setItem("jti_user", JSON.stringify({ username: "admin" }));
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("renders schedule name and existing visits", async () => {
    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByText("April 2026")).toBeInTheDocument();
    });
    expect(screen.getByText("Kiosk Alpha")).toBeInTheDocument();
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
  });

  it("shows AI generation panel", async () => {
    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByText("AI Schedule Generation")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /regenerate/i })
    ).toBeInTheDocument();
  });

  it("calls generate and displays AI summary", async () => {
    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByText("AI Schedule Generation")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /regenerate/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Generated 1 visit based on peak windows.")
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/550 tokens used/i)).toBeInTheDocument();
  });

  it("shows error when generation fails", async () => {
    server.use(
      http.post("/api/schedules/:id/generate/", () =>
        HttpResponse.json({ error: "OPENAI_API_KEY is not configured on the server." }, { status: 503 })
      )
    );

    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByText("AI Schedule Generation")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /regenerate/i }));

    await waitFor(() => {
      expect(
        screen.getByText("OPENAI_API_KEY is not configured on the server.")
      ).toBeInTheDocument();
    });
  });

  it("redirects to /login when schedule fetch returns 401", async () => {
    server.use(
      http.get("/api/schedules/:id", () => new HttpResponse(null, { status: 401 }))
    );

    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  it("navigates back to home when back button is clicked", async () => {
    renderDetailPage();

    await waitFor(() => {
      expect(screen.getByText("April 2026")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /schedules/i }));

    await waitFor(() => {
      expect(screen.getByTestId("home-page")).toBeInTheDocument();
    });
  });
});
