export default {
  async fetch(request, env) {
    const requestId = request.headers.get("x-request-id") || crypto.randomUUID();
    const traceparent = request.headers.get("traceparent") || `00-${crypto.randomUUID().replaceAll("-", "")}-0000000000000001-01`;
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-headers": "content-type,traceparent,x-request-id",
          "access-control-allow-methods": "GET,HEAD,OPTIONS,POST",
          "access-control-allow-origin": "*",
          "x-request-id": requestId,
          traceparent,
        },
      });
    }

    if (!env.ORIGIN_BASE_URL) {
      return new Response("edge origin is not configured", {
        status: 503,
        headers: { "x-request-id": requestId, traceparent },
      });
    }

    const origin = new URL(url.pathname + url.search, env.ORIGIN_BASE_URL);
    const headers = new Headers(request.headers);
    headers.set("x-request-id", requestId);
    headers.set("traceparent", traceparent);
    headers.set("x-lengeas-edge", "cloudflare");

    const response = await fetch(origin, { method: request.method, headers, body: request.body, redirect: "manual" });
    const output = new Response(response.body, response);
    output.headers.set("x-request-id", requestId);
    output.headers.set("traceparent", traceparent);
    return output;
  },
};
