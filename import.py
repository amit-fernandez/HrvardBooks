import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    book = open("books.csv")
    reader = csv.reader(book)
    for isbn, title, author,year in reader:
        db.execute("INSERT INTO bookdetails (isbn, title, author,year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year":year})
        print(f"Book Added {isbn} {title}  {author} {year}")
    db.commit()

if __name__ == "__main__":
    main()
