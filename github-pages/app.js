
document.addEventListener('DOMContentLoaded', async () => {
    const spotListEl = document.getElementById('spot-list');
    const video = document.getElementById('video');
    const titleEl = document.getElementById('stream-title');
    const locationEl = document.getElementById('stream-location');
    const placeholderEl = document.getElementById('video-placeholder');

    let hls = null;

    // Load data
    try {
        const response = await fetch('../data/filteredSpotData.json');
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

        if (!isMobile && !isExtensionActive) {
            console.warn("Viewership on desktop without extension may fail due to CORS.");
            alert("This viewer requires a mobile device or the Surfline Referer Injector Chrome extension to function properly on desktop.");
        }

        if (isMobile || isExtensionActive) {
            const reason = isMobile ? "Mobile Device" : "Chrome Extension";
            console.log(`${reason} detected: Using direct stream connection`);
        }

        // Direct playback logic
        if (Hls.isSupported()) {
            if (hls) hls.destroy();
            hls = new Hls(); // No proxy loader!
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
            hls.on(Hls.Events.ERROR, function(event, data) {
                if (data.fatal) {
                    console.error("HLS Error:", data);
                }
            });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = streamUrl;
            video.addEventListener('loadedmetadata', () => video.play());
        }
    }
});
