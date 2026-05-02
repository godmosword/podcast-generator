import { afterEach, describe, expect, it, vi } from "vitest";
import { absoluteApiUrl, fetchClassicScript, fetchJob } from "./api";

describe("API URL helpers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("rejects absolute and unexpected API paths", () => {
    expect(() => absoluteApiUrl("https://example.com/api/files/1")).toThrow("Invalid API path.");
    expect(() => absoluteApiUrl("//example.com/api/files/1")).toThrow("Invalid API path.");
    expect(() => absoluteApiUrl("/admin")).toThrow("Invalid API path.");
  });

  it("allows expected server-provided event paths", () => {
    expect(absoluteApiUrl("/api/generate/job-1/events", "/api/generate/")).toBe(
      "http://localhost:8000/api/generate/job-1/events",
    );
  });

  it("encodes job and classic IDs in path params", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "story/id", script: "ok", status: "done" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchJob("job/id 1");
    await fetchClassicScript("story/id 1");

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/generate/job%2Fid%201");
    expect(fetchMock.mock.calls[1][0]).toBe("http://localhost:8000/api/classics/story%2Fid%201/script");
  });
});
