document.addEventListener("DOMContentLoaded", () => {
    const userMenuWrapper = document.querySelector(".user-menu-wrapper");
    const userMenuButton = document.querySelector(".user-menu-button");
    const gridContainer = document.querySelector(".artist-grid");
    const searchInput = document.querySelector("#artist-search");
    const clearButton = document.querySelector(".clear-btn");
    const activeFiltersText = document.querySelector(".active-tags-bar span");
    const filterInputs = document.querySelectorAll('input[type="checkbox"][name]');

    if (userMenuWrapper && userMenuButton) {
        userMenuButton.addEventListener("click", () => {
            const isOpen = userMenuWrapper.classList.contains("is-open");
            userMenuWrapper.classList.toggle("is-open", !isOpen);
        });

        document.addEventListener("click", (event) => {
            if (!userMenuWrapper.contains(event.target)) {
                userMenuWrapper.classList.remove("is-open");
            }
        });
    }

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
        checkArtistImages(filteredArtists);
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
            <a href="../artist/${artist.id}" target="_self" rel="noopener noreferrer">
                <img src="${artist.image}" alt="${artist.name}">
                <h2>${artist.name}</h2>
                <div class="card-meta" aria-label="Artist metadata">
                    <span class="metadata-pill"><strong>Genre</strong><span>${artist.genre}</span></span>
                    <span class="metadata-pill"><strong>Decade</strong><span>${artist.decade}</span></span>
                    <span class="metadata-pill"><strong>Region</strong><span>${artist.region}</span></span>
                </div>
            </a>
            `;

            gridContainer.appendChild(card);
        });
    }

    function checkArtistImages(artistsList) {
        artistsList.forEach(artist => {
            const img = new Image();
            img.src = artist.image;

            img.onerror = () => {
                // Replace with placeholder image on error
                const artistCard = Array.from(gridContainer.children).find(card => {
                    return card.querySelector("h2").textContent === artist.name;
                });

                if (artistCard) {
                    const imgElement = artistCard.querySelector("img");
                    imgElement.src = "/static/images/person-placeholder.png";
                    imgElement.alt = "Placeholder image for missing artist image";
                }
            };
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

    // Check for flash messages and hide after 5 seconds
    const flashMessages = document.querySelectorAll(".flash-messages");
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.animation = "fadeOut 1s ease forwards"; // Apply fade-out animation
                setTimeout(() => {
                    msg.style.display = "none"; // Hide the message after the fade-out animation
                }, 1000);
            });
        }, 5000);
    }
});