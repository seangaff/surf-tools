document.addEventListener('DOMContentLoaded', async () => {
    const spotListEl = document.getElementById('spot-list');
    const video = document.getElementById('video');
    const titleEl = document.getElementById('stream-title');
    const locationEl = document.getElementById('stream-location');
    const placeholderEl = document.getElementById('video-placeholder');
    const searchEl = document.getElementById('spot-search');
    const filtersEl = document.getElementById('source-filters');
    const countEl = document.getElementById('cam-count');
    const noteEl = document.getElementById('load-note');

    const FILTERS = [
        { id: 'all', label: 'All' },
        { id: 'pacifica', label: 'Pacifica' },
        { id: 'bay-area', label: 'Bay Area' },
        { id: 'san-diego', label: 'San Diego' },
    ];

    let hls = null;
    let spots = [];
    let activeFilter = 'all';
    const collapsed = new Set();

    const catalogs = [
        { url: '../data/filteredSpotData.json', fallbackSource: 'Favorites' },
        { url: '../data/sanDiegoSpotData.json', fallbackSource: 'San Diego' },
    ];

    const loaded = await Promise.all(catalogs.map(loadCatalog));
    const failures = loaded.filter(result => result.error);
    spots = loaded.flatMap(result => result.spots);

    if (!spots.length) {
        spotListEl.innerHTML = '<p class="empty-list">Error loading data</p>';
        return;
    }

    if (failures.length) {
        noteEl.hidden = false;
        noteEl.textContent = `Could not load ${failures.map(result => result.source).join(', ')}.`;
    }

    renderFilters();
    renderSpots();

    searchEl.addEventListener('input', renderSpots);
    filtersEl.addEventListener('click', event => {
        const button = event.target.closest('button[data-filter]');
        if (!button) return;
        activeFilter = button.dataset.filter;
        renderFilters();
        renderSpots();
    });

    async function loadCatalog(catalog) {
        try {
            const response = await fetch(catalog.url);
            if (!response.ok) throw new Error(String(response.status));
            const data = await response.json();
            const list = data.spots || data.favorites || [];
            const source = data.region || catalog.fallbackSource;
            return {
                source,
                spots: list.map(spot => ({ ...spot, source, filters: coastFilters(spot, source) })),
            };
        } catch (error) {
            console.error(`Failed to load ${catalog.url}`, error);
            return { source: catalog.fallbackSource, spots: [], error };
        }
    }

    // Marin (about 38.3N) through Santa Cruz (about 36.9N). Pacifica sits inside that stretch.
    function coastFilters(spot, source) {
        const filters = new Set();
        const subregion = (spot.subregionName || '').toLowerCase();
        const lat = spot.lat;

        if (subregion === 'pacifica') filters.add('pacifica');
        if (typeof lat === 'number' && lat <= 38.35 && lat >= 36.85) filters.add('bay-area');
        if (source === 'San Diego' || subregion.includes('san diego')) filters.add('san-diego');
        return filters;
    }

    function renderFilters() {
        filtersEl.replaceChildren();
        FILTERS.forEach(filter => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chip';
            button.dataset.filter = filter.id;
            button.textContent = filter.label;
            button.setAttribute('aria-pressed', String(filter.id === activeFilter));
            filtersEl.appendChild(button);
        });
    }

    function playableCameras(spot) {
        return (spot.cameras || []).filter(camera => camera.streamUrl && !camera.isDown);
    }

    function matchingCameras(spot, query) {
        const cameras = playableCameras(spot);
        if (!query) return cameras;
        const spotText = `${spot.name} ${spot.subregionName || ''} ${spot.source}`.toLowerCase();
        if (spotText.includes(query)) return cameras;
        return cameras.filter(camera => (camera.title || '').toLowerCase().includes(query));
    }

    function renderSpots() {
        const query = searchEl.value.trim().toLowerCase();
        const groups = new Map();

        spots.forEach(spot => {
            if (activeFilter !== 'all' && !spot.filters.has(activeFilter)) return;
            const cameras = matchingCameras(spot, query);
            if (!cameras.length) return;

            const name = spot.subregionName || 'Other';
            if (!groups.has(name)) {
                groups.set(name, { name, lat: -Infinity, entries: [] });
            }
            const group = groups.get(name);
            group.lat = Math.max(group.lat, spot.lat || -Infinity);
            group.entries.push({ spot, cameras });
        });

        const ordered = [...groups.values()].sort((a, b) => b.lat - a.lat);
        let camCount = 0;
        spotListEl.replaceChildren();

        if (!ordered.length) {
            const empty = document.createElement('p');
            empty.className = 'empty-list';
            empty.textContent = 'No cams match';
            spotListEl.appendChild(empty);
            countEl.textContent = '0 cams';
            return;
        }

        ordered.forEach(group => {
            group.entries.sort((a, b) => (b.spot.lat || 0) - (a.spot.lat || 0));
            const groupCount = group.entries.reduce((sum, entry) => sum + entry.cameras.length, 0);
            camCount += groupCount;

            const groupEl = document.createElement('div');
            groupEl.className = 'spot-group';
            if (!query && collapsed.has(group.name)) groupEl.classList.add('collapsed');

            const title = document.createElement('button');
            title.type = 'button';
            title.className = 'group-title';
            title.setAttribute('aria-expanded', String(!groupEl.classList.contains('collapsed')));

            const label = document.createElement('span');
            label.textContent = `${group.name} · ${groupCount}`;
            const chevron = document.createElement('span');
            chevron.className = 'chevron';
            chevron.textContent = '▾';
            title.append(label, chevron);
            title.addEventListener('click', () => {
                const willCollapse = !groupEl.classList.contains('collapsed');
                groupEl.classList.toggle('collapsed', willCollapse);
                title.setAttribute('aria-expanded', String(!willCollapse));
                if (willCollapse) collapsed.add(group.name);
                else collapsed.delete(group.name);
            });
            groupEl.appendChild(title);

            const body = document.createElement('div');
            body.className = 'group-body';
            group.entries.forEach(({ spot, cameras }) => {
                const block = document.createElement('div');
                block.className = 'spot-block';

                const spotLabel = document.createElement('div');
                spotLabel.className = 'spot-label';
                spotLabel.textContent = spot.name;
                block.appendChild(spotLabel);

                cameras.forEach(camera => {
                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'spot-item';

                    const camTitle = document.createElement('span');
                    camTitle.className = 'cam-title';
                    camTitle.textContent = camera.title;
                    item.appendChild(camTitle);

                    item.addEventListener('click', () => {
                        document.querySelectorAll('.spot-item').forEach(el => el.classList.remove('active'));
                        item.classList.add('active');
                        loadStream(camera, spot.name, spot.subregionName);
                    });
                    block.appendChild(item);
                });

                body.appendChild(block);
            });

            groupEl.appendChild(body);
            spotListEl.appendChild(groupEl);
        });

        countEl.textContent = `${camCount} cam${camCount === 1 ? '' : 's'}`;
    }

    function loadStream(camera, spotName, subregionName) {
        const streamUrl = camera.streamUrl;

        titleEl.textContent = camera.title;
        locationEl.textContent = [spotName, subregionName].filter(Boolean).join(' · ');
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

        if (Hls.isSupported()) {
            if (hls) hls.destroy();
            hls = new Hls();
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
            hls.on(Hls.Events.ERROR, function (event, data) {
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
