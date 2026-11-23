/**
 * Urban Air Quality Assistant - Core Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const appSidebar = document.getElementById('appSidebar');
    if (sidebarToggle && appSidebar) {
        sidebarToggle.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth < 992 &&
                !appSidebar.contains(e.target) &&
                !sidebarToggle.contains(e.target) &&
                appSidebar.classList.contains('show')) {
                appSidebar.classList.remove('show');
            }
        });
    }

    // 2. City Search with Autocomplete
    const searchInput = document.getElementById('globalCitySearch');
    const searchDropdown = document.getElementById('searchResultsDropdown');

    if (searchInput && searchDropdown) {
        let debounceTimer;

        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 2) {
                searchDropdown.style.display = 'none';
                searchDropdown.innerHTML = '';
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/search-locations/?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        searchDropdown.innerHTML = '';
                        if (data.results && data.results.length > 0) {
                            data.results.forEach(loc => {
                                const item = document.createElement('div');
                                item.className = 'search-item';
                                item.innerHTML = `
                                    <div class="fw-semibold"><i class="bi bi-geo-alt me-1 text-primary"></i>${loc.name}</div>
                                    <small class="text-muted">${loc.display_name}</small>
                                `;
                                item.addEventListener('click', () => {
                                    setActiveLocation(loc.name, loc.latitude, loc.longitude);
                                });
                                searchDropdown.appendChild(item);
                            });
                            searchDropdown.style.display = 'block';
                        } else {
                            searchDropdown.innerHTML = '<div class="p-3 text-muted text-center small">No matching cities found.</div>';
                            searchDropdown.style.display = 'block';
                        }
                    })
                    .catch(err => {
                        console.error('Search error:', err);
                    });
            }, 300);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.style.display = 'none';
            }
        });
    }

    // 3. Helper to switch location and reload
    window.setActiveLocation = function (cityName, lat, lon) {
        fetch('/api/set-location/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                city_name: cityName,
                latitude: lat,
                longitude: lon
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        })
        .catch(err => console.error('Failed to update location:', err));
    };

    // Helper to get CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    window.getCookie = getCookie;
});
