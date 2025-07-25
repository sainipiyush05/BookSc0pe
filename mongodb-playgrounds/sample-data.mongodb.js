use('desidoc_library')

// Insert sample books
db.books.insertMany([
    {
        title: "Defense Technology Handbook",
        author: "DRDO Research Team",
        subject: "Defense Systems",
        isbn: "978-1234567890",
        total_pages: 450,
        publication_date: "2024-01-15",
        file_path: "/documents/defense_handbook.pdf",
        upload_date: new Date(),
        status: "active"
    },
    {
        title: "Radar Systems and Applications",
        author: "Dr. A.K. Singh",
        subject: "Electronics",
        isbn: "978-1234567891",
        total_pages: 320,
        publication_date: "2023-12-10",
        file_path: "/documents/radar_systems.pdf",
        upload_date: new Date(),
        status: "active"
    },
    {
        title: "Missile Defense Technologies",
        author: "Dr. B.R. Sharma",
        subject: "Defense Technology",
        isbn: "978-1234567892",
        total_pages: 380,
        publication_date: "2024-02-20",
        file_path: "/documents/missile_defense.pdf",
        upload_date: new Date(),
        status: "active"
    }
])

// Insert sample search index entries
db.search_index.insertMany([
    {
        word: "radar",
        book_id: ObjectId(),
        page_number: 45,
        position: 120,
        frequency: 3
    },
    {
        word: "defense",
        book_id: ObjectId(),
        page_number: 1,
        position: 0,
        frequency: 5
    },
    {
        word: "missile",
        book_id: ObjectId(),
        page_number: 23,
        position: 89,
        frequency: 2
    }
])
