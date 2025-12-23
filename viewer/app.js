class ProxyLoader extends Hls.DefaultConfig.loader {
    constructor(config) {
        super(config);
        var load = this.load.bind(this);
        this.load = function (context, config, callbacks) {
            // Modify the URL to go through our proxy
            // Check if it's already proxied to avoid double wrapping
            const originalUrl = context.url;

            if (!context.url.includes('/proxy?url=')) {
                context.url = `/proxy?url=${encodeURIComponent(context.url)}`;
            }

            // Intercept onSuccess to trick hls.js into thinking it got the data from originalUrl
            // This ensures relative paths in playlists are resolved against the original CDN URL
            const onSuccess = callbacks.onSuccess;
            callbacks.onSuccess = function (response, stats, context) {
                // Restore the original URL so HLS.js resolves relative paths correctly
                response.url = originalUrl;
                onSuccess(response, stats, context);
            };

            load(context, config, callbacks);
        };
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const spotListEl = document.getElementById('spot-list');
    const video = document.getElementById('video');
    const titleEl = document.getElementById('stream-title');
    const locationEl = document.getElementById('stream-location');
    const placeholderEl = document.getElementById('video-placeholder');

    let hls = null;

    // Load data
    try {
        const response = await fetch('/filteredSpotData.json');
        const data = await response.json();
        renderSpots(data.favorites);
    } catch (e) {
        console.error("Failed to load spot data", e);
        spotListEl.innerHTML = '<p style="color:red; padding:10px;">Error loading data</p>';
    }

    function renderSpots(favorites) {
        // Group by subregion
        const grouped = {};
        favorites.forEach(spot => {
            if (!grouped[spot.subregionName]) {
                grouped[spot.subregionName] = [];
            }
            grouped[spot.subregionName].push(spot);
        });

        // Clear list
        spotListEl.innerHTML = '';

        Object.keys(grouped).forEach(region => {
            const groupEl = document.createElement('div');
            groupEl.className = 'spot-group';

            const title = document.createElement('div');
            title.className = 'group-title';
            title.textContent = region;
            groupEl.appendChild(title);

            grouped[region].forEach(spot => {
                // If spot has cameras
                if (spot.cameras && spot.cameras.length > 0) {
                    // Add spot item(s). 
                    // The JSON structure shows a spot can have multiple cameras.
                    // We should probably list each camera individually or handle spot selection?
                    // Let's list each camera as a selectable item
                    spot.cameras.forEach(cam => {
                        const item = document.createElement('div');
                        item.className = 'spot-item';
                        item.textContent = `${spot.name} - ${cam.title}`;
                        item.onclick = () => {
                            // Highlight active
                            document.querySelectorAll('.spot-item').forEach(el => el.classList.remove('active'));
                            item.classList.add('active');

                            loadStream(cam, spot.name);
                        };
                        groupEl.appendChild(item);
                    });
                }
            });

            spotListEl.appendChild(groupEl);
        });
    }

    function loadStream(camera, spotName) {
        const streamUrl = camera.streamUrl;

        // Update UI
        titleEl.textContent = camera.title;
        locationEl.textContent = spotName;
        placeholderEl.style.display = 'none';
        video.style.display = 'block';

        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        const isExtensionActive = document.body.getAttribute('data-surfline-extension-active') === 'true';

        if (isMobile || isExtensionActive) {
            const reason = isMobile ? "Mobile Device" : "Chrome Extension";
            console.log(`${reason} detected: Using direct stream connection`);

            // Direct playback logic
            if (Hls.isSupported()) {
                if (hls) hls.destroy();
                hls = new Hls(); // No proxy loader!
                hls.loadSource(streamUrl);
                hls.attachMedia(video);
                hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = streamUrl;
                video.addEventListener('loadedmetadata', () => video.play());
            }
            return;
        }

        if (Hls.isSupported()) {
            if (hls) {
                hls.destroy();
            }

            // Configure HLS to use our custom loader
            // We only need to proxy if we are strictly using the CustomLoader approach.
            // However, hls.js `pLoader` config option is the cleanest way.

            hls = new Hls({
                pLoader: ProxyLoader,
                // We might also need fLoader for fragments if pLoader doesn't cover it?
                // Hls.js docs say pLoader is for playlists, fLoader for fragments.
                // Let's use the same loader class for both.
                fLoader: ProxyLoader
            });

            // The URL we pass to loadSource must be the initial m3u8. 
            // The loader will intercept it.
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, function () {
                video.play();
            });

            hls.on(Hls.Events.ERROR, function (event, data) {
                console.error("HLS Error:", data);
            });

        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // Safari has native HLS support. 
            // It will NOT use our Javascript proxy loader. 
            // We must manually proxy the src URL.
            // AND the m3u8 content itself must contain proxied URLs for the chunks... 
            // WAIT. If we proxy the m3u8, the m3u8 content likely contains relative paths or absolute paths.
            // If absolute paths (likely for CDNs), the browser will hit them directly without Referer.
            // 
            // If Safari native is used, we are in trouble because we can't intercept the segment requests easily 
            // unless we rewrite the m3u8 content on the fly.

            // Fortunately, Hls.js works on most modern browsers EXCEPT iOS Safari (sometimes) where it's native only?
            // Hls.js works on desktop Safari if we force it? No, generally MediaSource extensions are available.

            // For this specific user request ("simple website"), implementing a full M3U8 rewriter 
            // in the python server would be robust but complex.
            // 
            // BUT, since we verified the iPhone UA *avoids* needing the Referer, 
            // native Safari on desktop *might* fail if we just pass a proxy URL because 
            // the segments inside the m3u8 will allow direct connection? 

            // Let's stick to HLS.js for now. It usually works on desktop Chrome/Firefox/Safari.
            // If HLS.js fails on Safari, we might need a fallback.

            // For now, let's just supply the PROXIED url to native player if HLS.js is not supported,
            // and hope the segments don't need Referer or the session cookie carries over? 
            // Actually, if the m3u8 has absolute URLs for segments, the native player will request them directly.
            // Surfline segments usually require Referer.

            // So HLS.js is critical.

            video.src = `/proxy?url=${encodeURIComponent(streamUrl)}`;
            video.addEventListener('loadedmetadata', function () {
                video.play();
            });
        }
    }
});
