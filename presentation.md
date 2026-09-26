# Macedonian Music Discovery

## Project title

Macedonian Music Discovery

## 1. Project idea and goal

This project was created as a web application for discovering Macedonian artists, music culture, and local talent. The main goal is to build a digital catalog that makes Macedonian music easier to explore, understand, and appreciate.

The website is designed to help users:

- browse and discover artists from North Macedonia
- search by artist name
- filter content by genre, decade, and region
- access cultural and biographical information about musicians
- save favorite artists to a personal list
- explore music in a structured, visual, and user-friendly way

From a web design perspective, the project combines aesthetics, usability, and interactive functionality. From a technical perspective, it demonstrates how a full-stack web application can integrate data collection, database management, user interaction, and front-end design.

---

## 2. Why this project is important

Macedonia has a rich musical heritage, but much of this cultural value is fragmented across different platforms, archives, and communities. This project brings local music into one organized digital space.

The importance of the project is both cultural and technical:

- it preserves and presents local cultural identity
- it gives visibility to artists who may not be widely known
- it promotes digital literacy and creative thinking
- it shows how web technologies can support cultural discovery and education

This makes the project meaningful not only as a student assignment but also as a useful service for music lovers, researchers, and cultural audiences.

---

## 3. Main problem solved

The main problem addressed by this project is the lack of a centralized and modern platform for discovering Macedonian music.

Before such a system, users would have to search across different sources, often without a clear structure, consistent information, or easy filtering. This application solves that by creating a single web interface where the information is organized and visually accessible.

The project also answers a broader issue in digital culture: how to turn raw information into a usable and engaging experience for users.

---

## 4. Main functionality

The application includes several important features:

### Artist catalog

- users can browse a list of Macedonian artists
- each artist card contains name, genre, decade, region, and image
- the catalog is displayed in a clear, modern card-layout format

### Search and filtering system

- users can search by artist name
- filters are available for genre, decade, and region
- all results update dynamically on the page without full reload
- the interaction is designed to feel smooth and intuitive

### Favorites system

- logged-in users can add artists to a favorites list
- favorites are stored in the database
- the system supports personalized user interaction

### Authentication system

- users can sign up and log in
- the app checks credentials and restricts certain actions to authenticated users
- protected routes are used for personalized features

### Admin functionality

- administrators can manage artists and update the data
- protected admin pages ensure that only authorized users can change content

### Dynamic UI behavior

- the front end uses JavaScript to update the interface without reloading the page
- user actions such as filtering and favorite toggling are handled in real time

### Responsive design

- the layout is adapted for different screen sizes
- CSS styling improves readability, spacing, and visual hierarchy

---

## 5. Technologies used

This project brings together multiple technologies from both front-end and back-end development.

### Front-end

- HTML for structure and content
- CSS for styling and layout
- JavaScript for interactivity and dynamic behavior

### Back-end

- Python as the primary server-side language
- Flask as the web framework

### Database layer

- SQLite for local database storage
- SQLAlchemy for ORM-based database modeling and interaction

### Data and content integration

- JSON files as structured data storage
- scripts for data scraping and data sync
- automatic database seeding from existing dataset files

### External APIs and enrichment

- Spotify API for artist metadata, popularity, and image references
- Gemini API for content validation and enrichment
- this adds a more intelligent data-processing layer to the project

---

## 6. System design and architecture

The app follows a simple but effective web application architecture:

1. The user opens the website in the browser.
2. The Flask app serves the HTML templates and static assets.
3. The front end sends requests to the server for artist data or user actions.
4. The back end queries the SQLite database and returns JSON or rendered templates.
5. The browser renders the response and updates the page dynamically.

This architecture demonstrates the separation between:

- presentation layer (HTML/CSS/JS)
- application logic layer (Flask routes and business logic)
- data layer (SQLite database and JSON source files)

This is a key concept in modern web development and is important to explain during the presentation.

---

## 7. Project structure

The project is organized in a clean file structure that makes it understandable and maintainable.

Main files and folders:

- app.py — main Flask application and route definitions
- models.py — database models for Artist, User, and Favorite
- extensions.py — database initialization and extension setup
- static/ — CSS files, JavaScript, and images
- templates/ — all HTML pages for the website
- artists.json — main catalog of artists
- known-artists.json — manually reviewed seed artists
- scrape-artists.py — collects and organizes artist metadata
- sync-artists.py — syncs and validates data before database insertion
- instance/ — local database and runtime files

This structure is important because it shows how a project can be divided into reusable and organized components.

---

## 8. Data flow in the project

One of the strongest technical aspects of the project is the data flow.

The general process is:

1. data is scraped or imported from available sources
2. artist records are cleaned and normalized
3. metadata such as genre, region, popularity, and description is enriched
4. the data is stored in JSON for review or batch processing
5. the data is synchronized into the SQLite database
6. the app reads and displays that data through the website

This process shows a realistic pipeline for working with data-driven web applications. It also demonstrates how projects can go beyond simple static pages and become data-powered systems.

---

## 9. Data processing and enrichment

The project goes beyond simple static content by using automated processing steps.

### Scraping

The scraper gathers artist information from sources such as MusicBrainz and Spotify. It can collect artist names, genres, images, and popularity indicators.

### Deduplication

The system removes duplicate records by matching unique Spotify IDs and normalized names.

### Validation and quality control

The sync process uses Gemini to classify artists and validate whether they belong to Macedonia. This helps reduce incorrect or irrelevant records.

### Ranking logic

The app uses editorial priority and Spotify popularity as ordering signals. This helps important artists appear more prominently while still considering general public interest.

These features show advanced thinking about data quality and user experience.

---

## 10. Database design

The database is built using SQLAlchemy models with a clear structure.

### Artist model

Stores:

- artist name
- genre
- decade
- region
- image URL
- description
- Spotify ID
- popularity
- editorial priority

### User model

Stores:

- username
- email
- password hash
- user type

### Favorite model

Stores:

- user relationship
- artist relationship
- uniqueness constraints to prevent duplicates

This design is simple but effective, and it shows a proper relational database structure for a web app.

---

## 11. Security and user management

Although this is a student project, it includes important security concepts.

Examples:

- password hashing is used instead of storing raw passwords
- login checks protect certain routes
- admin routes are restricted using authorization logic
- sessions are used to keep track of logged-in users

This is an important technical detail because it shows awareness of web application security practices, even in a small project.

---

## 12. Front-end design and user experience

The website is designed to be visually appealing and easy to use.

### Key UI aspects

- strong hero section for the homepage
- organized artist cards with metadata
- search bar and filter panel
- clear visual hierarchy with headings and categories
- interactive favorite buttons and dynamic updates

### UX considerations

- the interface avoids clutter
- the most important actions are easy to find
- users can quickly browse and narrow down results
- the design is modern and aligned with the project theme

This demonstrates good web design thinking and helps the project feel more professional.

---

## 13. Main challenges faced during development

Several challenges were part of the project:

- collecting and cleaning unreliable or incomplete music data
- handling duplicate artist records from multiple sources
- integrating external APIs without breaking application flow
- syncing database records without losing data integrity
- creating a simple but effective front-end interface
- keeping the code structured and readable
- implementing authentication and favorites correctly

These challenges reflect real-world development problems, and solving them shows technical maturity.

---

## 14. What I learned from the project

This project gave me a practical understanding of the complete web development process.

I learned how to:

- build a web application from scratch
- create routes and connect them to templates
- work with databases and SQLAlchemy models
- manage user sessions and login logic
- design and implement front-end interactions using JavaScript
- process real data and improve it before presenting it in the app
- connect different technologies into one working system

This is one of the most valuable aspects of the project because it connects theory with practice.

---

## 15. Why this project is suitable for presentation

This project is strong for presentation because it combines several important elements:

- web design
- programming
- data processing
- database management
- user authentication
- API integration
- cultural relevance

It is not just a simple website; it is a complete, data-driven application with multiple layers. This makes it suitable for explaining how modern applications work in real life.

---

## 16. Short presentation speech

"This project is called Macedonian Music Discovery. It is a web application designed to help users discover Macedonian artists and music in a more organized and engaging way. The website allows users to search for artists, filter them by genre, decade, and region, and save their favorites. The project combines HTML, CSS, JavaScript, Python, Flask, SQLite, and external APIs in order to create a functional and modern digital platform. I also implemented data processing and validation so the catalog is more complete and reliable. The main idea behind this project is to promote Macedonian culture by using technology to present music in a more accessible and visually appealing format."

---

## 17. Final conclusion

This project shows how web design, software engineering, and digital culture can work together in one application. It demonstrates practical programming skills, data organization, database design, authentication, and interactive UI development.

Overall, Macedonian Music Discovery is more than just a class project. It is a functional web platform that combines technology with culture, creativity, and problem-solving. It is a strong example of what can be built through modern web development and good design thinking.

---

## 18. Closing sentence for the presentation

"In the end, this project shows that technology can be used not only for business or entertainment, but also to preserve, discover, and promote local culture."
