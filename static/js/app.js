document.addEventListener("DOMContentLoaded", () => {
    const gridContainer = document.querySelector(".artist-grid");

    // Fetch data from the Python Backend API
    fetch("/api/artists")
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(artists => {
            renderArtists(artists);
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            gridContainer.innerHTML = "<p>Failed to load artists.</p>";
        });

    // Manipulate the DOM to display the cards
    function renderArtists(artistsList) {
        gridContainer.innerHTML = ""; // Remove the "Loading..." text

        artistsList.forEach(artist => {
            // Create the card element
            const card = document.createElement("div");
            card.classList.add("artist-card");

            // Fill it with content
            card.innerHTML = `
                <img src="${artist.image}" alt="${artist.name}" style="width:100%; border-radius:8px;">
                <h2>${artist.name}</h2>
                <p><strong>Genre:</strong> ${artist.genre}</p>
                <p><strong>Decade:</strong> ${artist.decade}</p>
                <p><strong>Region:</strong> ${artist.region}</p>
            `;

            // Append it to the grid container
            gridContainer.appendChild(card);
        });
    }
});