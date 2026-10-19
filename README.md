# Alumni Fundraising Demo

A fictional University of Arkansas alumni fundraising demonstration.

Open `index.html` in a browser or host the contents with GitHub Pages. No installation or build is required. For GitHub Pages, select **Settings → Pages → Deploy from a branch → main → /(root)**.

## Features

- Overview and fundraising goal progress
- Assigned alumni and shared alumni directory
- Contact history, follow-ups, referrals, and giving records
- Upcoming department events
- Outlook calendar file downloads and Teams scheduling links
- Top donor badges without numbered rankings

## Demonstration only

All initial alumni names and financial records are fictional. Records entered in the demo are saved only in that browser using local storage. They are not synchronized between visitors. The role switcher simulates staff access; it is not secure authentication. Use fictional data only.

University marks and supplied photography belong to their respective owners. This is an independent internship demonstration, not an official university system.

## Analytics and backend demonstration

Select **Admin** in Preview account, then open **Analytics**. Reports include monthly payments, request outcomes, giving by college/source, contact connection rates, fundraiser comparisons, data-quality checks, and CSV exports. The Backend & data view explains relationships and lets you inspect the browser records.

A working SQLite database and local API example is in [backend/](backend/README.md). This is separate from the static website and is not hosted by GitHub Pages.
