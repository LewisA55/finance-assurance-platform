# LinkedIn Project Screenshots

These 16:9 screenshots are captured from the local production-shaped product
journey with the governed API and browser-local analytical runtime available.

Recommended featured-project order:

1. `01-cfo-command-centre.png`
2. `02-financial-performance.png`
3. `03-cash-and-capital.png`
4. `06-planning-and-valuation.png`
5. `07-assurance-casework.png`

The remaining Revenue & SaaS and Assurance & Control Readiness views are
available for a longer launch post or portfolio case study.

To regenerate the complete set, start the governed API and web product using
the same environment used by the browser journey tests, then run from `web/`:

```text
SCREENSHOT_BASE_URL=http://127.0.0.1:3100 npm run capture:linkedin
```

On PowerShell, set `SCREENSHOT_BASE_URL` as an environment variable before
running the npm command.
