# ADA Accessibility Analyzer Controlled PoC

This server records observable requests made by an accessibility analyzer. It does not target internal services or extract sensitive data.

## Run

Python 3, standard library only:

```bash
PUBLIC_BASE_URL=https://your-public-domain.example PORT=8080 python3 server.py
```

Put the service behind an HTTPS reverse proxy or use your normal hosting platform. Set `PUBLIC_BASE_URL` to the publicly reachable HTTPS origin. Do not expose `/logs` publicly; it is localhost-only by design.

Use the printed `PoC URL` in the JSON `url` parameter of `/ada/adacheck`, e.g.:

```json
{"url":"https://your-public-domain.example/?t=YOUR_TOKEN"}
```

Then test the printed `Redirect URL` similarly. Inspect `requests.jsonl` locally, or `curl http://127.0.0.1:8080/logs` from the server.

## Interpreting results

- `/` or `/final`: HTML was requested.
- `/style.css`: stylesheet was requested.
- `/pixel.png`: image was requested.
- `/frame`: iframe was requested.
- `/beacon?kind=javascript`: page JavaScript ran and sent a fetch request. This is **not** remote OS command execution.
- `/redirect` followed by `/final`: redirect was followed.

Each entry records timestamp, method, path, query, source IP, User-Agent and Referer. Use distinct `t` tokens per test to correlate results. Do not treat requests as proof they originated from CDPH until correlated with your test timing and analyzer response. Results depend on browser policies and network restrictions.

**Important:** Never put credentials, cookies, or internal URLs in this test page. Limit testing to systems within the agreed authorization and scope.
