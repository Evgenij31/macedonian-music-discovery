document.addEventListener("DOMContentLoaded", () => {
    const gridContainer = document.querySelector(".artist-grid");
    const searchInput = document.querySelector("#artist-search");
    const clearButton = document.querySelector(".clear-btn");
    const activeFiltersText = document.querySelector(".active-tags-bar span");
    const filterInputs = document.querySelectorAll('input[type="checkbox"][name]');

    const filterState = {
        search: "",
        genre: new Set(),
        decade: new Set(),
        region: new Set(),
    };

    let allArtists = [];

    fetch("/api/artists")
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(artists => {
            allArtists = artists;
            renderFilteredArtists();
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            gridContainer.innerHTML = "<p class=\"status-msg\">Failed to load artists.</p>";
        });

    searchInput.addEventListener("input", event => {
        filterState.search = event.target.value.trim().toLowerCase();
        renderFilteredArtists();
    });

    filterInputs.forEach(input => {
        input.addEventListener("change", event => {
            const { name, value, checked } = event.target;

            if (!filterState[name]) {
                return;
            }

            if (checked) {
                filterState[name].add(value);
            } else {
                filterState[name].delete(value);
            }

            renderFilteredArtists();
        });
    });

    clearButton.addEventListener("click", () => {
        filterState.search = "";
        filterState.genre.clear();
        filterState.decade.clear();
        filterState.region.clear();

        searchInput.value = "";
        filterInputs.forEach(input => {
            input.checked = false;
        });

        renderFilteredArtists();
    });

    function renderFilteredArtists() {
        const filteredArtists = allArtists.filter(artist => {
            const matchesSearch = !filterState.search || artist.name.toLowerCase().includes(filterState.search);
            const matchesGenre = matchesFilterGroup("genre", artist.genre);
            const matchesDecade = matchesFilterGroup("decade", artist.decade);
            const matchesRegion = matchesFilterGroup("region", artist.region);

            return matchesSearch && matchesGenre && matchesDecade && matchesRegion;
        });

        renderArtists(filteredArtists);
        renderActiveFilters(filteredArtists.length);
    }

    function matchesFilterGroup(groupName, artistValue) {
        const selectedValues = filterState[groupName];

        if (!selectedValues || selectedValues.size === 0) {
            return true;
        }

        return selectedValues.has(artistValue);
    }

    function renderArtists(artistsList) {
        gridContainer.innerHTML = "";

        if (artistsList.length === 0) {
            gridContainer.innerHTML = "<p class=\"status-msg\">No artists match the current filters.</p>";
            return;
        }

        artistsList.forEach(artist => {
            const card = document.createElement("article");
            card.classList.add("artist-card");

            card.innerHTML = `
                <img src="${artist.image}" alt="${artist.name}">
                <h2>${artist.name}</h2>
                <p><strong>Genre:</strong> ${artist.genre}</p>
                <p><strong>Decade:</strong> ${artist.decade}</p>
                <p><strong>Region:</strong> ${artist.region}</p>
            `;

            gridContainer.appendChild(card);
        });
    }

    function renderActiveFilters(resultCount) {
        const activeFilters = [];

        if (filterState.search) {
            activeFilters.push(`Search: ${searchInput.value.trim()}`);
        }

        ["genre", "decade", "region"].forEach(groupName => {
            filterState[groupName].forEach(value => {
                activeFilters.push(`${groupName}: ${value}`);
            });
        });

        const summary = activeFilters.length > 0 ? activeFilters.join(" • ") : "None";
        activeFiltersText.textContent = `Active Filters: ${summary} (${resultCount} found)`;
    }
});