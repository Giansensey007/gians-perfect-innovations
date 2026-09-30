interface Env {
  ASSETS: Fetcher;
}

const DETAIL = /^\/innovation\/([a-z0-9-]+)\/?$/;

export default {
  async fetch(request, env): Promise<Response> {
    const url = new URL(request.url);
    const match = DETAIL.exec(url.pathname);
    if (match) {
      url.pathname = "/assets/innovation-shell";
      return env.ASSETS.fetch(new Request(url.toString(), request));
    }
    return env.ASSETS.fetch(request);
  },
} satisfies ExportedHandler<Env>;
