CREATE TABLE userdetails (
    loginid SERIAL PRIMARY KEY,
    firstname VARCHAR NOT NULL,
    lastname VARCHAR NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR NOT NULL,
    createddate TIMESTAMP
);


CREATE TABLE UserCred (
 loginid INTEGER NOT NULL,
 password VARCHAR NOT NULL,
 createddate TIMESTAMP,
 PRIMARY KEY (loginid),
 FOREIGN KEY (loginid) REFERENCES UserDetails (loginid)
);



CREATE TABLE bookdetails (
    bookid SERIAL PRIMARY KEY,
    isbn VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year VARCHAR NOT NULL,
    UNIQUE(isbn)
);


CREATE TABLE bookreviews (
 reviewid SERIAL PRIMARY KEY,
 username varchar NOT NULL,
 isbn VARCHAR NOT NULL,
 rating INTEGER NOT NULL,
 comments VARCHAR NOT NULL,
 createddate TIMESTAMP,
 FOREIGN KEY (username) REFERENCES UserDetails (username),
 FOREIGN KEY (isbn) REFERENCES bookdetails (isbn),
 UNIQUE(username,isbn)
);
