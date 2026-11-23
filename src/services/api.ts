
const BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the server. Is the backend running?"
    );
  }

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const body = await response.json();

      detail =
        typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail ?? body);
    } catch {
      // Keep the original status text if the response is not JSON.
    }

    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string): Promise<T> => {
    return request<T>(path);
  },

  post: <T>(
    path: string,
    body?: unknown
  ): Promise<T> => {
    return request<T>(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
    });
  },

  upload: <T>(
    path: string,
    file: File
  ): Promise<T> => {
    const formData = new FormData();

    // Must match FastAPI's parameter: file: UploadFile
    formData.append("file", file);

    return request<T>(path, {
      method: "POST",
      body: formData,
    });
  },
};
