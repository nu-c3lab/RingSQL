CREATE TABLE Movie(
	mID int primary key, 
	title text, 
	year int, 
	director text
);

CREATE TABLE Rating(
	rID int, 
	mID int, 
	stars int, 
	ratingDate date,
	FOREIGN KEY (mID) references Movie(mID),
	FOREIGN KEY (rID) references Reviewer(rID)
);

CREATE TABLE Reviewer(
	rID int primary key, 
	name text);

