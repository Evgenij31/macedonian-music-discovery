document.addEventListener("DOMContentLoaded", () => {
    const userMenuWrapper = document.querySelector(".user-menu-wrapper");
    const userMenuButton = document.querySelector(".user-menu-button");
    const gridContainer = document.querySelector(".artist-grid");
    const searchInput = document.querySelector("#artist-search");
    const clearButton = document.querySelector(".clear-btn");
    const activeFiltersText = document.querySelector(".active-tags-bar span");
    const filterInputs = document.querySelectorAll('input[type="checkbox"][name]');
    const pagination = document.querySelector(".pagination");
    const paginationStatus = document.querySelector(".pagination-status");
    const paginationButtons = document.querySelectorAll("[data-page-action]");

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

    document.querySelectorAll("[data-favorite-id]").forEach(button => {
        button.addEventListener("click", async event => {
            event.preventDefault();
            event.stopPropagation();

            const response = await fetch(`/api/favorites/${button.dataset.favoriteId}`, {
                method: "POST",
            });

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            if (!response.ok) {
                return;
            }

            const data = await response.json();
            updateFavoriteButton(button, data.is_favorite);

            if (button.closest(".favorites-grid") && !data.is_favorite) {
                button.closest(".artist-card").remove();
                if (!document.querySelector(".favorites-grid .artist-card")) {
                    document.querySelector(".favorites-grid").innerHTML =
                        '<p class="status-msg">You have not saved any artists yet.</p>';
                }
            }
        });
    });

    function updateFavoriteButton(button, isFavorite) {
        button.classList.toggle("is-favorite", isFavorite);
        button.setAttribute("aria-pressed", String(isFavorite));
        button.innerHTML = `<span aria-hidden="true">${isFavorite ? "♥" : "♡"}</span> ${isFavorite ? "Favorite" : "Add to favorites"}`;
    }

    if (!gridContainer || !searchInput || !clearButton || !activeFiltersText) {
        return;
    }

    const filterState = {
        search: "",
        genre: new Set(),
        decade: new Set(),
        region: new Set(),
    };

    let allArtists = [];
    let currentPage = 1;
    const artistsPerPage = 12;

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
        currentPage = 1;
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

            currentPage = 1;
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

        currentPage = 1;
        renderFilteredArtists();
    });

    paginationButtons.forEach(button => {
        button.addEventListener("click", () => {
            currentPage += button.dataset.pageAction === "next" ? 1 : -1;
            renderFilteredArtists();
            gridContainer.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    function renderFilteredArtists() {
        const filteredArtists = allArtists.filter(artist => {
            const matchesSearch = !filterState.search || artist.name.toLowerCase().includes(filterState.search);
            const matchesGenre = matchesFilterGroup("genre", artist.genre);
            const matchesDecade = matchesFilterGroup("decade", artist.decade);
            const matchesRegion = matchesFilterGroup("region", artist.region);

            return matchesSearch && matchesGenre && matchesDecade && matchesRegion;
        });

        const totalPages = Math.max(1, Math.ceil(filteredArtists.length / artistsPerPage));
        currentPage = Math.min(currentPage, totalPages);
        const pageStart = (currentPage - 1) * artistsPerPage;
        const pagedArtists = filteredArtists.slice(pageStart, pageStart + artistsPerPage);

        renderArtists(pagedArtists);
        checkArtistImages(pagedArtists);
        renderPagination(filteredArtists.length, totalPages);
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
            <button class="favorite-button ${artist.is_favorite ? "is-favorite" : ""}" type="button" data-favorite-id="${artist.id}" aria-pressed="${artist.is_favorite}">
                <span aria-hidden="true">${artist.is_favorite ? "♥" : "♡"}</span> ${artist.is_favorite ? "Favorite" : "Add to favorites"}
            </button>
            `;

            gridContainer.appendChild(card);
            const favoriteButton = card.querySelector("[data-favorite-id]");
            favoriteButton.addEventListener("click", async event => {
                event.preventDefault();
                event.stopPropagation();
                const response = await fetch(`/api/favorites/${artist.id}`, { method: "POST" });
                if (response.status === 401) {
                    window.location.href = "/login";
                    return;
                }
                if (!response.ok) {
                    return;
                }
                const data = await response.json();
                artist.is_favorite = data.is_favorite;
                updateFavoriteButton(favoriteButton, data.is_favorite);
            });
        });
    }

    function renderPagination(resultCount, totalPages) {
        if (!pagination) {
            return;
        }

        const shouldShowPagination = resultCount > artistsPerPage;
        pagination.hidden = !shouldShowPagination;

        if (!shouldShowPagination) {
            return;
        }

        paginationStatus.textContent = `Page ${currentPage} of ${totalPages}`;
        paginationButtons.forEach(button => {
            button.disabled =
                button.dataset.pageAction === "previous"
                    ? currentPage === 1
                    : currentPage === totalPages;
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