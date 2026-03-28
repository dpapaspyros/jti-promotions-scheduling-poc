import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { beforeAll, afterAll, afterEach, describe, it, expect, beforeEach } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import ProtectedRoute from "../components/ProtectedRoute";
import HomePage from "../pages/HomePage";
import { handlers } from "./handlers";

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderHomePage() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div data-testid="login-page" />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

describe("HomePage", () => {
  beforeEach(() => {
    localStorage.setItem("jti_access", "fake-access-token");
    localStorage.setItem("jti_refresh", "fake-refresh-token");
    localStorage.setItem("jti_user", JSON.stringify({ username: "admin" }));
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("displays the API message on success", async () => {
    renderHomePage();

    await waitFor(() => {
      expect(screen.getByText("Hello, world!")).toBeInTheDocument();
    });
  });

  it("redirects to /login when API returns 401", async () => {
    server.use(
      http.get("/api/hello/", () => {
        return new HttpResponse(null, { status: 401 });
      })
    );

    renderHomePage();

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
    expect(localStorage.getItem("jti_access")).toBeNull();
  });

  it("shows error message when API returns a non-401 error", async () => {
    server.use(
      http.get("/api/hello/", () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    renderHomePage();

    await waitFor(() => {
      expect(
        screen.getByText("Could not load data from API.")
      ).toBeInTheDocument();
    });
  });
});
