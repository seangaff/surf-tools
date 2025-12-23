# Installing the Surfline Referer Extension

1.  Open Chrome/Edge.
2.  Go to `chrome://extensions`.
3.  Enable **Developer Mode** (toggle in top right).
4.  Click **Load Unpacked**.
5.  Select the `surf-tools/extension` folder.

Once installed:
- Reload the viewer page.
- Streams should now play **directly** from Surfline (check the Network tab, you will see requests to `cdn-surfline.com` instead of `/proxy`).
- The Python server is now only serving the HTML/JSON, saving massive bandwidth.
